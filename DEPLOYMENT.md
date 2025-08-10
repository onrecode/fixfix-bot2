# 🚀 Развертывание FixFix Bot в продакшн

## 📋 Требования

### Системные требования (минимальная нагрузка: 0-20 заявок/день)
- **CPU**: 2 vCPU
- **RAM**: 4 GB
- **Storage**: 20 GB SSD
- **OS**: Ubuntu 22.04 LTS или CentOS 8+
- **Network**: 100 Mbps

### Программное обеспечение
- Docker 20.10+
- Docker Compose 2.0+
- Git
- OpenSSL (для самоподписанных сертификатов)

## 🔧 Подготовка к развертыванию

### 1. Клонирование репозитория
```bash
git clone https://github.com/your-username/fixfix-bot.git
cd fixfix-bot
```

### 2. Настройка переменных окружения
```bash
# Копируем пример конфигурации
cp env.production .env.production

# Редактируем файл
nano .env.production
```

**Обязательные переменные:**
- `TELEGRAM_TOKEN` - токен вашего бота от @BotFather
- `DB_PASSWORD` - надежный пароль для базы данных
- `REQUESTS_GROUP_ID` - ID группы для заявок
- `ADMIN_IDS` - ID администраторов (через запятую)

### 3. Настройка Telegram Bot
1. Создайте бота через @BotFather
2. Получите токен
3. Добавьте бота в группу для заявок
4. Получите ID группы (можно через @userinfobot)

## 🐳 Развертывание через Docker

### Быстрое развертывание
```bash
# Делаем скрипты исполняемыми
chmod +x scripts/*.sh

# Запускаем развертывание
./scripts/deploy.sh
```

### Ручное развертывание
```bash
# Создаем необходимые директории
mkdir -p logs backups nginx/ssl

# Собираем и запускаем
docker-compose -f docker-compose.prod.yml up -d --build
```

## 🔐 Настройка SSL (HTTPS)

### Самоподписанный сертификат (для тестирования)
```bash
# Создаем сертификат
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/key.pem \
    -out nginx/ssl/cert.pem \
    -subj "/C=RU/ST=Moscow/L=Moscow/O=FixFix/CN=your-domain.com"
```

### Let's Encrypt (для продакшн)
```bash
# Устанавливаем certbot
sudo apt install certbot

# Получаем сертификат
sudo certbot certonly --standalone -d your-domain.com

# Копируем сертификаты
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/key.pem
```

## 📊 Мониторинг и управление

### Просмотр статуса
```bash
# Статус всех сервисов
docker-compose -f docker-compose.prod.yml ps

# Логи приложения
docker-compose -f docker-compose.prod.yml logs -f app

# Логи базы данных
docker-compose -f docker-compose.prod.yml logs -f postgres
```

### Обновление приложения
```bash
# Автоматическое обновление
./scripts/update.sh

# Ручное обновление
git pull origin main
docker-compose -f docker-compose.prod.yml up -d --build app
```

### Резервное копирование
```bash
# Создание бэкапа базы данных
docker-compose -f docker-compose.prod.yml exec postgres \
    pg_dump -U fixfix_user fixfix_bot > backup_$(date +%Y%m%d_%H%M%S).sql

# Восстановление из бэкапа
docker-compose -f docker-compose.prod.yml exec -T postgres \
    psql -U fixfix_user fixfix_bot < backup_file.sql
```

## 🚨 Устранение неполадок

### Проблемы с запуском
```bash
# Проверка логов
docker-compose -f docker-compose.prod.yml logs app

# Перезапуск сервиса
docker-compose -f docker-compose.prod.yml restart app

# Полная перезагрузка
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

### Проблемы с базой данных
```bash
# Проверка подключения
docker-compose -f docker-compose.prod.yml exec postgres pg_isready

# Проверка пользователей
docker-compose -f docker-compose.prod.yml exec postgres psql -U fixfix_user -d fixfix_bot -c "\du"
```

### Проблемы с Telegram Bot
1. Проверьте токен в `.env.production`
2. Убедитесь, что бот добавлен в группу
3. Проверьте права бота в группе
4. Посмотрите логи: `docker-compose -f docker-compose.prod.yml logs app`

## 🔒 Безопасность

### Рекомендации
- Измените пароли по умолчанию
- Используйте надежные пароли для базы данных
- Ограничьте доступ к портам (только 80, 443, 8000)
- Регулярно обновляйте Docker образы
- Настройте файрвол на сервере

### Файрвол (Ubuntu)
```bash
# Устанавливаем ufw
sudo apt install ufw

# Настраиваем правила
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 8000

# Включаем файрвол
sudo ufw enable
```

## 📈 Масштабирование

### Для увеличения нагрузки (50+ заявок/день)
- Увеличьте RAM до 8 GB
- Добавьте Redis для кэширования
- Настройте балансировщик нагрузки
- Используйте отдельный сервер для базы данных

### Мониторинг производительности
```bash
# Использование ресурсов
docker stats

# Логи производительности
docker-compose -f docker-compose.prod.yml logs app | grep "performance"
```

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `docker-compose -f docker-compose.prod.yml logs`
2. Проверьте статус сервисов: `docker-compose -f docker-compose.prod.yml ps`
3. Создайте issue в репозитории
4. Обратитесь к документации Docker и FastAPI

---

**Удачи с развертыванием! 🚀**
