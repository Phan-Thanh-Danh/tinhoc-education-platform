import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db, init_db
from app.middleware import setup_middlewares

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Đang khởi động ứng dụng FastAPI TinHoc Education Platform...")
    # Tự động kết nối và tạo bảng CSDL khi container khởi động
    await init_db()
    yield
    logger.info("Đang tắt ứng dụng...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Backend API cho Nền tảng Học tập & Khảo thí Tin học GDPT",
    lifespan=lifespan,
)

# Cấu hình CORS để Frontend Vue 3 kết nối thông suốt
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cài đặt các Middleware an ninh, Correlation ID, Rate Limit và Exception Handlers
setup_middlewares(app)


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Chào mừng đến với TinHoc Education Platform API!",
        "version": "1.0.0",
        "status": "online",
        "docs_url": "/docs",
    }


@app.get("/health", tags=["Health"])
@app.get("/api/v1/health", tags=["Health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    db_status = "unhealthy"
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        db_status = f"error: {str(exc)}"

    return {
        "status": "ok" if db_status == "connected" else "degraded",
        "database": db_status,
        "environment": settings.ENVIRONMENT,
    }

