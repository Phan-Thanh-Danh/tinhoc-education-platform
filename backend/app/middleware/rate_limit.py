# filepath: backend/app/middleware/rate_limit.py
from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict
from typing import Callable, Optional

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.core.config import settings
from app.services.audit import AuditAction, log_audit_background

logger = logging.getLogger("middleware.rate_limit")

# Bộ nhớ đệm tạm thời dự phòng (In-Memory Fallback) khi Redis không khả dụng
_memory_rate_cache: dict[str, list[float]] = defaultdict(list)
_redis_client = None
_redis_available: bool = True
_last_redis_retry_time: float = 0.0


def get_client_ip(request: Request) -> str:
    """
    Trích xuất địa chỉ IP thực tế của Client:
    - Ưu tiên đọc từ Reverse Proxy headers (CF-Connecting-IP, X-Forwarded-For, X-Real-IP).
    - Ngăn chặn IP Spoofing và lỗi nhận nhầm IP của Nginx/Docker host.
    """
    # Cloudflare Header
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip.strip()

    # X-Forwarded-For: Client, Proxy1, Proxy2...
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        parts = forwarded.split(",")
        if parts:
            client_ip = parts[0].strip()
            if client_ip:
                return client_ip

    # X-Real-IP Header từ Nginx
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    # Fallback Starlette client host
    return request.client.host if request.client else "unknown"


async def get_redis_client():
    """
    Khởi tạo hoặc lấy kết nối Redis Client bất đồng bộ an toàn.
    Hỗ trợ cơ chế tự động thử kết nối lại sau mỗi 60 giây nếu trước đó từng mất kết nối.
    """
    global _redis_client, _redis_available, _last_redis_retry_time
    now = time.time()

    # Nếu Redis trước đó bị lỗi, chỉ thử kết nối lại sau 60 giây (tránh spam timeout)
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
            logger.warning(
                f"Không thể kết nối cụm Redis ({exc}). "
                "Tự động chuyển sang chế độ dự phòng In-Memory Rate Limiting (Graceful Degradation)."
            )
            _redis_available = False
            _redis_client = None
    return _redis_client


async def check_rate_limit(
    key: str,
    max_requests: int,
    window_seconds: int,
) -> tuple[bool, int]:
    """
    Kiểm tra tần suất gọi bằng thuật toán Sliding Window Counter.
    Trả về: (is_allowed: bool, retry_after_seconds: int)
    """
    now = time.time()
    redis = await get_redis_client()

    if redis is not None:
        try:
            # Thuật toán Sliding Window qua Redis Sorted Set (ZSET)
            zset_key = f"ratelimit:{key}"
            unique_member = f"{now}:{uuid.uuid4().hex[:8]}"

            pipe = redis.pipeline()
            # 1. Xóa các mốc thời gian ngoài cửa sổ trượt
            pipe.zremrangebyscore(zset_key, 0, now - window_seconds)
            # 2. Thêm mốc thời gian hiện tại kèm unique member để chống đè key
            pipe.zadd(zset_key, {unique_member: now})
            # 3. Đếm số lượng request còn lại trong cửa sổ
            pipe.zcard(zset_key)
            # 4. Thiết lập thời gian sống (TTL) cho key
            pipe.expire(zset_key, window_seconds + 5)
            results = await pipe.execute()

            request_count = results[2]
            if request_count > max_requests:
                # Tính thời gian chờ (Retry-After) dựa trên entry cũ nhất
                oldest_entries = await redis.zrange(zset_key, 0, 0, withscores=True)
                retry_after = (
                    int(window_seconds - (now - oldest_entries[0][1])) + 1
                    if oldest_entries
                    else window_seconds
                )
                return False, max(1, retry_after)
            return True, 0
        except Exception as exc:
            logger.warning(f"Lỗi truy vấn Redis Rate Limit: {exc}. Chuyển sang In-Memory fallback.")

    # In-Memory Sliding Window Fallback
    timestamps = _memory_rate_cache[key]
    # Lọc bỏ các request đã quá hạn cửa sổ window_seconds
    timestamps = [t for t in timestamps if now - t < window_seconds]
    _memory_rate_cache[key] = timestamps

    if len(timestamps) >= max_requests:
        oldest_time = timestamps[0]
        retry_after = int(window_seconds - (now - oldest_time)) + 1
        return False, max(1, retry_after)

    _memory_rate_cache[key].append(now)
    return True, 0


def rate_limit(
    max_requests: int = 60,
    window_seconds: int = 60,
    by_user: bool = False,
):
    """
    FastAPI Dependency để giới hạn tần suất gọi API cho từng endpoint cụ thể:
        - Đăng nhập / OTP / Quên MK: max_requests=5, window_seconds=60 (by_user=False)
        - Đăng bài diễn đàn: max_requests=1, window_seconds=60 (by_user=True)
        - Đăng tài liệu / Bóc tách file: max_requests=5, window_seconds=60 (by_user=True)
    Tự động ghi nhận vi phạm vào Bảng 45 (audit_logs).
    """

    async def dependency(request: Request):
        client_ip = get_client_ip(request)
        user_id = getattr(request.state, "user_id", None)

        if by_user and user_id:
            key = f"user:{user_id}:{request.url.path}"
        else:
            key = f"ip:{client_ip}:{request.url.path}"

        allowed, retry_after = await check_rate_limit(key, max_requests, window_seconds)
        if not allowed:
            logger.warning(
                f"Rate limit exceeded: key={key} vượt quá {max_requests} req / {window_seconds}s"
            )
            # Tự động ghi nhật ký kiểm toán vi phạm tần suất vào Bảng 45
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
    Middleware áp dụng giới hạn chung cho toàn bộ API công khai (Mặc định: 120 req / phút / IP)
    để ngăn chặn các đợt quét botnet và tấn công từ chối dịch vụ (DDoS).
    Tự động lưu vết vi phạm vào Bảng 45 (audit_logs).
    """

    DEFAULT_MAX_REQUESTS: int = 120
    DEFAULT_WINDOW_SECONDS: int = 60

    # Các đường dẫn bỏ qua rate limit chung (Docs, Static, Healthcheck)
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

        allowed, retry_after = await check_rate_limit(
            key, self.DEFAULT_MAX_REQUESTS, self.DEFAULT_WINDOW_SECONDS
        )

        if not allowed:
            # Ghi nhật ký kiểm toán vi phạm vào Bảng 45 (audit_logs)
            log_audit_background(
                action=AuditAction.SECURITY_RATE_LIMIT_EXCEEDED,
                user_id=getattr(request.state, "user_id", None),
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
