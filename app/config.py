"""
Конфигурация приложения FixFix Bot
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from urllib.parse import urlsplit, urlunsplit


class DatabaseSettings(BaseSettings):
    """Настройки базы данных"""
    host: str = Field(default="localhost", env="DB_HOST")
    port: int = Field(default=5432, env="DB_PORT")
    name: str = Field(default="fixfix_bot", env="DB_NAME")
    user: str = Field(default="postgres", env="DB_USER")
    password: str = Field(default="password", env="DB_PASSWORD")
    pool_size: int = Field(default=10, env="DB_POOL_SIZE")
    max_overflow: int = Field(default=20, env="DB_MAX_OVERFLOW")

    def __init__(self, **kwargs):
        # Инициализируем из pydantic-settings (env, env_file)
        super().__init__(**kwargs)
        # Форсируем чтение системных переменных окружения (на случай, если из .env пришли иные значения)
        self.host = os.getenv("DB_HOST", self.host)
        self.port = int(os.getenv("DB_PORT", self.port))
        self.name = os.getenv("DB_NAME", self.name)
        self.user = os.getenv("DB_USER", self.user)
        self.password = os.getenv("DB_PASSWORD", self.password)
        # Безопасное логирование без секретов
        print("DEBUG: DatabaseSettings initialized:")
        print(f"  host: {self.host}")
        print(f"  port: {self.port}")
        print(f"  name: {self.name}")
        print(f"  user: {self.user}")
        print(f"  password: {'*' * len(self.password) if self.password else 'NOT_SET'}")
        print(f"  URL: {self._masked_url}")

    @property
    def url(self) -> str:
        """URL для подключения к базе данных"""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

    @property
    def _masked_url(self) -> str:
        """URL с маскировкой пароля для логов"""
        try:
            parts = urlsplit(self.url)
            # parts.netloc может содержать user:pass@host:port
            if "@" in parts.netloc:
                creds, host = parts.netloc.split("@", 1)
                if ":" in creds:
                    user, _ = creds.split(":", 1)
                    masked_netloc = f"{user}:****@{host}"
                else:
                    masked_netloc = f"{creds}@{host}"
                return urlunsplit((parts.scheme, masked_netloc, parts.path, parts.query, parts.fragment))
        except Exception:
            pass
        return self.url


class TelegramSettings(BaseSettings):
    """Настройки Telegram бота"""
    token: str = Field(..., env="TELEGRAM_TOKEN")
    requests_group_id: int = Field(default=-1004796553922, env="REQUESTS_GROUP_ID")
    admin_ids: str = Field(default="", env="ADMIN_IDS")
    
    class Config:
        env_file = ".env"
    
    def __init__(self, **kwargs):
        # Отладочная информация
        print("DEBUG: TelegramSettings.__init__ called")
        print("DEBUG: Environment variables:")
        token_set = bool(os.getenv("TELEGRAM_TOKEN"))
        admins_set = bool(os.getenv("ADMIN_IDS"))
        print(f"  TELEGRAM_TOKEN_SET: {token_set}")
        print(f"  REQUESTS_GROUP_ID_SET: {os.getenv('REQUESTS_GROUP_ID') is not None}")
        print(f"  ADMIN_IDS_SET: {admins_set}")
        
        # Передаем переменные окружения напрямую
        env_data = {
            "token": os.getenv("TELEGRAM_TOKEN"),
            "requests_group_id": os.getenv("REQUESTS_GROUP_ID", "-1004796553922"),
            "admin_ids": os.getenv("ADMIN_IDS", "")
        }
        
        # Объединяем с переданными kwargs
        env_data.update(kwargs)
        
        super().__init__(**env_data)
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
    # Важно инициализировать вложенные настройки через default_factory,
    # чтобы они читали актуальные переменные окружения при создании Settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    telegram: Optional[TelegramSettings] = None
    api: APISettings = Field(default_factory=APISettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    
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
