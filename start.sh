#!/bin/bash
set -e

# Ожидание базы данных
until pg_isready -h "$HOST" -p 5432 -U "$USER"; do
  echo "Waiting for database..."
  sleep 2
done

cd myshop

python manage.py migrate
python manage.py collectstatic --noinput

exec gunicorn myshop.wsgi:application --bind 0.0.0.0:$PORT