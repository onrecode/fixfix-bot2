# FixFix Bot - Telegram бот для сервиса по ремонту ПК

Современный Telegram бот с полной интеграцией базы данных, API и мониторингом для сервиса по ремонту ПК.

## 🛠️ Технологический стек

### Backend
- **Python 3.11** - основной язык разработки
- **FastAPI** - современный веб-фреймворк для создания API
- **SQLAlchemy 2.0** - ORM для работы с базой данных
- **Pydantic** - валидация данных и сериализация
- **Uvicorn** - ASGI сервер для запуска FastAPI приложения

### Telegram Bot
- **python-telegram-bot** - официальная библиотека для Telegram Bot API
- **Асинхронная обработка** - использование async/await для эффективной работы
- **Состояния пользователей** - управление процессом создания заявок
- **Интерактивные клавиатуры** - удобный пользовательский интерфейс

### База данных
- **PostgreSQL 15** - надежная реляционная СУБД
- **Alembic** - миграции базы данных
- **Асинхронные подключения** - использование asyncpg для производительности

### Контейнеризация и развертывание
- **Docker** - контейнеризация приложения
- **Docker Compose** - оркестрация сервисов
- **Nginx** - обратный прокси и SSL терминация
- **Multi-stage builds** - оптимизация размера образов

### CI/CD и мониторинг
- **GitLab CI/CD** - автоматизация сборки и развертывания
- **Prometheus** - сбор метрик (опционально для минимальной конфигурации)
- **Grafana** - визуализация метрик (опционально для минимальной конфигурации)

### Безопасность и производительность
- **Переменные окружения** - безопасное хранение конфигурации
- **Валидация входных данных** - защита от некорректных данных
- **Логирование** - структурированные логи для отладки
- **SSL/TLS** - шифрование трафика
- **Ограничения запросов** - защита от злоупотреблений

### Архитектурные паттерны
- **Сервис-ориентированная архитектура** - разделение на логические компоненты
- **Repository pattern** - абстракция доступа к данным
- **Dependency injection** - внедрение зависимостей
- **Middleware** - промежуточная обработка запросов

## 🚀 Возможности

- **Создание заявок** - полный цикл от выбора услуги до подтверждения
- **База данных PostgreSQL** - надежное хранение всех данных
- **REST API** - управление заявками через HTTP endpoints
- **Валидация данных** - проверка корректности заполнения заявок
- **Ограничения** - лимит на количество активных заявок
- **Мониторинг** - Prometheus + Grafana для отслеживания состояния
- **Docker** - полная контейнеризация приложения
- **Логирование** - структурированные логи в JSON формате

## 🏗️ Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram Bot  │    │   FastAPI App   │    │   PostgreSQL    │
│                 │    │                 │    │                 │
│ • Обработка     │    │ • REST API      │    │ • Заявки        │
│   сообщений     │◄──►│ • Валидация     │◄──►│ • Пользователи  │
│ • Клавиатуры    │    │ • Бизнес-логика │    │ • Статусы       │
│ • Состояния     │    │ • Middleware    │    │ • История       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Nginx       │    │   Prometheus    │    │     Redis       │
│                 │    │                 │    │                 │
│ • Проксирование│    │ • Метрики       │    │ • Кэширование   │
│ • SSL/TLS       │    │ • Мониторинг    │    │ • Сессии        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│     Grafana     │    │   Docker Compose│
│                 │    │                 │
│ • Дашборды      │    │ • Управление    │
│ • Визуализация  │    │   контейнерами  │
└─────────────────┘    └─────────────────┘
```

## 📋 Требования

- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM
- 20GB свободного места
- Linux/Windows/macOS

## 🛠️ Установка и запуск

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd fixfix-bot
```

### 2. Настройка переменных окружения

```bash
cp env.example .env
```

Отредактируйте `.env` файл:

```env
# Telegram Bot
TELEGRAM_TOKEN=your_bot_token_here
REQUESTS_GROUP_ID=1004796553922
ADMIN_IDS=123456789,987654321

# Database
DB_HOST=postgres
DB_PORT=5432
DB_NAME=fixfix_bot
DB_USER=postgres
DB_PASSWORD=your_secure_password

# API
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false

# Monitoring
GRAFANA_PASSWORD=admin

# Limits
MAX_REQUESTS_PER_USER=5
```

### 3. Запуск приложения

