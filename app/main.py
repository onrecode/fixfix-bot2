"""
Основное FastAPI приложение для FixFix Bot
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import time

from app.config import settings
from app.database.connection import init_db, close_db, check_db_connection
from app.api.requests import router as requests_router

# Настройка логирования
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


async def wait_for_database(max_retries: int = 30, delay: float = 2.0):
    """Ожидание готовности базы данных"""
    logger.info("Ожидание готовности базы данных...")
    
    for attempt in range(max_retries):
        try:
            if await check_db_connection():
                logger.info(f"База данных готова (попытка {attempt + 1})")
                return True
        except Exception as e:
            logger.warning(f"Попытка {attempt + 1}/{max_retries}: БД не готова: {e}")
        
        if attempt < max_retries - 1:
            await asyncio.sleep(delay)
    
    logger.error("База данных не готова после всех попыток")
    return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Запуск
    logger.info("Запуск приложения FixFix Bot")
    
    # Ожидание готовности базы данных
    if not await wait_for_database():
        logger.error("Не удалось подключиться к базе данных")
        raise RuntimeError("База данных недоступна")
    
    # Инициализация базы данных
    try:
        await init_db()
        logger.info("База данных инициализирована")
    except Exception as e:
        logger.error(f"Ошибка инициализации БД: {e}")
        raise
    
    yield
    
    # Завершение
    logger.info("Завершение работы приложения")
    await close_db()


# Создание FastAPI приложения
app = FastAPI(
    title="FixFix Bot API",
    description="API для сервиса по ремонту ПК",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware для логирования запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Логируем запрос
    logger.info(
        "HTTP Request",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    response = await call_next(request)
    
    # Логируем ответ
    process_time = time.time() - start_time
    logger.info(
        "HTTP Response",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=process_time
    )
    
    return response


# Обработчик ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled exception",
        method=request.method,
        url=str(request.url),
        error=str(exc),
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутренняя ошибка сервера"}
    )


# Подключение роутеров
app.include_router(requests_router, prefix="/api/v1")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Проверка состояния приложения"""
    db_status = await check_db_connection()
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "timestamp": time.time(),
        "version": "1.0.0"
    }


# Root endpoint
@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "message": "FixFix Bot API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.api.debug,
        log_level="info"
    )
