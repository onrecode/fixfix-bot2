# 📝 Правильные сообщения коммитов

## 🎯 Формат сообщений

```
тип(область): краткое описание

Подробное описание (опционально)
```

## 📋 Типы коммитов

| Тип | Описание | Пример |
|-----|----------|---------|
| `feat` | Новая функция | `feat(bot): добавить обработчик команды /start` |
| `fix` | Исправление бага | `fix(api): исправить ошибку валидации данных` |
| `docs` | Документация | `docs(readme): обновить инструкции по установке` |
| `style` | Форматирование кода | `style(bot): исправить отступы в handlers.py` |
| `refactor` | Рефакторинг | `refactor(database): оптимизировать запросы` |
| `test` | Тесты | `test(api): добавить тесты для endpoints` |
| `chore` | Обновления зависимостей | `chore(deps): обновить requirements.txt` |
| `ci` | CI/CD изменения | `ci(github): настроить GitHub Actions` |
| `build` | Сборка | `build(docker): обновить Dockerfile` |
| `deploy` | Деплой | `deploy(prod): обновить конфигурацию продакшена` |

## 🌍 Области

| Область | Описание |
|---------|----------|
| `bot` | Telegram бот |
| `api` | FastAPI приложение |
| `database` | База данных и модели |
| `docker` | Docker конфигурация |
| `github` | GitHub Actions |
| `nginx` | Nginx конфигурация |
| `monitoring` | Prometheus/Grafana |
| `docs` | Документация |

## ✅ Примеры правильных коммитов

```bash
# Настройка CI/CD
git commit -m "ci(github): настроить GitHub Container Registry workflow"

# Исправление бага
git commit -m "fix(bot): исправить обработку callback_query"

# Новая функция
git commit -m "feat(api): добавить endpoint для статистики заявок"

# Обновление документации
git commit -m "docs(readme): добавить инструкции по деплою"

# Рефакторинг
git commit -m "refactor(database): оптимизировать запросы пользователей"

# Обновление зависимостей
git commit -m "chore(deps): обновить python-telegram-bot до v20.7"
```

## 🚫 Примеры неправильных коммитов

```bash
# ❌ Плохо
git commit -m "fix"

# ❌ Плохо
git commit -m "обновил код"

# ❌ Плохо
git commit -m "WIP"

# ❌ Плохо
git commit -m "fixes"
```

## 🎯 Для текущего проекта

```bash
# Настройка GitHub Container Registry
git commit -m "ci(github): настроить GitHub Container Registry с правильными permissions"

# Исправление workflow
git commit -m "fix(ci): исправить теги Docker образов для ghcr.io"

# Обновление docker-compose
git commit -m "build(docker): обновить docker-compose для использования готовых образов"
```
