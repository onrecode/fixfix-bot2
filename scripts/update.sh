#!/bin/bash

# ========================================
# Скрипт обновления FixFix Bot
# ========================================

set -e  # Остановка при ошибке

echo "🔄 Начинаем обновление FixFix Bot..."

# Получаем последние изменения из Git
echo "📥 Получаем последние изменения..."
git pull origin main

# Останавливаем приложение (оставляем базу данных)
echo "🛑 Останавливаем приложение..."
docker-compose -f docker-compose.prod.yml stop app

# Удаляем старый образ приложения
echo "🧹 Удаляем старый образ..."
docker-compose -f docker-compose.prod.yml rm -f app
docker rmi fixfix-bot_app:latest || true

# Собираем новый образ
echo "🔨 Собираем новый образ..."
docker-compose -f docker-compose.prod.yml build app

# Запускаем обновленное приложение
echo "🚀 Запускаем обновленное приложение..."
docker-compose -f docker-compose.prod.yml up -d app

# Ждем запуска
echo "⏳ Ждем запуска приложения..."
sleep 10

# Проверяем статус
echo "📊 Проверяем статус..."
docker-compose -f docker-compose.prod.yml ps

# Проверяем логи
echo "📋 Проверяем логи..."
docker-compose -f docker-compose.prod.yml logs app --tail=20

echo "✅ Обновление завершено!"
echo "🤖 Telegram Bot обновлен и работает"
echo "🌐 API доступен по адресу: http://localhost:8000"
