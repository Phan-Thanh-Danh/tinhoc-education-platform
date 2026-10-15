# filepath: backend/app/middleware/rate_limit.py
from __future__ import annotations

import ipaddress
import logging
import time
import uuid
from typing import Callable, Optional

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.core.config import settings
from app.services.audit import AuditAction, log_audit_background

logger = logging.getLogger("middleware.rate_limit")

# Quản lý bộ nhớ đệm dự phòng In-Memory (LRU Cache với dung lượng giới hạn)
MAX_MEMORY_CACHE_KEYS: int = 5000
_memory_rate_cache: dict[str, list[float]] = {}
_memory_breached_keys: dict[str, float] = {}  # Lưu mốc thời gian vi phạm lần đầu để chống spam audit log

_redis_client = None
_redis_available: bool = True
_last_redis_retry_time: float = 0.0

# Phân tích danh sách Trusted Proxies từ settings
_trusted_networks = []
for entry in settings.TRUSTED_PROXIES.split(","):
    entry = entry.strip()
    if not entry:
        continue
    if entry.lower() in ("localhost", "::1"):
        _trusted_networks.append(ipaddress.ip_network("127.0.0.1/32"))
        _trusted_networks.append(ipaddress.ip_network("::1/128"))
    else:
        try:
            _trusted_networks.append(ipaddress.ip_network(entry, strict=False))
        except ValueError:
            pass


