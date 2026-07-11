#!/bin/bash
# /srv/cdGTS/deploy.sh — cdGTS 버전 스왑 배포 (공통 엔진).
# 직접 부르지 말고 환경별 래퍼로 호출:
#   prod:      /srv/cdGTS/deploy-prod.sh X.Y.Z   (DEPLOY_SNAPSHOT=1 — 배포 전 DB 스냅샷)
#   dev/test:  /srv/cdGTS/deploy-dev.sh  X.Y.Z   (스냅샷 없음, DB = 운영 복사본이라 폐기 가능)
# 직접 호출 시 DEPLOY_SNAPSHOT 미설정 → 스냅샷 없음(dev 동작).
# Usage: DEPLOY_SNAPSHOT=0|1 /srv/cdGTS/deploy.sh X.Y.Z
set -euo pipefail

VERSION=${1:-}
if [ -z "$VERSION" ]; then
    echo "Usage: $0 X.Y.Z"
    exit 1
fi

ROOT=/srv/cdGTS
cd "$ROOT"

IMAGE="honestjung/cdgts:${VERSION}"
PORT=8011

# 기본: 배포는 DB 를 손대지 않는다(컨테이너만 스왑). DEPLOY_SNAPSHOT=1(prod)이면
# 스왑 직전 pre_deploy 스냅샷을 뜬다. dev/test DB 는 운영 복사본이라 스냅샷 불필요
# (scripts/sync-cdgts-db.sh 가 운영서버 DB 를 pull → 히스토리 보관).

echo "=== [1/5] Pulling ${IMAGE} ==="
docker pull "${IMAGE}"

echo ""
echo "=== [2/5] Updating .env (IMAGE_TAG=${VERSION}) ==="
if grep -q '^IMAGE_TAG=' .env 2>/dev/null; then
    sed -i "s/^IMAGE_TAG=.*/IMAGE_TAG=${VERSION}/" .env
else
    echo "IMAGE_TAG=${VERSION}" >> .env
fi

echo ""
echo "=== [3/5] Swap container (DB 볼륨 유지) ==="
if [ "${DEPLOY_SNAPSHOT:-0}" = "1" ] && [ -f "$ROOT/db.sqlite3" ]; then
    echo "  pre-deploy DB snapshot (prod) — writer 정지 후 cp (이 동안 nginx 점검 페이지)"
    docker compose down
    SNAP_DIR="$ROOT/backup/pre_deploy"
    mkdir -p "$SNAP_DIR"
    TS=$(date -u +%Y%m%d_%H%M%S)
    SNAP="$SNAP_DIR/cdgts_pre_deploy_${VERSION}_${TS}.sqlite3"
    cp -p "$ROOT/db.sqlite3" "$SNAP"
    [ -f "$ROOT/db.sqlite3-wal" ] && cp -p "$ROOT/db.sqlite3-wal" "${SNAP}-wal" || true
    [ -f "$ROOT/db.sqlite3-shm" ] && cp -p "$ROOT/db.sqlite3-shm" "${SNAP}-shm" || true
    echo "  snapshot: $SNAP"
    # retention: 최근 20개만
    ls -1tr "$SNAP_DIR"/cdgts_pre_deploy_*.sqlite3 2>/dev/null \
        | head -n -20 \
        | while read -r f; do rm -f "$f" "$f-wal" "$f-shm"; done
fi
docker compose up -d cdgts

echo ""
echo "=== [4/5] Wait for backend ==="
for i in $(seq 1 60); do
    if curl -fsS -o /dev/null -m 2 "http://127.0.0.1:${PORT}/admin/login/"; then
        echo "  backend up after ${i}s"
        break
    fi
    sleep 1
done

echo ""
echo "=== [5/5] Verify DB binding (bind mount, not ephemeral image DB) ==="
# compose 는 host DB 디렉터리를 /app/hostdb 로 바인드한다(docker-compose.yml).
# .env 의 DATABASE_PATH 가 이 마운트를 벗어나면(예: /app/db.sqlite3) 컨테이너는
# 이미지 내부의 빈 DB 로 폴백 → 사이트가 빈 데이터로 뜬다(실데이터는 $ROOT/db.sqlite3 에 안전).
# 이 게이트는 그 오배선을 배포 직후 잡아 실패시킨다(0.1.52 배포 때 실제로 걸렸던 함정).
EXPECT_PREFIX=/app/hostdb/
DB_NAME=$(docker compose exec -T -e DJANGO_SETTINGS_MODULE=config.settings cdgts \
    python -c "from django.conf import settings; print(settings.DATABASES['default']['NAME'])" \
    2>/dev/null | tr -d '\r' | tail -n1)
case "$DB_NAME" in
    "${EXPECT_PREFIX}"*)
        echo "  OK: container DB = ${DB_NAME} (host bind mount)"
        ;;
    *)
        echo "  ✗ FATAL: container DB = '${DB_NAME:-<empty>}' — NOT under ${EXPECT_PREFIX}"
        echo "    컨테이너가 마운트되지 않은 이미지 내부 DB 를 쓰고 있다 → 사이트가 빈 데이터로 뜬다."
        echo "    실데이터는 ${ROOT}/db.sqlite3 에 안전. 고칠 곳:"
        echo "      ${ROOT}/.env 의 DATABASE_PATH=${EXPECT_PREFIX}db.sqlite3 로 수정 후"
        echo "      (cd ${ROOT} && docker compose up -d --force-recreate cdgts)"
        exit 1
        ;;
esac

echo ""
echo "=== Done: cdgts -> ${VERSION} ==="
docker compose ps cdgts
