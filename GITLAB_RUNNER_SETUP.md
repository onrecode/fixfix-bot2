# 🏃‍♂️ Настройка собственного GitLab Runner для FixFix Bot

## 🎯 Зачем нужен собственный Runner?

### Преимущества:
- **Безопасность**: Полный контроль над средой выполнения
- **Производительность**: Нет ограничений по времени и ресурсам
- **Надежность**: Не зависим от доступности общих исполнителей GitLab
- **Гибкость**: Можем настроить под свои нужды

### Недостатки:
- **Сложность**: Требует настройки и обслуживания
- **Ресурсы**: Использует ресурсы вашего сервера
- **Ответственность**: Вы отвечаете за работоспособность

## 🚀 Установка GitLab Runner на сервере

### 1. Подготовка сервера

```bash
# Подключаемся к серверу
ssh deploy@YOUR_SERVER_IP

# Обновляем систему
sudo apt update && sudo apt upgrade -y

# Устанавливаем необходимые пакеты
sudo apt install -y curl wget git
```

### 2. Установка GitLab Runner

```bash
# Добавляем официальный репозиторий GitLab Runner
curl -L "https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh" | sudo bash

# Устанавливаем GitLab Runner
sudo apt-get install gitlab-runner

# Проверяем установку
gitlab-runner --version
```

### 3. Регистрация Runner'а

```bash
# Запускаем регистрацию
sudo gitlab-runner register

# Введите следующие данные:
# GitLab instance URL: https://gitlab.com
# Registration token: [получите из GitLab проекта]
# Description: fixfix-bot-runner
# Tags: docker,linux
# Executor: docker
# Default image: alpine:latest
```

#### **Как получить Registration token:**

1. В GitLab проекте перейдите в **Settings > CI/CD > Runners**
2. В разделе "Specific runners" найдите "Registration token"
3. Скопируйте токен и используйте при регистрации

### 4. Настройка Docker executor

```bash
# Редактируем конфигурацию
sudo nano /etc/gitlab-runner/config.toml

# Найдите секцию [runners.docker] и добавьте:
# privileged = true
# volumes = ["/var/run/docker.sock:/var/run/docker.sock", "/cache"]
# network_mode = "host"
```

#### **Пример конфигурации:**

```toml
[[runners]]
  name = "fixfix-bot-runner"
  url = "https://gitlab.com"
  token = "YOUR_TOKEN"
  executor = "docker"
  [runners.docker]
    tls_verify = false
    image = "alpine:latest"
    privileged = true
    disable_entrypoint_overwrite = false
    oom_kill_disable = false
    disable_cache = false
    volumes = ["/var/run/docker.sock:/var/run/docker.sock", "/cache"]
    network_mode = "host"
    shm_size = 0
```

### 5. Перезапуск и проверка

```bash
# Перезапускаем runner
sudo gitlab-runner restart

# Проверяем статус
sudo gitlab-runner status

# Проверяем логи
sudo gitlab-runner --debug run
```

## 🔧 Настройка в GitLab

### 1. Проверка Runner'а

1. В GitLab проекте перейдите в **Settings > CI/CD > Runners**
2. Убедитесь, что ваш runner отображается как "Active"
3. Проверьте теги: `docker`, `linux`

### 2. Настройка переменных

Убедитесь, что все переменные настроены в **Settings > CI/CD > Variables**:

- `DB_PASSWORD`
- `TELEGRAM_TOKEN`
- `REQUESTS_GROUP_ID`
- `ADMIN_IDS`
- `SECRET_KEY`
- `DEPLOY_HOST`
- `DEPLOY_USER`
- `DEPLOY_KEY`

## 🧪 Тестирование Runner'а

### 1. Создание тестового pipeline

Создайте простой тестовый файл `.gitlab-ci-test.yml`:

```yaml
test-runner:
  stage: test
  tags:
    - docker
    - linux
  script:
    - echo "Runner работает корректно!"
    - docker --version
    - python --version || echo "Python не установлен"
```

### 2. Запуск теста

```bash
# В GitLab перейдите в CI/CD > Pipelines
# Создайте новый pipeline с файлом .gitlab-ci-test.yml
# Или временно замените .gitlab-ci.yml на тестовый
```

## 🚨 Устранение проблем

### Проблема: Runner не подключается

```bash
# Проверьте статус
sudo gitlab-runner status

# Проверьте логи
sudo journalctl -u gitlab-runner -f

# Перезапустите сервис
sudo systemctl restart gitlab-runner
```

### Проблема: Docker не работает

```bash
# Проверьте права доступа
sudo usermod -aG docker gitlab-runner

# Проверьте Docker
sudo docker ps

# Перезапустите runner
sudo gitlab-runner restart
```

### Проблема: Pipeline не запускается

1. Проверьте теги в `.gitlab-ci.yml`
2. Убедитесь, что runner активен
3. Проверьте логи runner'а

## 📊 Мониторинг и обслуживание

### 1. Автоматический перезапуск

```bash
# Включаем автозапуск
sudo systemctl enable gitlab-runner

# Проверяем статус
sudo systemctl status gitlab-runner
```

### 2. Обновление Runner'а

```bash
# Останавливаем runner
sudo gitlab-runner stop

# Обновляем
curl -L "https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh" | sudo bash
sudo apt-get install gitlab-runner

# Запускаем
sudo gitlab-runner start
```

### 3. Резервное копирование конфигурации

```bash
# Копируем конфигурацию
sudo cp /etc/gitlab-runner/config.toml /opt/fixfix-bot/backups/

# Восстанавливаем при необходимости
sudo cp /opt/fixfix-bot/backups/config.toml /etc/gitlab-runner/
```

## 🎯 Следующие шаги

После настройки Runner'а:

1. **Запустите тестовый pipeline** для проверки
2. **Настройте все переменные** в GitLab
3. **Запустите основной pipeline** для развертывания
4. **Мониторьте логи** и производительность

## 📚 Полезные команды

```bash
# Управление runner'ом
sudo gitlab-runner start
sudo gitlab-runner stop
sudo gitlab-runner restart
sudo gitlab-runner status

# Просмотр логов
sudo journalctl -u gitlab-runner -f

# Проверка конфигурации
sudo gitlab-runner verify

# Список всех runner'ов
sudo gitlab-runner list
```

---

**Важно**: После настройки Runner'а отключите общие исполнители GitLab в настройках проекта для безопасности.
