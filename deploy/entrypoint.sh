#!/bin/bash
set -e
umask 002

HOSTDB=/app/hostdb

# --- 비-root 실행(권한 드롭) ---
# DB 는 $HOSTDB 디렉터리 바인드(WAL/-shm 형제 파일을 호스트와 공유). 컨테이너 프로세스가 그
# 디렉터리·DB 파일 소유 uid 로 돌아야 저널·-wal 생성이 된다. 호스트마다 소유 uid 가 달라서
# (prod=1001·test=1000) Dockerfile 의 USER 로 고정하면 다른 호스트에서 소유권이 어긋난다
# (계약 문서의 "디렉터리 마운트 소유권 함정"). 대신 root 로 시작해 **마운트 소유자를 런타임 감지**,
# 그 uid 로 gosu 드롭한다 — 호스트 무관·chown 불요. 마운트가 root 소유면 그대로 root(폴백).
if [ "$(id -u)" = "0" ] && [ -d "$HOSTDB" ]; then
    UID_T=$(stat -c %u "$HOSTDB"); GID_T=$(stat -c %g "$HOSTDB")
    if [ "$UID_T" != "0" ]; then
        # collectstatic 은 이미지 static 디렉터리(root 소유)에 쓰므로 드롭 전 root 로. web(인자 없음)만.
        [ "$#" -eq 0 ] && python manage.py collectstatic --noinput
        # 과거 root 실행기가 남긴 root 소유 DB 형제 파일이 있으면 드롭 후 못 쓰니 소유 정리(멱등).
        chown "${UID_T}:${GID_T}" "$HOSTDB"/db.sqlite3* 2>/dev/null || true
        echo "entrypoint: drop → uid ${UID_T}:${GID_T} (owner of ${HOSTDB})"
        exec gosu "${UID_T}:${GID_T}" "$0" "$@"
    fi
    echo "entrypoint: ${HOSTDB} is root-owned → staying root"
fi

# --- 드롭 후(비-root) 또는 root 폴백 ---
# 인자가 있으면 그대로 실행 (worker = python manage.py run_worker). migrate/collectstatic 은
# web 진입점(인자 없음)에서만 — 워커가 web 과 마이그레이션 경합하지 않게(web 이 스키마 올린 뒤 폴링).
if [ "$#" -gt 0 ]; then
    exec "$@"
fi

# root 폴백 경로(마운트 root 소유)에서만 collectstatic 미실행 상태 → 여기서 처리. 드롭 경로는 위에서 이미 함.
if [ "$(id -u)" = "0" ]; then
    python manage.py collectstatic --noinput
fi
python manage.py migrate --noinput
exec gunicorn --bind 0.0.0.0:8000 --workers "${GUNICORN_WORKERS:-2}" --access-logfile - config.wsgi:application
