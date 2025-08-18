# 🐳 Настройка GitHub Container Registry (актуально 2024)

## Шаг 1: Проверка доступности GitHub Packages

GitHub Packages теперь включен по умолчанию для всех репозиториев. Дополнительная настройка не требуется.

## Шаг 2: Проверка workflow файла

Убедитесь, что в `.github/workflows/ci-cd.yml` есть правильные permissions:

```yaml
build:
  needs: test
  runs-on: ubuntu-latest
  permissions:
    contents: read
    packages: write  # Это важно!
  if: github.ref == 'refs/heads/main'
```

## Шаг 3: Проверка авторизации

В workflow используется встроенный `GITHUB_TOKEN`:

```yaml
- name: Log in to GitHub Container Registry
  uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}  # Автоматически доступен
```

## Шаг 4: Тестирование

1. Сделайте push в main ветку
2. Проверьте вкладку "Actions"
3. Убедитесь, что образ загрузился в Packages

## Шаг 5: Просмотр пакетов

После успешного build:
1. Перейдите в ваш репозиторий
2. Вкладка **"Packages"** (должна появиться автоматически)
3. Там будет ваш Docker образ

## Устранение проблем

### Ошибка "denied: installation not allowed"
- Убедитесь, что в workflow есть `permissions: packages: write`
- Проверьте, что используете `${{ secrets.GITHUB_TOKEN }}`

### Пакеты не видны
- Подождите несколько минут после build
- Проверьте, что build прошел успешно
- Обновите страницу репозитория

### Ошибка авторизации
- `GITHUB_TOKEN` создается автоматически
- Не нужно создавать дополнительные токены

## Полезные команды

```bash
# Локальная проверка образа
docker pull ghcr.io/onrecode/fixfix-bot2:latest

# Запуск образа
docker run -p 8000:8000 ghcr.io/onrecode/fixfix-bot2:latest
```

## Структура образа

После успешного build образ будет доступен как:
`ghcr.io/onrecode/fixfix-bot2:COMMIT_SHA`

Например: `ghcr.io/onrecode/fixfix-bot2:a9ec1c7b72e2714691c69dba82774e312bd0b78a`
