#!/bin/bash
# /srv/cdGTS/deploy.sh — cdGTS 버전 스왑 배포 (개발/테스트 + 프로덕션 공통)
# Usage: /srv/cdGTS/deploy.sh X.Y.Z
set -euo pipefail

VERSION=${1:-}
if [ -z "$VERSION" ]; then
    echo "Usage: $0 X.Y.Z"
    exit 1
fi

ROOT=/srv/cdGTS
cd "$ROOT"

IMAGE="honestjung/cdgts:${VERSION}"
PORT=8010

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
echo "=== [3/5] Stop old container + pre-deploy DB snapshot ==="
docker compose down
# compose down 직후 — writer 없어 cp 안전. WAL/SHM 도 함께 보존.
if [ -f "$ROOT/db.sqlite3" ]; then
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

echo ""
echo "=== [4/5] Start new container ==="
docker compose up -d cdgts

echo ""
echo "=== [5/5] Wait for backend ==="
for i in $(seq 1 60); do
    if curl -fsS -o /dev/null -m 2 "http://127.0.0.1:${PORT}/admin/login/"; then
        echo "  backend up after ${i}s"
        break
    fi
    sleep 1
done

echo ""
echo "=== Done: cdgts -> ${VERSION} ==="
docker compose ps cdgts