```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

### 4. Инициализация базы данных

```bash
# Создание таблиц (автоматически при первом запуске)
docker-compose exec app python -c "
from app.database.connection import init_db
import asyncio
asyncio.run(init_db())
"
```

## 🔧 Конфигурация

### Telegram Bot

1. Создайте бота через [@BotFather](https://t.me/botfather)
2. Получите токен и добавьте в `.env`
3. Добавьте бота в группу для заявок
4. Укажите ID группы в `REQUESTS_GROUP_ID`

### База данных

- **PostgreSQL 15** - основная БД
- **Автоматические миграции** при запуске
- **Connection pooling** для оптимизации
- **Backup директория** для резервных копий

### API

- **FastAPI** - современный веб-фреймворк
- **Автоматическая документация** на `/docs`
- **Валидация данных** через Pydantic
- **CORS** настроен для веб-интерфейса

### Мониторинг

- **Prometheus** - сбор метрик
- **Grafana** - визуализация (порт 3000)
- **Метрики приложения** на `/metrics`
- **Health check** на `/health`

## 📱 Использование бота

### Команды

- `/start` - начало работы с ботом
- `/myrequests` - просмотр своих заявок

### Создание заявки

1. Выберите категорию услуги
2. Укажите конкретную проблему
3. Опишите детали (минимум 10 символов)
4. Выберите формат работы
5. Укажите удобное время
6. Предоставьте контактные данные
7. Подтвердите заявку

### Ограничения

- Максимум 5 активных заявок на пользователя
- Валидация всех полей
- Проверка корректности данных

## 🔌 API Endpoints

### Заявки

- `POST /api/v1/requests/` - создание заявки
- `GET /api/v1/requests/{request_id}` - получение заявки
- `GET /api/v1/requests/user/{user_id}` - заявки пользователя
- `PUT /api/v1/requests/{request_id}/status` - обновление статуса
- `POST /api/v1/requests/{request_id}/comments` - добавление комментария

### Система

- `GET /health` - проверка состояния
- `GET /metrics` - метрики Prometheus
- `GET /docs` - документация API

## 📊 Мониторинг

### Prometheus метрики

- HTTP запросы и ответы
- Время выполнения запросов
- Количество заявок
- Состояние базы данных

### Grafana дашборды

- Обзор системы
- Метрики производительности
- Статистика заявок
- Мониторинг БД

## 🐳 Docker

### Сервисы

- **app** - основное FastAPI приложение
- **bot** - Telegram бот
- **postgres** - база данных
- **redis** - кэширование
- **nginx** - веб-сервер
- **prometheus** - мониторинг
- **grafana** - визуализация

### Полезные команды

```bash
# Пересборка образа
docker-compose build --no-cache

# Просмотр логов конкретного сервиса
docker-compose logs -f app

# Выполнение команд в контейнере
docker-compose exec app python -c "print('Hello')"

# Очистка неиспользуемых ресурсов
docker system prune -a
```

## 🔒 Безопасность

- **Переменные окружения** для конфиденциальных данных
- **Валидация входных данных** через Pydantic
- **SQL injection protection** через SQLAlchemy
- **CORS настройки** для веб-интерфейса
- **Логирование** всех действий

## 📝 Логирование

- **Структурированные логи** в JSON формате
- **Уровни логирования** (DEBUG, INFO, WARNING, ERROR)
- **Автоматическая ротация** логов
- **Мониторинг ошибок** через Prometheus

## 🚀 Развертывание в продакшене

### 1. Настройка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Настройка SSL

```bash
# Получение SSL сертификата
sudo apt install certbot
sudo certbot certonly --standalone -d yourdomain.com

# Копирование сертификатов
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./nginx/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./nginx/ssl/
```

### 3. Настройка firewall

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 4. Автозапуск

```bash
# Создание systemd сервиса
sudo nano /etc/systemd/system/fixfix-bot.service

[Unit]
Description=FixFix Bot
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/path/to/fixfix-bot
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target

# Включение автозапуска
sudo systemctl enable fixfix-bot.service
sudo systemctl start fixfix-bot.service
```

## 🧪 Тестирование

### Запуск тестов

```bash
# Установка зависимостей для тестирования
pip install -r requirements.txt

# Запуск тестов
pytest

# Запуск с покрытием
pytest --cov=app
```

### Тестовые данные

```bash
# Создание тестового пользователя
docker-compose exec postgres psql -U postgres -d fixfix_bot -c "
INSERT INTO users (telegram_id, username, first_name, is_admin) 
VALUES (123456789, 'test_user', 'Test User', true);
"
```

## 📈 Масштабирование

### Горизонтальное масштабирование

```yaml
# docker-compose.override.yml
services:
  app:
    deploy:
      replicas: 3
    environment:
      - DB_POOL_SIZE=20
      - DB_MAX_OVERFLOW=40
```

### Load Balancer

```yaml
# nginx/nginx.conf
upstream app_servers {
    server app1:8000;
    server app2:8000;
    server app3:8000;
}
```

## 🔧 Устранение неполадок

### Частые проблемы

1. **Бот не отвечает**
   - Проверьте токен в `.env`
   - Убедитесь, что бот запущен

2. **Ошибки базы данных**
   - Проверьте подключение к PostgreSQL
   - Убедитесь, что БД запущена

3. **Проблемы с Docker**
   - Перезапустите контейнеры: `docker-compose restart`
   - Проверьте логи: `docker-compose logs`

### Полезные команды

```bash
# Проверка состояния сервисов
docker-compose ps

# Просмотр использования ресурсов
docker stats

# Очистка логов
docker-compose logs --tail=100

# Проверка подключения к БД
docker-compose exec postgres pg_isready -U postgres
```

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature branch
3. Внесите изменения
4. Добавьте тесты
5. Создайте Pull Request

## 📄 Лицензия

MIT License - см. файл LICENSE для деталей.

## 📞 Поддержка

- **Issues** - для багов и предложений
- **Discussions** - для вопросов и обсуждений
- **Wiki** - для документации

---

**FixFix Bot** - современное решение для автоматизации сервиса по ремонту ПК! 🚀
