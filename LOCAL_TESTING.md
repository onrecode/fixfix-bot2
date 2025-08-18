# 🧪 Локальное тестирование FixFix Bot

## 🎯 Цель
Протестировать бота локально с готовым Docker образом из GitHub Container Registry перед деплоем на продакшн.

## 📋 Предварительные требования

- Docker установлен
- Telegram бот создан и токен получен
- Переменные окружения настроены

## 🚀 Быстрый старт

### 1. Скачать готовый образ

```bash
# Скачать последний образ
docker pull ghcr.io/onrecode/fixfix-bot2:latest

# Проверить, что образ скачался
docker images | grep fixfix-bot2
```

### 2. Создать .env файл

```bash
# Скопировать пример
cp env.example .env

# Отредактировать .env
nano .env
```

Содержимое `.env`:
```env
# Telegram Bot
TELEGRAM_TOKEN=your_bot_token_here
REQUESTS_GROUP_ID=1004796553922
ADMIN_IDS=123456789

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fixfix_bot
DB_USER=postgres
DB_PASSWORD=password

# API
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=true
```

### 3. Запустить PostgreSQL

```bash
# Запустить PostgreSQL в Docker
docker run -d \
  --name fixfix_postgres \
  -e POSTGRES_DB=fixfix_bot \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  postgres:15-alpine

# Дождаться запуска
docker logs fixfix_postgres
```

### 4. Запустить бота

```bash
# Запустить бота с переменными окружения
docker run -d \
  --name fixfix_bot_test \
  --env-file .env \
  -p 8000:8000 \
  ghcr.io/onrecode/fixfix-bot2:latest

# Проверить логи
docker logs fixfix_bot_test
```

## 🔍 Тестирование

### 1. Проверка API

```bash
# Проверка health endpoint
curl http://localhost:8000/health

# Проверка документации
open http://localhost:8000/docs
```

### 2. Тестирование бота

1. Найдите вашего бота в Telegram
2. Отправьте команду `/start`
3. Протестируйте создание заявки:
   - Выберите категорию
   - Укажите проблему
   - Заполните все поля
   - Подтвердите заявку

### 3. Проверка базы данных

```bash
# Подключиться к БД
docker exec -it fixfix_postgres psql -U postgres -d fixfix_bot

# Проверить таблицы
\dt

# Проверить заявки
SELECT * FROM requests;

# Выйти
\q
```

## 🐛 Отладка

### Просмотр логов

```bash
# Логи бота
docker logs fixfix_bot_test

# Логи PostgreSQL
docker logs fixfix_postgres

# Следить за логами в реальном времени
docker logs -f fixfix_bot_test
```

### Проверка состояния контейнеров

```bash
# Статус контейнеров
docker ps

# Детальная информация
docker inspect fixfix_bot_test
```

### Перезапуск

```bash
# Остановить и удалить контейнеры
docker stop fixfix_bot_test fixfix_postgres
docker rm fixfix_bot_test fixfix_postgres

# Запустить заново
# (см. шаги выше)
```

## 🧹 Очистка

```bash
# Остановить все контейнеры
docker stop fixfix_bot_test fixfix_postgres

# Удалить контейнеры
docker rm fixfix_bot_test fixfix_postgres

# Удалить образ (опционально)
docker rmi ghcr.io/onrecode/fixfix-bot2:latest
```

## ✅ Чек-лист тестирования

- [ ] Образ успешно скачался
- [ ] PostgreSQL запустился
- [ ] Бот запустился без ошибок
- [ ] API доступен на localhost:8000
- [ ] Команда `/start` работает
- [ ] Создание заявки работает полностью
- [ ] Данные сохраняются в БД
- [ ] Логи показывают корректную работу

## 🚨 Возможные проблемы

### Ошибка подключения к БД
- Проверьте, что PostgreSQL запущен
- Убедитесь, что порт 5432 свободен
- Проверьте переменные окружения

### Бот не отвечает
- Проверьте токен в .env
- Убедитесь, что бот не заблокирован
- Проверьте логи на ошибки

### API недоступен
- Проверьте, что порт 8000 свободен
- Убедитесь, что контейнер запущен
- Проверьте логи на ошибки запуска

---

**После успешного тестирования** можно переходить к настройке деплоя на продакшн!
