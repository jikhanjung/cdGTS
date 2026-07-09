#!/bin/bash
set -e
umask 002

# 인자가 있으면 그대로 실행 (예: worker 서비스 = `python manage.py run_worker`).
# migrate/collectstatic 은 web 진입점(인자 없음)에서만 — 워커가 DB 마이그레이션을 web 과
# 경합하지 않게 한다(워커는 web 이 스키마를 올린 뒤 폴링만).
if [ "$#" -gt 0 ]; then
  exec "$@"
fi

python manage.py collectstatic --noinput
python manage.py migrate --noinput

exec gunicorn --bind 0.0.0.0:8000 --workers "${GUNICORN_WORKERS:-2}" --access-logfile - config.wsgi:application
