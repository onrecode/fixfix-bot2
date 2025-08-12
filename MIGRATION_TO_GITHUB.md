# 🔄 Миграция с GitLab на GitHub Actions

## Зачем мигрировать?

Если у вас проблемы с верификацией аккаунта в GitLab, GitHub Actions может быть отличной альтернативой:

✅ **Преимущества GitHub Actions:**
- Не требует верификации номера телефона
- Проще в настройке для новичков
- Готовые action'ы для всего
- Отличная документация
- Бесплатные минуты для публичных репозиториев

## 📋 Пошаговый план миграции

### 1. Подготовка GitHub репозитория

1. **Создайте репозиторий на GitHub:**
   - Перейдите на [github.com](https://github.com)
   - Нажмите "New repository"
   - Выберите имя и описание
   - Сделайте репозиторий публичным (для бесплатных GitHub Actions)

2. **Скопируйте код:**
   ```bash
   # Добавьте GitHub как remote
   git remote add github https://github.com/YOUR_USERNAME/YOUR_REPO.git
   
   # Отправьте код на GitHub
   git push github main
   ```

### 2. Настройка GitHub Actions

1. **Создайте папку `.github/workflows/`** (уже создана)
2. **Файлы workflow'ов уже готовы:**
   - `ci-cd.yml` - основной CI/CD pipeline
   - `test-runner.yml` - тестирование runner'а

3. **GitHub автоматически обнаружит workflow'ы** и начнет их выполнять

### 3. Настройка секретов

В настройках репозитория (Settings > Secrets and variables > Actions) добавьте:

| Секрет | Описание | Пример |
|--------|----------|---------|
| `PROD_HOST` | IP адрес вашего продакшн сервера | `123.45.67.89` |
| `PROD_USERNAME` | Имя пользователя для SSH | `root` или `ubuntu` |
| `PROD_SSH_KEY` | Приватный SSH ключ для доступа к серверу | Содержимое `~/.ssh/id_rsa` |

### 4. Получение SSH ключа

```bash
# Сгенерируйте SSH ключ (если нет)
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# Скопируйте публичный ключ на сервер
ssh-copy-id username@your_server_ip

# Скопируйте приватный ключ в GitHub Secrets
cat ~/.ssh/id_rsa
```

### 5. Тестирование

1. **Первый тест:** Простой workflow (`test-runner.yml`)
2. **Второй тест:** Основной CI/CD pipeline (`ci-cd.yml`)
3. **Проверка:** Вкладка "Actions" в репозитории

## 🔧 Что изменилось

### Файлы GitLab → GitHub Actions

| GitLab | GitHub Actions | Назначение |
|--------|---------------|------------|
| `.gitlab-ci.yml` | `.github/workflows/ci-cd.yml` | Основной CI/CD pipeline |
| `.gitlab-ci-test.yml` | `.github/workflows/test-runner.yml` | Тестирование |
| GitLab CI/CD Variables | GitHub Secrets | Секреты и переменные |
| GitLab Runner | GitHub-hosted runners | Выполнение задач |

### Структура workflow'а

```yaml
name: CI/CD Pipeline
on: [push, pull_request]  # Триггеры

jobs:
  test:     # Тестирование
  build:    # Сборка Docker образа
  deploy:   # Деплой на сервер
```

## 🚨 Решение проблем

### Workflow не запускается
- Проверьте, что файлы находятся в `.github/workflows/`
- Убедитесь, что ветка называется `main`
- Проверьте вкладку "Actions" в репозитории

### Ошибка SSH подключения
- Проверьте правильность `PROD_HOST` и `PROD_USERNAME`
- Убедитесь, что SSH ключ добавлен в `authorized_keys` на сервере
- Проверьте, что порт 22 открыт на сервере

### Docker образ не собирается
- Убедитесь, что в корне есть `Dockerfile`
- Проверьте, что `docker-compose.yml` корректный
- Проверьте логи в GitHub Actions

## 📊 Мониторинг

- **Вкладка "Actions"** показывает все запущенные workflow'ы
- **Логи каждого шага** доступны для просмотра
- **Уведомления** о успехе/ошибке
- **История выполнения** всех pipeline'ов

## 🎯 Следующие шаги после миграции

1. **Протестируйте** простой workflow
2. **Настройте** основной CI/CD pipeline
3. **Протестируйте** деплой на продакшн
4. **Отключите** GitLab CI/CD (если больше не нужен)
5. **Настройте** мониторинг и уведомления

## 📚 Полезные ссылки

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [SSH Action](https://github.com/appleboy/ssh-action)
- [Docker Build Action](https://github.com/docker/build-push-action)

---

**Примечание:** После успешной миграции вы можете удалить файлы GitLab CI/CD (`.gitlab-ci.yml`, `GITLAB_SETUP.md`, `GITLAB_RUNNER_SETUP.md`) из репозитория.
