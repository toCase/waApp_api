FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y python3-dev default-libmysqlclient-dev build-essential pkg-config libpq-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app/

# Создаем директорию для статических файлов
RUN mkdir -p /app/staticfiles

# Переходим в правильную директорию для manage.py
WORKDIR /app/apicore

# Собираем статические файлы
RUN python manage.py collectstatic --noinput || true

# Migrate
RUN python manage.py migrate

EXPOSE 8000

# Исправленная команда для запуска gunicorn
CMD ["gunicorn", "apicore.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "debug"]