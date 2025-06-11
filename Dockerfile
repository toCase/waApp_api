FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Ставим system deps
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем всё внутрь контейнера
COPY . /app

# Устанавливаем зависимости
RUN pip install --upgrade pip && pip install -r requirements.txt

# Собираем статику (если нужно)
RUN python apicore/manage.py collectstatic --noinput || true

# Открываем порт
EXPOSE 8000

# Запускаем сервер
CMD ["gunicorn", "apicore.apicore.wsgi:application", "--bind", "0.0.0.0:8000"]
