# 🐳 Настройка Docker Hub для CI/CD

## Шаг 1: Создание аккаунта Docker Hub

1. Перейдите на https://hub.docker.com
2. Создайте аккаунт (если нет)
3. Подтвердите email

## Шаг 2: Создание репозитория

1. Нажмите "Create Repository"
2. Имя: `fixfix-bot2`
3. Visibility: Public (бесплатно)
4. Нажмите "Create"

## Шаг 3: Создание Access Token

1. Перейдите в Account Settings → Security
2. Нажмите "New Access Token"
3. Имя: `github-actions`
4. Выберите "Read & Write"
5. Скопируйте токен (сохраните!)

## Шаг 4: Настройка GitHub Secrets

1. Перейдите в ваш GitHub репозиторий
2. Settings → Secrets and variables → Actions
3. Нажмите "New repository secret"
4. Добавьте:

| Имя | Значение |
|-----|----------|
| `DOCKERHUB_USERNAME` | ваш логин Docker Hub |
| `DOCKERHUB_TOKEN` | ваш Access Token |

## Шаг 5: Тестирование

1. Сделайте push в main ветку
2. Проверьте вкладку "Actions"
3. Убедитесь, что образ загрузился в Docker Hub

## Полезные команды

```bash
# Проверка образа локально
docker pull onrecode/fixfix-bot2:latest

# Запуск образа
docker run -p 8000:8000 onrecode/fixfix-bot2:latest
```

## Устранение проблем

### Ошибка авторизации
- Проверьте правильность `DOCKERHUB_USERNAME` и `DOCKERHUB_TOKEN`
- Убедитесь, что токен имеет права "Read & Write"

### Ошибка push
- Проверьте, что репозиторий `fixfix-bot2` существует в Docker Hub
- Убедитесь, что репозиторий публичный или у токена есть права на приватный
