#!/bin/bash
set -e
umask 002

python manage.py collectstatic --noinput
python manage.py migrate --noinput

exec gunicorn --bind 0.0.0.0:8000 --workers "${GUNICORN_WORKERS:-2}" --access-logfile - config.wsgi:application
