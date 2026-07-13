#!/bin/bash
# deploy/sync_to_srv.sh — 운영/테스트 호스트에서 host/* → /srv/cdGTS 동기화.
#
# 사용법 (개발/테스트 서버 + 프로덕션 서버 모두):
#   cd ~/projects/cdGTS && git pull
#   ./deploy/sync_to_srv.sh
#   /srv/cdGTS/deploy.sh X.Y.Z
#
# 최초 1회: /srv/cdGTS 생성 + .env 준비 (deploy/host/.env.example 참조) 후 실행.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
HOST_DEST="${HOST_DEST:-/srv/cdGTS}"

if [ ! -d "$HOST_DEST" ]; then
    echo "ERROR: $HOST_DEST 없음." >&2
    echo "  최초 설정:" >&2
    echo "    sudo mkdir -p $HOST_DEST/backup && sudo chown \$USER $HOST_DEST" >&2
    echo "    cp deploy/host/.env.example $HOST_DEST/.env   # 편집(SECRET_KEY 등)" >&2
    echo "    touch $HOST_DEST/db.sqlite3" >&2
    exit 1
fi

echo "=== host/* → $HOST_DEST/ ==="
cp -p "$PROJECT_DIR/deploy/host/docker-compose.yml" "$HOST_DEST/"
cp -p "$PROJECT_DIR/deploy/host/deploy.sh"          "$HOST_DEST/"
cp -p "$PROJECT_DIR/deploy/host/deploy-prod.sh"     "$HOST_DEST/"
cp -p "$PROJECT_DIR/deploy/host/deploy-dev.sh"      "$HOST_DEST/"
cp -p "$PROJECT_DIR/deploy/host/smoke.sh"           "$HOST_DEST/"
cp -p "$PROJECT_DIR/deploy/host/rollback.sh"        "$HOST_DEST/"
cp -p "$PROJECT_DIR/deploy/host/maintenance.html"   "$HOST_DEST/"
chmod +x "$HOST_DEST/deploy.sh" "$HOST_DEST/deploy-prod.sh" "$HOST_DEST/deploy-dev.sh" \
         "$HOST_DEST/smoke.sh" "$HOST_DEST/rollback.sh"
echo "  docker-compose.yml + deploy{,-prod,-dev}.sh + smoke.sh + rollback.sh + maintenance.html synced."
echo ""
echo "=== 다음: /srv/cdGTS/deploy.sh X.Y.Z  (끝에 smoke 자동) ==="
