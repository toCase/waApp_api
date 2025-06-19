#!/bin/bash
set -e

echo "🔄 Запуск Django приложения..."

# Функция для проверки подключения к БД
check_db() {
    python -c "
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apicore.settings')
django.setup()
from django.db import connection
try:
    connection.ensure_connection()
    print('✅ База данных доступна')
    exit(0)
except Exception as e:
    print(f'❌ База данных недоступна: {e}')
    exit(1)
"
}

# Ожидание доступности БД (максимум 60 секунд)
echo "⏳ Проверяем доступность базы данных..."
retry_count=0
max_retries=60

while ! check_db; do
    retry_count=$((retry_count + 1))
    if [ $retry_count -eq $max_retries ]; then
        echo "❌ Не удалось подключиться к базе данных за 60 секунд"
        exit 1
    fi
    echo "⏳ Ожидание подключения к БД... (попытка $retry_count/$max_retries)"
    sleep 1
done

# Создание миграций (если есть изменения в моделях)
echo "🔍 Проверяем изменения в моделях..."
python manage.py makemigrations --dry-run --verbosity=1 | grep -q "No changes detected" || {
    echo "📝 Обнаружены изменения в моделях, создаём миграции..."
    python manage.py makemigrations --verbosity=2
}

# Проверка наличия неприменённых миграций
echo "🔍 Проверяем неприменённые миграции..."
if python manage.py showmigrations --plan | grep -q "\[ \]"; then
    echo "🔄 Применяем миграции..."
    python manage.py migrate --verbosity=2
    echo "✅ Миграции успешно применены"
else
    echo "✅ Все миграции уже применены"
fi

# Сбор статических файлов
echo "📦 Собираем статические файлы..."
python manage.py collectstatic --noinput --clear || {
    echo "⚠️  Ошибка при сборе статики, продолжаем..."
}

echo "🚀 Запускаем Django сервер..."
exec "$@"