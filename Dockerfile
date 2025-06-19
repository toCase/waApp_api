FROM python:3.11-slim

# Предотвращаем создание .pyc файлов и буферизацию вывода
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    python3-dev \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Создаём и переходим в рабочую директорию
WORKDIR /app

# Копируем и устанавливаем Python зависимости
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Копируем код приложения
COPY . /app/

# Создаём директории для статики и медиа
RUN mkdir -p /app/staticfiles /app/media

# Делаем entrypoint.sh исполняемым
RUN chmod +x /app/entrypoint.sh

# Переходим в директорию Django проекта
WORKDIR /app/apicore

# Открываем порт
EXPOSE 8000

# Запускаем через entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "apicore.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "info"]