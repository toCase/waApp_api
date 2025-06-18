#!/bin/sh

echo "💡 Ждём базу данных..."
# Ожидание БД (можно настроить по своей ситуации)
until python manage.py migrate --check > /dev/null 2>&1; do
    echo "⏳ База данных ещё не готова, подождём..."
    sleep 1
done

echo "✅ Применяем миграции..."
python manage.py migrate --noinput

echo "📦 Собираем статику..."
python manage.py collectstatic --noinput || true

# Запускаем gunicorn
exec "$@"
