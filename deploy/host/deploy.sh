#!/bin/bash
# /srv/cdGTS/deploy.sh — cdGTS 버전 스왑 배포 (공통 엔진).
# 직접 부르지 말고 환경별 래퍼로 호출:
#   prod:      /srv/cdGTS/deploy-prod.sh X.Y.Z   (DEPLOY_SNAPSHOT=1 — 배포 전 DB 스냅샷)
#   dev/test:  /srv/cdGTS/deploy-dev.sh  X.Y.Z   (스냅샷 없음, DB = 운영 복사본이라 폐기 가능)
# 미설정 시 DEPLOY_SNAPSHOT 기본=1 — 직접 호출도 안전측(fsis/fcmanager 동형, 2026-07-14 통일). dev 는 래퍼가 0 명시.
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

# 기본: 배포는 DB 를 손대지 않는다(컨테이너만 스왑). DEPLOY_SNAPSHOT=1(기본, prod)이면
# 스왑 직전 pre_deploy 스냅샷을 뜬다. dev/test 는 래퍼(deploy-dev.sh)가 0 을 명시 —
# DB 가 운영 복사본이라 스냅샷 불필요(scripts/sync-cdgts-db.sh 가 운영서버 DB 를 pull → 히스토리 보관).

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
DB="$ROOT/db/db.sqlite3"     # 정본 위치 = db/ 서브디렉터리(0.1.64~). compose 가 $ROOT/db 만 /app/hostdb 로 마운트.

# rollback keep 가드용: 배포 전(migrate 실행 전) 적용 migration 수를 컨테이너 정지 전에 조회(정지 후 exec 불가).
PRE_MIG=$(docker compose exec -T cdgts python manage.py showmigrations --plan 2>/dev/null | grep -c '\[X\]' || echo "")

# --- one-way 컷오버(멱등): 옛 루트 DB(/srv/cdGTS/db.sqlite3) → db/ 서브디렉터리 이행(1회). ---
# 종전엔 whole-/srv 를 마운트해 컨테이너가 .env(시크릿)·backup/·배포 스크립트까지 봤다(blast radius).
# db/ 만 마운트로 좁힌다. DB 이동은 WAL 일관 위해 컨테이너 정지 후. symlink 는 컷오버 이전 이미지(옛
# compose = whole-/srv 마운트)로 실수 재배포해도 DB 를 찾게 하는 안전망(상대경로라 두 레이아웃 다 유효).
if [ -f "$ROOT/db.sqlite3" ] && [ ! -L "$ROOT/db.sqlite3" ] && [ ! -e "$DB" ]; then
    echo "  cutover: /srv/cdGTS → /srv/cdGTS/db 마운트 이행(1회, blast radius 축소). 이동 전 컨테이너 정지."
    docker compose down 2>/dev/null || true
    mkdir -p "$ROOT/db"
    mv "$ROOT/db.sqlite3" "$DB"
    [ -f "$ROOT/db.sqlite3-wal" ] && mv "$ROOT/db.sqlite3-wal" "${DB}-wal" || true
    [ -f "$ROOT/db.sqlite3-shm" ] && mv "$ROOT/db.sqlite3-shm" "${DB}-shm" || true
    ln -sf db/db.sqlite3 "$ROOT/db.sqlite3"
    echo "  cutover 완료: 정본 = $DB (+ 안전망 symlink $ROOT/db.sqlite3 → db/db.sqlite3)"
fi

# --- pre-deploy 스냅샷(prod, DEPLOY_SNAPSHOT=1) — 새 위치 $DB 에서 ---
if [ "${DEPLOY_SNAPSHOT:-1}" = "1" ] && [ -f "$DB" ]; then
    echo "  pre-deploy DB snapshot (prod) — writer 정지 후 cp (이 동안 nginx 점검 페이지)"
    docker compose down 2>/dev/null || true
    SNAP_DIR="$ROOT/backup/pre_deploy"
    mkdir -p "$SNAP_DIR"
    TS=$(date -u +%Y%m%d_%H%M%S)
    SNAP="$SNAP_DIR/cdgts_pre_deploy_${VERSION}_${TS}.sqlite3"
    cp -p "$DB" "$SNAP"
    [ -f "${DB}-wal" ] && cp -p "${DB}-wal" "${SNAP}-wal" || true
    [ -f "${DB}-shm" ] && cp -p "${DB}-shm" "${SNAP}-shm" || true
    [ -n "$PRE_MIG" ] && printf '%s\n' "$PRE_MIG" > "${SNAP}.mig" || true
    echo "  snapshot: $SNAP (pre-migration count: ${PRE_MIG:-미상})"
    # retention: 최근 20개만(.mig 사이드카 포함)
    ls -1tr "$SNAP_DIR"/cdgts_pre_deploy_*.sqlite3 2>/dev/null \
        | head -n -20 \
        | while read -r f; do rm -f "$f" "$f-wal" "$f-shm" "$f.mig"; done
fi
# 전 서비스 조정 — 웹(cdgts) + 워커(cdgts-worker) 둘 다 현재 이미지로. up -d cdgts(웹만)이면
# 스냅샷 경로의 down 뒤 워커가 안 켜지고, dev 경로에선 워커가 옛 이미지로 남는다.
docker compose up -d

