#!/bin/sh
set -e

# Ожидание базы данных (убедитесь, что postgresql-client установлен)
until pg_isready -h db -p 5432 -U postgres; do
  echo "Waiting for database..."
  sleep 2
done

python /app/myshop/manage.py migrate
python /app/myshop/manage.py collectstatic --noinput

# Запуск Gunicorn
exec gunicorn myshop.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 4 \
    --timeout 120