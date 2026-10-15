# filepath: backend/app/core/security.py
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

# Độ phức tạp băm mật khẩu chuẩn Work Factor >= 12 theo Tài liệu Đặc tả NFR 2.0
BCRYPT_ROUNDS = 12


def hash_password(plain_password: str) -> str:
    """
    Băm mật khẩu bằng thuật toán BCrypt với Work Factor = 12.
    - Tự động mã hóa UTF-8.
    - Cắt tối đa 72 bytes theo giới hạn chuẩn của BCrypt để tránh tấn công DoS payload dài.
    - Sinh muối ngẫu nhiên (Cryptographic Salt) độc lập cho từng mật khẩu.
    """
    if not plain_password:
        raise ValueError("Mật khẩu không được để trống")

    # Giới hạn 72 bytes chuẩn BCrypt
    password_bytes = plain_password.encode("utf-8")[:72]
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    return hashed_bytes.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Kiểm tra mật khẩu người dùng nhập vào với chuỗi băm trong CSDL.
    Sử dụng so sánh hằng số thời gian (Constant-time comparison) chống tấn công Timing Attack.
    """
    if not plain_password or not hashed_password:
        return False

    try:
        password_bytes = plain_password.encode("utf-8")[:72]
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


def hash_otp_code(otp_code: str, pepper: Optional[str] = None) -> str:
    """
    Băm mã xác thực OTP (6 chữ số) bằng HMAC-SHA256 kết hợp Server Pepper
    theo đúng chuẩn Bảng 5 (verification_codes) của Tài liệu Thiết kế CSDL.
    """
    server_pepper = pepper or settings.SECRET_KEY
    return hmac.new(
        key=server_pepper.encode("utf-8"),
        msg=otp_code.strip().encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()


def verify_otp_code(plain_otp: str, hashed_otp: str, pepper: Optional[str] = None) -> bool:
    """
    Đối soát mã OTP người dùng nhập vào với chuỗi băm HMAC-SHA256 trong CSDL.
    """
    calculated_hash = hash_otp_code(plain_otp, pepper)
    return hmac.compare_digest(calculated_hash, hashed_otp)


def generate_numeric_otp(digits: int = 6) -> str:
    """
    Tạo mã số xác thực OTP ngẫu nhiên an toàn tuyệt đối (CSPRNG) với số lượng chữ số định trước.
    """
    min_val = 10 ** (digits - 1)
    max_val = (10 ** digits) - 1
    return str(secrets.randbelow(max_val - min_val + 1) + min_val)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Tạo JSON Web Token (Access Token) có thời hạn sống ngắn (Mặc định: 15-30 phút).
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        # Mặc định 30 phút theo NFR Bảo mật
        expire = now + timedelta(minutes=30)

    to_encode.update({
        "iat": now,
        "exp": expire,
        "type": "access",
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Tạo Refresh Token có thời hạn sống 7 ngày (phục vụ cơ chế RTR chống Replay Attack).
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        # Mặc định 7 ngày theo NFR Bảo mật
        expire = now + timedelta(days=7)

    to_encode.update({
        "iat": now,
        "exp": expire,
        "type": "refresh",
        "jti": secrets.token_hex(16),  # Mã ngẫu nhiên duy nhất của token family
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_jwt_token(token: str) -> Dict[str, Any]:
    """
    Giải mã và xác thực chữ ký của JWT Token.
    Ném lỗi JWTError nếu token giả mạo hoặc hết hạn.
    """
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )
