import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "TinHoc Education Platform"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "mysql+aiomysql://root:123456@mysql_db:3306/tinhoc_education_db",
    )

    # Redis Configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")

    # Security & JWT
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", "super_secret_jwt_key_tinhoc_education_platform_2026"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Proxy & Network Security
    BEHIND_PROXY: bool = os.getenv("BEHIND_PROXY", "true").lower() in ("true", "1", "yes")
    USE_CLOUDFLARE: bool = os.getenv("USE_CLOUDFLARE", "false").lower() in ("true", "1", "yes")
    TRUSTED_PROXIES: str = os.getenv("TRUSTED_PROXIES", "127.0.0.1,::1,localhost,172.16.0.0/12,10.0.0.0/8")

    # Audit Log Configuration
    MAX_AUDIT_BODY_SIZE: int = int(os.getenv("MAX_AUDIT_BODY_SIZE", "65536"))  # 64 KB

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

