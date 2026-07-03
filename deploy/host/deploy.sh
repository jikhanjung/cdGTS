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
PORT=8011

# DB 는 배포에서 손대지 않는다(스냅샷 없음). DB 는 scripts/sync-cdgts-db.sh 가
# 운영서버에서 받아와 관리(개발/테스트 DB = 운영 복사본, 폐기 가능).

echo "=== [1/4] Pulling ${IMAGE} ==="
docker pull "${IMAGE}"

echo ""
echo "=== [2/4] Updating .env (IMAGE_TAG=${VERSION}) ==="
if grep -q '^IMAGE_TAG=' .env 2>/dev/null; then
    sed -i "s/^IMAGE_TAG=.*/IMAGE_TAG=${VERSION}/" .env
else
    echo "IMAGE_TAG=${VERSION}" >> .env
fi

echo ""
echo "=== [3/4] Swap container (DB 볼륨 유지) ==="
docker compose up -d cdgts

echo ""
echo "=== [4/4] Wait for backend ==="
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