def is_trusted_proxy(ip_str: str) -> bool:
    """Kiểm tra xem địa chỉ IP kết nối trực tiếp có thuộc mạng Proxy tin cậy hay không."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return any(ip in net for net in _trusted_networks)
    except ValueError:
        return False


def get_client_ip(request: Request) -> str:
    """
    Trích xuất IP thực tế có thẩm định Proxy tin cậy (Anti-IP Spoofing):
    - Chỉ tin tưởng các Header proxy KHI VÀ CHỈ KHI kết nối trực tiếp đến từ Reverse Proxy tin cậy (Nginx, Cloudflare, v.v.).
    - Thứ tự ưu tiên xác thực chặt chẽ:
      1. X-Real-IP: Nginx luôn ghi đè giá trị $remote_addr vào header này, client không thể can thiệp.
      2. CF-Connecting-IP: Chỉ tin tưởng khi cờ USE_CLOUDFLARE = True (tránh client tự bịa header khi chỉ qua Nginx thuần).
      3. X-Forwarded-For: Khi Nginx cấu hình proxy_add_x_forwarded_for, IP thật được nối vào CUỐI chuỗi.
         Duyệt ngược từ cuối danh sách (reversed) để lấy địa chỉ IP công khai đầu tiên không thuộc mạng TRUSTED_PROXIES.
    """
    direct_ip = request.client.host if request.client else "unknown"

    # Nếu không chạy sau Proxy hoặc IP trực tiếp không thuộc danh sách tin cậy -> Trả về direct_ip ngay
    if not settings.BEHIND_PROXY or not is_trusted_proxy(direct_ip):
        return direct_ip

    # 1. Ưu tiên số 1: X-Real-IP (do Nginx ghi đè biến $remote_addr, an toàn tuyệt đối)
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    # 2. CF-Connecting-IP (chỉ khi có cấu hình sử dụng Cloudflare)
    if getattr(settings, "USE_CLOUDFLARE", False):
        cf_ip = request.headers.get("cf-connecting-ip")
        if cf_ip:
            return cf_ip.strip()

    # 3. X-Forwarded-For: Duyệt ngược từ cuối chuỗi để tìm IP thật gần nhất (bỏ qua các IP giả client chèn ở đầu)
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        parts = [p.strip() for p in forwarded.split(",") if p.strip()]
        for ip in reversed(parts):
            if not is_trusted_proxy(ip):
                return ip
        if parts:
            return parts[-1]

    # 4. Fallback cuối: CF-Connecting-IP nếu không có các header trên
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip.strip()

    return direct_ip


def extract_user_id_from_request(request: Request) -> Optional[str]:
    """
    Trích xuất an toàn user_id từ request.state hoặc giải mã nhanh từ Authorization Bearer Token.
    Giải quyết triệt để điểm mù thứ tự thực thi giữa Middleware và Authentication Dependency.
    """
    # 1. Nếu route đã chạy qua Auth Dependency
    if hasattr(request.state, "user_id") and request.state.user_id:
        return str(request.state.user_id)
    if hasattr(request.state, "user") and request.state.user:
        return getattr(request.state.user, "id", None)

    # 2. Giải mã token nhanh từ header nếu có
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        try:
            from jose import jwt
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
                options={"verify_exp": False},
            )
            return payload.get("sub")
        except Exception:
            pass

    return None


async def get_redis_client():
    """Khởi tạo hoặc lấy kết nối Redis Client với cơ chế thử lại có kiểm soát (Backoff)."""
    global _redis_client, _redis_available, _last_redis_retry_time
    now = time.time()

    if not _redis_available:
        if now - _last_redis_retry_time < 60:
            return None
        _last_redis_retry_time = now

    if _redis_client is None:
        try:
            import redis.asyncio as aioredis
            _redis_client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=1.5,
            )
            await _redis_client.ping()
            _redis_available = True
            logger.info("Kết nối cụm Redis cho Rate Limiting thành công!")
        except Exception as exc:
            logger.warning(f"Không thể kết nối Redis ({exc}). Chuyển sang In-Memory fallback.")
            _redis_available = False
            _redis_client = None
    return _redis_client


def _cleanup_memory_cache(now: float, window_seconds: int) -> None:
    """Dọn dẹp bộ nhớ In-Memory khi đạt ngưỡng để chống cạn kiệt RAM (OOM DoS)."""
    if len(_memory_rate_cache) < MAX_MEMORY_CACHE_KEYS and len(_memory_breached_keys) < MAX_MEMORY_CACHE_KEYS:
        return

    # 1. Xóa các key có toàn bộ timestamp đã hết hạn
    expired_keys = [
        k for k, timestamps in _memory_rate_cache.items()
        if not timestamps or (now - timestamps[-1] >= window_seconds)
    ]
    for k in expired_keys:
        _memory_rate_cache.pop(k, None)
        _memory_breached_keys.pop(k, None)

    # 2. Xóa các key vi phạm cũ
    expired_breaches = [
        k for k, t in _memory_breached_keys.items()
        if now - t >= window_seconds
    ]
    for k in expired_breaches:
        _memory_breached_keys.pop(k, None)

    # 3. Nếu vẫn đầy, cưỡng chế xóa bớt 20% key cũ nhất (LRU eviction) trên cả 2 dict
    if len(_memory_rate_cache) >= MAX_MEMORY_CACHE_KEYS:
        keys_to_remove = list(_memory_rate_cache.keys())[: int(MAX_MEMORY_CACHE_KEYS * 0.2)]
        for k in keys_to_remove:
            _memory_rate_cache.pop(k, None)
            _memory_breached_keys.pop(k, None)

    if len(_memory_breached_keys) >= MAX_MEMORY_CACHE_KEYS:
        breach_keys_to_remove = list(_memory_breached_keys.keys())[: int(MAX_MEMORY_CACHE_KEYS * 0.2)]
        for k in breach_keys_to_remove:
            _memory_breached_keys.pop(k, None)


async def check_rate_limit(
    key: str,
    max_requests: int,
    window_seconds: int,
) -> tuple[bool, int, bool]:
    """
    Kiểm tra tần suất gọi bằng thuật toán Sliding Window Counter an toàn:
    - Chống Redis Memory DoS: Không chèn thêm member mới vào ZSET khi đã vượt ngưỡng.
    - Chống In-Memory Memory Leak: Dọn dẹp key định kỳ và giới hạn tối đa 5000 keys.
    - Chống Database DoS: Báo cờ is_first_breach=True ở LẦN ĐẦU TIÊN vi phạm để ghi DB,
      tất cả các lần spam tiếp theo trong cửa sổ sẽ có is_first_breach=False.
    Trả về: (is_allowed: bool, retry_after_seconds: int, is_first_breach: bool)
    """
    now = time.time()
    redis = await get_redis_client()

    if redis is not None:
        try:
            zset_key = f"ratelimit:{key}"
            pipe = redis.pipeline()
            # 1. Xóa các mốc thời gian ngoài cửa sổ
            pipe.zremrangebyscore(zset_key, 0, now - window_seconds)
            # 2. Đếm số lượng request hiện tại
            pipe.zcard(zset_key)
            results = await pipe.execute()
            current_count = results[1]

            if current_count >= max_requests:
                # Đã vượt ngưỡng: KHÔNG chèn thêm vào Redis ZSET để chống tràn RAM!
                oldest_entries = await redis.zrange(zset_key, 0, 0, withscores=True)
                retry_after = (
                    int(window_seconds - (now - oldest_entries[0][1])) + 1
                    if oldest_entries
                    else window_seconds
                )
                # Đánh dấu cờ vi phạm lần đầu bằng key phụ có TTL trong Redis
                breach_flag_key = f"breach_logged:{key}"
                is_first_breach = bool(await redis.set(breach_flag_key, "1", ex=window_seconds, nx=True))
                return False, max(1, retry_after), is_first_breach

            # Chưa vượt ngưỡng: Chèn timestamp mới vào ZSET
            unique_member = f"{now}:{uuid.uuid4().hex[:8]}"
            pipe = redis.pipeline()
            pipe.zadd(zset_key, {unique_member: now})
            pipe.expire(zset_key, window_seconds + 5)
            await pipe.execute()
            return True, 0, False

        except Exception as exc:
            logger.warning(f"Lỗi truy vấn Redis Rate Limit: {exc}. Chuyển sang In-Memory fallback.")

    # In-Memory Sliding Window Fallback (Bảo vệ RAM tối đa)
    _cleanup_memory_cache(now, window_seconds)

    timestamps = _memory_rate_cache.get(key, [])
    # Lọc bỏ các timestamp đã quá hạn cửa sổ
    timestamps = [t for t in timestamps if now - t < window_seconds]
    _memory_rate_cache[key] = timestamps

    if len(timestamps) >= max_requests:
        oldest_time = timestamps[0]
        retry_after = int(window_seconds - (now - oldest_time)) + 1

        # Kiểm tra xem đây có phải là lần chạm ngưỡng đầu tiên không
        is_first_breach = False
        last_breach_time = _memory_breached_keys.get(key)
        if not last_breach_time or (now - last_breach_time >= window_seconds):
            _memory_breached_keys[key] = now
            is_first_breach = True

        return False, max(1, retry_after), is_first_breach

    timestamps.append(now)
    return True, 0, False


def rate_limit(
    max_requests: int = 60,
    window_seconds: int = 60,
    by_user: bool = False,
):
    """
    FastAPI Dependency để giới hạn tần suất gọi API cho từng endpoint cụ thể:
        - Đăng nhập / OTP: max_requests=5, window_seconds=60 (by_user=False)
        - Đăng bài diễn đàn: max_requests=1, window_seconds=60 (by_user=True)
        - Tải tài liệu lên: max_requests=5, window_seconds=60 (by_user=True)
    """

    async def dependency(request: Request):
        client_ip = get_client_ip(request)
        user_id = extract_user_id_from_request(request) if by_user else None

        if by_user and user_id:
            key = f"user:{user_id}:{request.url.path}"
        else:
            key = f"ip:{client_ip}:{request.url.path}"

        allowed, retry_after, is_first_breach = await check_rate_limit(key, max_requests, window_seconds)
        if not allowed:
            logger.warning(
                f"Rate limit exceeded: key={key} vượt quá {max_requests} req / {window_seconds}s"
            )

            # CHỈ GHI NHẬT KÝ KIỂM TOÁN VÀO CSDL Ở LẦN ĐẦU TIÊN (Chống Database/Disk DoS)
            if is_first_breach:
                log_audit_background(
                    action=AuditAction.SECURITY_RATE_LIMIT_EXCEEDED,
                    user_id=user_id,
                    ip_address=client_ip,
                    user_agent=request.headers.get("user-agent"),
                    details={
                        "path": request.url.path,
                        "method": request.method,
                        "max_requests": max_requests,
                        "window_seconds": window_seconds,
                        "retry_after": retry_after,
                    },
                )

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Bạn đang gửi yêu cầu quá nhanh. Vui lòng thử lại sau ít phút để bảo vệ hệ thống.",
                headers={"Retry-After": str(retry_after)},
            )

    return dependency


class GlobalRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware áp dụng giới hạn chung cho toàn bộ API công khai (Mặc định: 120 req / phút / IP).
    Ngăn chặn DDoS và Botnet quét lỗ hổng mà không làm đầy ổ đĩa hoặc treo RAM.
    """

    DEFAULT_MAX_REQUESTS: int = 120
    DEFAULT_WINDOW_SECONDS: int = 60

    EXEMPT_PATHS: set[str] = {
        "/",
        "/health",
        "/api/v1/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/favicon.ico",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in self.EXEMPT_PATHS or request.method == "OPTIONS":
            return await call_next(request)

        client_ip = get_client_ip(request)
        key = f"global_ip:{client_ip}"

        allowed, retry_after, is_first_breach = await check_rate_limit(
            key, self.DEFAULT_MAX_REQUESTS, self.DEFAULT_WINDOW_SECONDS
        )

        if not allowed:
            # CHỈ GHI AUDIT LOG VÀO DATABASE Ở LẦN ĐẦU TIÊN BỊ KHÓA
            if is_first_breach:
                log_audit_background(
                    action=AuditAction.SECURITY_RATE_LIMIT_EXCEEDED,
                    user_id=extract_user_id_from_request(request),
                    ip_address=client_ip,
                    user_agent=request.headers.get("user-agent"),
                    details={
                        "type": "global_rate_limit",
                        "path": request.url.path,
                        "method": request.method,
                        "retry_after": retry_after,
                    },
                )

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "error": "RateLimitExceeded",
                    "message": "Địa chỉ IP của bạn đã gửi quá nhiều yêu cầu trong thời gian ngắn. Vui lòng thử lại sau ít phút.",
                    "retry_after": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)
