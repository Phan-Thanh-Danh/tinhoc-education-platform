import asyncio
import logging
from typing import AsyncGenerator

from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.models import Base

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency cung cấp AsyncSession cho các FastAPI routers."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db(max_retries: int = 15, delay_seconds: int = 2) -> None:
    """
    Chờ kết nối tới MySQL và tự động tạo bảng (Code-First) khi chạy môi trường phát triển.
    """
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(
                f"Đang kết nối tới CSDL MySQL (Lần thử {attempt}/{max_retries})..."
            )
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Khởi tạo và đồng bộ cấu trúc 45 bảng CSDL thành công!")

            # Gieo dữ liệu khởi tạo mặc định (Roles, Grades, Topics, Categories)
            from app.core.seed import seed_initial_data
            async with AsyncSessionLocal() as session:
                await seed_initial_data(session)
            return
        except OperationalError as exc:
            logger.warning(
                f"Chưa thể kết nối CSDL ({exc}). Thử lại sau {delay_seconds}s..."
            )
            await asyncio.sleep(delay_seconds)
        except Exception as exc:
            logger.error(f"Lỗi khi khởi tạo CSDL: {exc}")
            raise exc

    raise RuntimeError(
        f"Không thể kết nối CSDL MySQL sau {max_retries} lần thử."
    )

