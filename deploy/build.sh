#!/bin/bash
# deploy/build.sh — 테스트 + 버전 bump + Docker 이미지 빌드/푸시. (빌드 호스트 전용)
# Usage: ./deploy/build.sh X.Y.Z
#
# 책임 분리 (fsis2026 관행):
#   - 본 스크립트: 빌드 호스트에서 test + bump + docker build + push
#   - 운영/테스트 호스트(/srv/cdGTS) 동기화는 deploy/sync_to_srv.sh + host/deploy.sh
set -e

VERSION=$1
if [ -z "$VERSION" ]; then
    echo "Usage: $0 X.Y.Z"
    exit 1
fi

VENV="${VENV:-$HOME/venv/cdGTS/bin/activate}"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE=honestjung/cdgts

cd "$PROJECT_DIR"

echo "=== [1/4] Running tests ==="
source "$VENV"
python -m pytest -q
echo "All tests passed."

echo ""
echo "=== [2/4] Bumping version to $VERSION ==="
echo "VERSION = '$VERSION'" > config/version.py
git add config/version.py
if git diff --cached --quiet; then
    echo "(version already at $VERSION, no commit)"
else
    git commit -m "Bump version to $VERSION"
fi

echo ""
echo "=== [3/4] Building image $IMAGE:$VERSION (+ latest) ==="
docker build -f deploy/Dockerfile -t "$IMAGE:$VERSION" -t "$IMAGE:latest" .

echo ""
echo "=== [4/4] Pushing image ==="
docker push "$IMAGE:$VERSION"
docker push "$IMAGE:latest"

echo ""
echo "=== Done: $IMAGE:$VERSION ==="
echo ""
echo "다음 단계 (운영/테스트 호스트에서):"
echo "  cd ~/projects/cdGTS && git pull"
echo "  ./deploy/sync_to_srv.sh          # host/* → /srv/cdGTS"
echo "  /srv/cdGTS/deploy.sh $VERSION    # 컨테이너 교체 + 스냅샷"
