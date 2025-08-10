# Многоэтапная сборка для оптимизации размера
FROM python:3.11-slim as builder

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости для сборки
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы зависимостей
COPY requirements.txt .

# Создаем виртуальное окружение и устанавливаем зависимости
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# Финальный образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем только необходимые системные зависимости
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Копируем виртуальное окружение из builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Создаем пользователя для безопасности
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app

# Создаем необходимые директории
RUN mkdir -p /app/logs /app/backups \
    && chown -R app:app /app

# Копируем код приложения
COPY --chown=app:app . .

# Переключаемся на пользователя app
USER app

# Открываем порт
EXPOSE 8000

# Команда запуска (будет переопределена в docker-compose)
CMD ["python", "-m", "app.main"]
