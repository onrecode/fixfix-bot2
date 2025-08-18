"""
Конфигурация приложения FixFix Bot
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class DatabaseSettings(BaseSettings):
    """Настройки базы данных"""
    host: str = Field(default="localhost", env="DB_HOST")
    port: int = Field(default=5432, env="DB_PORT")
    name: str = Field(default="fixfix_bot", env="DB_NAME")
    user: str = Field(default="postgres", env="DB_USER")
    password: str = Field(default="password", env="DB_PASSWORD")
    pool_size: int = Field(default=10, env="DB_POOL_SIZE")
    max_overflow: int = Field(default=20, env="DB_MAX_OVERFLOW")

    @property
    def url(self) -> str:
        """URL для подключения к базе данных"""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class TelegramSettings(BaseSettings):
    """Настройки Telegram бота"""
    token: str = Field(..., env="TELEGRAM_TOKEN")
    requests_group_id: int = Field(default=-1004796553922, env="REQUESTS_GROUP_ID")
    admin_ids: str = Field(default="", env="ADMIN_IDS")
    
    class Config:
        env_file = ".env"
    
    def __init__(self, **kwargs):
        # Отладочная информация
        print(f"DEBUG: TelegramSettings.__init__ called")
        print(f"DEBUG: Environment variables:")
        print(f"  TELEGRAM_TOKEN: {os.getenv('TELEGRAM_TOKEN', 'NOT_SET')}")
        print(f"  REQUESTS_GROUP_ID: {os.getenv('REQUESTS_GROUP_ID', 'NOT_SET')}")
        print(f"  ADMIN_IDS: {os.getenv('ADMIN_IDS', 'NOT_SET')}")
        
        super().__init__(**kwargs)
        # Парсим admin_ids из строки
        if isinstance(self.admin_ids, str) and self.admin_ids:
            self.admin_ids = [int(id.strip()) for id in self.admin_ids.split(",") if id.strip()]
        else:
            self.admin_ids = []


class APISettings(BaseSettings):
    """Настройки API"""
    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8000, env="API_PORT")
    debug: bool = Field(default=False, env="DEBUG")


class MonitoringSettings(BaseSettings):
    """Настройки мониторинга"""
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")


class Settings(BaseSettings):
    """Основные настройки приложения"""
    database: DatabaseSettings = DatabaseSettings()
    telegram: Optional[TelegramSettings] = None
    api: APISettings = APISettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    
    # Лимиты и ограничения
    max_requests_per_user: int = Field(default=5, env="MAX_REQUESTS_PER_USER")
    max_description_length: int = Field(default=1000, env="MAX_DESCRIPTION_LENGTH")
    
    class Config:
        env_file = ".env"
    
    def __init__(self, **kwargs):
        print(f"DEBUG: Settings.__init__ called")
        super().__init__(**kwargs)
        # Инициализируем telegram settings после загрузки переменных окружения
        if self.telegram is None:
            try:
                self.telegram = TelegramSettings()
                print(f"DEBUG: TelegramSettings created successfully")
            except Exception as e:
                print(f"ERROR: Failed to create TelegramSettings: {e}")
                raise


# Глобальный экземпляр настроек
try:
    settings = Settings()
    print(f"DEBUG: Settings created successfully")
except Exception as e:
    print(f"ERROR: Failed to create Settings: {e}")
    raise