echo ""
echo "=== [4/6] Wait for backend ==="
# liveness: /healthz 200 대기(fsis/fcmanager 동형, 2026-07-14 통일 — 종전 /admin/login/).
# X-Forwarded-Proto: prod(SECURE_SSL_REDIRECT=True)에서 평문 301 대신 실제 200 응답을 받아 기동 확인.
# 빈 DB 최초 배포는 healthz 가 503(시드 부재)이라 60s 대기 후 진행 — [5b] --reseed 가 채우면 smoke 통과.
for i in $(seq 1 60); do
    if curl -fsS -o /dev/null -m 2 -H 'X-Forwarded-Proto: https' "http://127.0.0.1:${PORT}/healthz"; then
        echo "  backend up after ${i}s"
        break
    fi
    sleep 1
done

echo ""
echo "=== [5/6] Verify DB binding (bind mount, not ephemeral image DB) ==="
# compose 는 host DB 디렉터리($ROOT/db)를 /app/hostdb 로 바인드한다(docker-compose.yml, 0.1.64~ db/ 서브디렉터리).
# .env 의 DATABASE_PATH 가 이 마운트를 벗어나면(예: /app/db.sqlite3) 컨테이너는
# 이미지 내부의 빈 DB 로 폴백 → 사이트가 빈 데이터로 뜬다(실데이터는 $ROOT/db/db.sqlite3 에 안전).
# 이 게이트는 그 오배선을 배포 직후 잡아 실패시킨다(0.1.52 배포 때 실제로 걸렸던 함정).
EXPECT_PREFIX=/app/hostdb/
# 이식-안전(계약 §deploy DB 게이트 함정): 순수 `python -c` 는 DJANGO_SETTINGS_MODULE 없는 컨테이너에서
# ImproperlyConfigured 로 죽어 false-fail 한다(fcmanager 0.6.12 실측). manage.py 가 settings 기본값을
# 세팅하는 `manage.py shell -c` 경유로 통일(fsis/fcmanager 동형, 2026-07-14).
DB_NAME=$(docker compose exec -T cdgts \
    python manage.py shell -c "from django.conf import settings; print(settings.DATABASES['default']['NAME'])" \
    2>/dev/null | tr -d '\r' | tail -n1)
case "$DB_NAME" in
    "${EXPECT_PREFIX}"*)
        echo "  OK: container DB = ${DB_NAME} (host bind mount)"
        ;;
    *)
        echo "  ✗ FATAL: container DB = '${DB_NAME:-<empty>}' — NOT under ${EXPECT_PREFIX}"
        echo "    컨테이너가 마운트되지 않은 이미지 내부 DB 를 쓰고 있다 → 사이트가 빈 데이터로 뜬다."
        echo "    실데이터는 ${ROOT}/db/db.sqlite3 에 안전. 고칠 곳:"
        echo "      ${ROOT}/.env 의 DATABASE_PATH=${EXPECT_PREFIX}db.sqlite3 로 수정 후"
        echo "      (cd ${ROOT} && docker compose up -d --force-recreate cdgts)"
        exit 1
        ;;
esac

# 쓰기 프로브(계약, fcmanager 0.6.17): 읽기 경로 게이트로는 "디렉터리 마운트 소유권 함정"을 못 잡는다
# — 컨테이너 uid 가 마운트 디렉터리 소유자가 아니면 SQLite 저널/-wal 생성이 막혀 **쓰기만** readonly 로
# 죽는데 healthz(읽기)·경로 확인은 통과한다. 앱과 같은 uid(마운트 소유자)로 임시 테이블 CREATE/DROP 하여
# 실제 쓰기 가능성을 배포 직후 검증한다(비-root 실행·소유권 오배치를 여기서 잡음).
echo "  write probe (앱 uid = 마운트 소유자)…"
# 마운트 소스 = $ROOT/db(entrypoint 가 이 소유 uid 로 드롭). 프로브도 같은 uid 로 돌려 실제 서비스 권한 검증.
OWNER_UID=$(stat -c %u "$ROOT/db"); OWNER_GID=$(stat -c %g "$ROOT/db")
if docker compose exec -T -u "${OWNER_UID}:${OWNER_GID}" cdgts \
    python manage.py shell -c "from django.db import connection as x; c=x.cursor(); c.execute('CREATE TABLE IF NOT EXISTS _wprobe_gate (n integer)'); c.execute('DROP TABLE _wprobe_gate'); print('WRITE_OK')" \
    2>/dev/null | grep -q WRITE_OK; then
    echo "  OK: DB 쓰기 프로브 통과 (uid ${OWNER_UID})"
else
    echo "  ✗ FATAL: DB 쓰기 프로브 실패 — 컨테이너가 마운트 디렉터리에 못 쓴다(소유권 오배치?)."
    echo "    ${ROOT} 및 db.sqlite3* 소유 uid 와 컨테이너 실행 uid(entrypoint 드롭 대상)를 확인."
    echo "    보통 ${ROOT} 와 db.sqlite3* 를 같은 uid 로 chown 하면 해소."
    exit 1
fi

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
