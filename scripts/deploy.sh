#!/bin/bash

# ========================================
# Скрипт развертывания FixFix Bot
# ========================================

set -e  # Остановка при ошибке

echo "🚀 Начинаем развертывание FixFix Bot..."

# Проверяем наличие Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker и попробуйте снова."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Установите Docker Compose и попробуйте снова."
    exit 1
fi

# Проверяем наличие .env файла
if [ ! -f .env.production ]; then
    echo "❌ Файл .env.production не найден. Создайте его на основе env.production"
    exit 1
fi

# Останавливаем существующие контейнеры
echo "🛑 Останавливаем существующие контейнеры..."
docker-compose -f docker-compose.prod.yml down

# Удаляем старые образы
echo "🧹 Удаляем старые образы..."
docker system prune -f

# Создаем необходимые директории
echo "📁 Создаем необходимые директории..."
mkdir -p logs backups nginx/ssl

# Создаем самоподписанный SSL сертификат (для тестирования)
if [ ! -f nginx/ssl/cert.pem ]; then
    echo "🔐 Создаем самоподписанный SSL сертификат..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/key.pem \
        -out nginx/ssl/cert.pem \
        -subj "/C=RU/ST=Moscow/L=Moscow/O=FixFix/CN=localhost"
fi

# Собираем и запускаем сервисы
echo "🔨 Собираем образы..."
docker-compose -f docker-compose.prod.yml build

echo "🚀 Запускаем сервисы..."
docker-compose -f docker-compose.prod.yml up -d

# Ждем запуска сервисов
echo "⏳ Ждем запуска сервисов..."
sleep 10

# Проверяем статус сервисов
echo "📊 Проверяем статус сервисов..."
docker-compose -f docker-compose.prod.yml ps

# Проверяем логи
echo "📋 Проверяем логи приложения..."
docker-compose -f docker-compose.prod.yml logs app --tail=20

echo "✅ Развертывание завершено!"
echo "🌐 API доступен по адресу: http://localhost:8000"
echo "🤖 Telegram Bot запущен"
echo "📊 База данных: PostgreSQL на порту 5432"

# Показываем команды для управления
echo ""
echo "📚 Полезные команды:"
echo "  Просмотр логов: docker-compose -f docker-compose.prod.yml logs -f"
echo "  Остановка: docker-compose -f docker-compose.prod.yml down"
echo "  Перезапуск: docker-compose -f docker-compose.prod.yml restart"
echo "  Обновление: ./scripts/update.sh"
