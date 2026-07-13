#!/bin/bash
# /srv/cdGTS/deploy.sh — cdGTS 버전 스왑 배포 (공통 엔진).
# 직접 부르지 말고 환경별 래퍼로 호출:
#   prod:      /srv/cdGTS/deploy-prod.sh X.Y.Z   (DEPLOY_SNAPSHOT=1 — 배포 전 DB 스냅샷)
#   dev/test:  /srv/cdGTS/deploy-dev.sh  X.Y.Z   (스냅샷 없음, DB = 운영 복사본이라 폐기 가능)
# 직접 호출 시 DEPLOY_SNAPSHOT 미설정 → 스냅샷 없음(dev 동작).
# Usage: DEPLOY_SNAPSHOT=0|1 /srv/cdGTS/deploy.sh X.Y.Z [--reseed]
#   --reseed : migrate 후 smoke 전에 seed --mode=replace + seed_demo (시드 변경 릴리스·빈 DB 최초 배포).
#              replace 는 운영 데이터 보존 upsert(P08.1)라 멱등·안전.
set -euo pipefail

VERSION=${1:-}
if [ -z "$VERSION" ]; then
    echo "Usage: $0 X.Y.Z [--reseed]"
    exit 1
fi

RESEED=0
for a in "$@"; do [ "$a" = "--reseed" ] && RESEED=1; done

ROOT=/srv/cdGTS
cd "$ROOT"

IMAGE="honestjung/cdgts:${VERSION}"
PORT=8011

# 기본: 배포는 DB 를 손대지 않는다(컨테이너만 스왑). DEPLOY_SNAPSHOT=1(prod)이면
# 스왑 직전 pre_deploy 스냅샷을 뜬다. dev/test DB 는 운영 복사본이라 스냅샷 불필요
# (scripts/sync-cdgts-db.sh 가 운영서버 DB 를 pull → 히스토리 보관).

echo "=== [1/6] Pulling ${IMAGE} ==="
docker pull "${IMAGE}"

echo ""
echo "=== [2/6] Updating .env (IMAGE_TAG=${VERSION}) ==="
if grep -q '^IMAGE_TAG=' .env 2>/dev/null; then
    sed -i "s/^IMAGE_TAG=.*/IMAGE_TAG=${VERSION}/" .env
else
    echo "IMAGE_TAG=${VERSION}" >> .env
fi

echo ""
echo "=== [3/6] Swap container (DB 볼륨 유지) ==="
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
# 전 서비스 조정 — 웹(cdgts) + 워커(cdgts-worker) 둘 다 현재 이미지로. up -d cdgts(웹만)이면
# 스냅샷 경로의 down 뒤 워커가 안 켜지고, dev 경로에선 워커가 옛 이미지로 남는다.
docker compose up -d

echo ""
echo "=== [4/6] Wait for backend ==="
for i in $(seq 1 60); do
    # X-Forwarded-Proto: prod(SECURE_SSL_REDIRECT=True)에서 평문 301 대신 실제 200 응답을 받아 기동 확인.
    if curl -fsS -o /dev/null -m 2 -H 'X-Forwarded-Proto: https' "http://127.0.0.1:${PORT}/admin/login/"; then
        echo "  backend up after ${i}s"
        break
    fi
    sleep 1
done

echo ""
echo "=== [5/6] Verify DB binding (bind mount, not ephemeral image DB) ==="
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
echo "=== [5b/6] Reseed (--reseed) ==="
# 시드 변경 릴리스·빈 DB 최초 배포는 smoke 전에 재시드해야 healthz 가 건전(행 수>0)해진다.
# replace 는 운영 데이터 보존 upsert(P08.1)라 멱등·안전. 데모 그래프(시스템)는 seed_demo 로 복원.
if [ "$RESEED" = "1" ]; then
    docker compose exec -T cdgts python manage.py seed --mode=replace
    docker compose exec -T cdgts python manage.py seed_demo
else
    echo "  (--reseed 미지정 — 건너뜀. 시드 변경 릴리스면 --reseed 로 재배포하거나 배포 후 수동 재시드.)"
fi

echo ""
echo "=== [6/6] Smoke (healthz + 버전 일치 + 행 수) ==="
# smoke.sh 는 sync_to_srv.sh 로 함께 동기화됨(없으면 구버전 — 경고만).
if [ -x "$ROOT/smoke.sh" ]; then
    if ! "$ROOT/smoke.sh" "$VERSION"; then
        echo "  ✗ smoke 실패 — 배포된 컨테이너가 불건전. 롤백 검토:"
        echo "      $ROOT/rollback.sh <이전 X.Y.Z>"
        exit 1
    fi
else
    echo "  (smoke.sh 없음 — sync_to_srv.sh 재실행 권장. 건너뜀.)"
fi

echo ""
echo "=== Done: cdgts -> ${VERSION} ==="
docker compose ps cdgts
