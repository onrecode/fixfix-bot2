# 🔧 Настройка GitLab CI/CD для FixFix Bot

## 📋 Предварительные требования

1. **GitLab аккаунт** (бесплатный план включает 400 минут CI/CD в месяц)
2. **Доступ к серверу** для развертывания
3. **SSH ключи** для подключения к серверу

## 🚀 Пошаговая настройка

### 1. Создание репозитория в GitLab

1. Войдите в GitLab
2. Нажмите "New Project"
3. Выберите "Create blank project"
4. Заполните поля:
   - **Project name**: `fx-bot`
   - **Visibility Level**: `Private` (рекомендуется)
   - **Initialize repository with**: оставьте пустым

### 2. Настройка переменных окружения

В вашем проекте перейдите в **Settings > CI/CD > Variables** и добавьте:

#### **Обязательные переменные:**
```
DB_PASSWORD          - Пароль для базы данных
TELEGRAM_TOKEN      - Токен Telegram бота
REQUESTS_GROUP_ID   - ID группы для заявок
ADMIN_IDS           - ID администраторов (через запятую)
SECRET_KEY          - Секретный ключ для приложения
```

#### **Переменные для развертывания:**
```
DEPLOY_HOST         - IP или домен сервера
DEPLOY_USER         - Пользователь на сервере (обычно root)
DEPLOY_KEY          - Приватный SSH ключ для подключения к серверу
```

### 3. Настройка SSH ключей

#### **На сервере:**
```bash
# Создаем пользователя для развертывания
sudo adduser deploy
sudo usermod -aG sudo deploy

# Переключаемся на пользователя deploy
su - deploy

# Создаем SSH директорию
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Создаем authorized_keys
touch ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

#### **На вашем компьютере:**
```bash
# Генерируем SSH ключ (если нет)
ssh-keygen -t rsa -b 4096 -C "your-email@example.com"

# Копируем публичный ключ на сервер
ssh-copy-id deploy@YOUR_SERVER_IP

# Проверяем подключение
ssh deploy@YOUR_SERVER_IP
```

### 4. Подготовка сервера

```bash
# Подключаемся к серверу
ssh deploy@YOUR_SERVER_IP

# Устанавливаем Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker deploy

# Устанавливаем Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Создаем директорию для проекта
sudo mkdir -p /opt/fixfix-bot
sudo chown deploy:deploy /opt/fixfix-bot
cd /opt/fixfix-bot

# Выходим из SSH сессии
exit
```

### 5. Настройка собственного GitLab Runner

#### **Важно**: Мы используем собственный GitLab Runner вместо общих исполнителей GitLab для безопасности и контроля.

#### **На сервере развертывания:**

```bash
# Подключаемся к серверу
ssh deploy@YOUR_SERVER_IP

# Устанавливаем GitLab Runner
curl -L "https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh" | sudo bash
sudo apt-get install gitlab-runner

# Регистрируем runner
sudo gitlab-runner register

# При регистрации введите:
# GitLab instance URL: https://gitlab.com (или ваш GitLab)
# Registration token: (получите из Settings > CI/CD > Runners)
# Description: fixfix-bot-runner
# Tags: docker,linux
# Executor: docker
# Default image: alpine:latest
# Docker image: alpine:latest

# Проверяем статус runner'а
sudo gitlab-runner status

# Убеждаемся, что runner активен в GitLab
# Settings > CI/CD > Runners должен показывать активный runner
```

#### **Настройка Docker executor:**

```bash
# Редактируем конфигурацию runner'а
sudo nano /etc/gitlab-runner/config.toml

# Добавляем в секцию [runners.docker]:
# privileged = true
# volumes = ["/var/run/docker.sock:/var/run/docker.sock", "/cache"]

# Перезапускаем runner
sudo gitlab-runner restart
```

### 6. Клонирование проекта

```bash
# Клонируем проект на сервер
ssh deploy@YOUR_SERVER_IP
cd /opt/fixfix-bot
git clone https://gitlab.com/YOUR_USERNAME/fixfix-bot.git .
```

### 7. Настройка переменных в GitLab

В GitLab проекте перейдите в **Settings > CI/CD > Variables**:

#### **DB_PASSWORD**
- **Key**: `DB_PASSWORD`
- **Value**: `your_secure_database_password`
- **Type**: Variable
- **Protected**: ✅
- **Masked**: ✅

#### **TELEGRAM_TOKEN**
- **Key**: `TELEGRAM_TOKEN`
- **Value**: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`
- **Type**: Variable
- **Protected**: ✅
- **Masked**: ✅

#### **DEPLOY_KEY**
- **Key**: `DEPLOY_KEY`
- **Value**: Содержимое вашего приватного SSH ключа
- **Type**: Variable
- **Protected**: ✅
- **Masked**: ❌

#### **DEPLOY_HOST**
- **Key**: `DEPLOY_HOST`
- **Value**: `YOUR_SERVER_IP`
- **Type**: Variable
- **Protected**: ✅
- **Masked**: ❌

### 8. Первый запуск CI/CD

1. **Закоммитьте и запушьте** все файлы в GitLab
2. Перейдите в **CI/CD > Pipelines**
3. Дождитесь завершения этапов `test` и `build`
4. В этапе `deploy` нажмите **Play** для ручного запуска

## 🔍 Мониторинг и отладка

### Просмотр логов CI/CD
- **CI/CD > Pipelines** - общий статус
- **CI/CD > Jobs** - детальные логи каждого этапа
- **CI/CD > Schedules** - планировщик задач

### Отладка проблем
1. **Проверьте переменные** в Settings > CI/CD > Variables
2. **Проверьте SSH подключение** к серверу
3. **Проверьте права доступа** на сервере
4. **Проверьте логи** на сервере

## 📊 Оптимизация CI/CD

### Кэширование
- GitLab автоматически кэширует зависимости Python
- Docker слои кэшируются между сборками

### Параллельное выполнение
- Этапы `test` и `build` могут выполняться параллельно
- Для экономии времени CI/CD

### Условное выполнение
- `deploy` запускается только при успешном `build`
- Ручной запуск для безопасности

## 🚨 Безопасность

### Рекомендации
1. **Используйте Protected branches** для main ветки
2. **Включите Protected variables** для чувствительных данных
3. **Ограничьте доступ** к проекту
4. **Регулярно обновляйте** SSH ключи

### Переменные безопасности
- `DB_PASSWORD` - защищенная и замаскированная
- `TELEGRAM_TOKEN` - защищенная и замаскированная
- `DEPLOY_KEY` - защищенная (но не замаскированная)
- `SECRET_KEY` - защищенная и замаскированная

## 📈 Мониторинг ресурсов

### GitLab CI/CD лимиты
- **Бесплатный план**: 400 минут/месяц
- **Этап test**: ~2-3 минуты
- **Этап build**: ~5-10 минут
- **Этап deploy**: ~2-3 минуты

### Экономия времени
- Используйте кэширование
- Оптимизируйте Dockerfile
- Минимизируйте зависимости

## 🔄 Автоматическое обновление

### Webhook для автоматического развертывания
1. В GitLab: **Settings > Webhooks**
2. URL: `https://YOUR_SERVER/webhook`
3. Triggers: **Push events**
4. SSL verification: ✅

### Cron для регулярных обновлений
В GitLab: **CI/CD > Schedules**
- **Description**: Daily Update
- **Interval Pattern**: `0 2 * * *` (ежедневно в 2:00)
- **Target Branch**: `main`
- **Variables**: пусто

---

**Удачи с настройкой GitLab CI/CD! 🚀**
