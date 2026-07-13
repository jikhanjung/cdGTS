#!/bin/bash
# deploy/sync_to_srv.sh — **repo 있는 머신에서** 최초 부트스트랩용(P08.6). host/* → /srv/cdGTS.
#
# 상시 배포는 git-free 다: /srv/cdGTS/deploy-{prod,dev}.sh X.Y.Z 가 이미지에서 모든 host 파일을 추출하고,
# 0.1.58~ 는 부트스트랩 파일까지 self-heal 하므로 이후 repo 는 영영 불필요.
# repo 가 없는 prod 는 이 스크립트 대신 **이미지에서 직접**(git-free) 부트스트랩할 수 있다 — DEPLOY.md 참조:
#   docker create → docker cp /app/deploy/host/{_extract_and_deploy,deploy-prod,deploy-dev}.sh → chmod +x.
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

echo "=== bootstrap host/* → $HOST_DEST/ ==="
# 상시 부트스트랩 파일(호스트에 남는 것) — git-free 배포의 진입점.
cp -p "$PROJECT_DIR/deploy/host/deploy-prod.sh"        "$HOST_DEST/"
cp -p "$PROJECT_DIR/deploy/host/deploy-dev.sh"         "$HOST_DEST/"
cp -p "$PROJECT_DIR/deploy/host/_extract_and_deploy.sh" "$HOST_DEST/"
# 나머지는 배포 시 이미지에서 추출되지만, 최초 부트스트랩 편의를 위해 함께 심는다.
cp -p "$PROJECT_DIR/deploy/host/docker-compose.yml"   "$HOST_DEST/"
cp -p "$PROJECT_DIR/deploy/host/deploy.sh"            "$HOST_DEST/"
cp -p "$PROJECT_DIR/deploy/host/smoke.sh"             "$HOST_DEST/"
cp -p "$PROJECT_DIR/deploy/host/rollback.sh"          "$HOST_DEST/"
cp -p "$PROJECT_DIR/deploy/host/maintenance.html"     "$HOST_DEST/"
chmod +x "$HOST_DEST"/deploy-prod.sh "$HOST_DEST"/deploy-dev.sh "$HOST_DEST"/_extract_and_deploy.sh \
         "$HOST_DEST"/deploy.sh "$HOST_DEST"/smoke.sh "$HOST_DEST"/rollback.sh
echo "  bootstrap synced (deploy-prod/dev + _extract_and_deploy + compose/deploy/smoke/rollback/maintenance)."
echo ""
echo "=== 상시 배포(git-free): /srv/cdGTS/deploy-{prod,dev}.sh X.Y.Z  (이미지 추출 → 스왑 → smoke) ==="
