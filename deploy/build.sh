#!/bin/bash
# deploy/build.sh — 테스트 + 버전 bump + Docker 이미지 빌드/푸시. (빌드 호스트 전용)
# Usage: ./deploy/build.sh X.Y.Z [--fast]
#   --fast : pytest 건너뜀(프론트 전용 변경 시 ~2분 단축). 백엔드 변경 시엔 --fast 없이.
#
# 책임 분리 (fsis2026 관행):
#   - 본 스크립트: 빌드 호스트에서 test + bump + docker build + push
#   - 운영/테스트 호스트(/srv/cdGTS) 동기화는 deploy/sync_to_srv.sh + host/deploy.sh
set -e

VERSION=""
FAST=0
for arg in "$@"; do
    case "$arg" in
        --fast|--skip-tests) FAST=1 ;;
        *) VERSION="$arg" ;;
    esac
done
if [ -z "$VERSION" ]; then
    echo "Usage: $0 X.Y.Z [--fast]"
    echo "  --fast : skip the pytest suite (frontend-only changes; ~2min faster). Backend changes → run full."
    exit 1
fi

VENV="${VENV:-$HOME/venv/cdGTS/bin/activate}"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE=honestjung/cdgts
export DOCKER_BUILDKIT=1        # layer + inline caching

cd "$PROJECT_DIR"

if [ "$FAST" = "1" ]; then
    echo "=== [1/4] Tests SKIPPED (--fast) — frontend-only 변경 가정. 백엔드 바뀌면 --fast 빼고 재빌드 ==="
else
    echo "=== [1/4] Running tests ==="
    source "$VENV"
    python -m pytest -q
    echo "All tests passed."
fi

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
echo "다음 단계 (운영/테스트 호스트에서 — git-free, P08.6):"
echo "  /srv/cdGTS/deploy-prod.sh $VERSION [--reseed]   # prod: 추출 → 스냅샷 → 스왑 → (--reseed 시 재시드) → smoke"
echo "  /srv/cdGTS/deploy-dev.sh  $VERSION [--reseed]   # dev/test: 스냅샷 없이"
echo "  → 시드/레이아웃 변경 릴리스면 --reseed (preflight 가 seed/ 변경을 플래그). 아니면 생략."
echo "  (부트스트랩 래퍼가 아직 없거나 바뀌었으면 repo 머신에서 1회: ./deploy/sync_to_srv.sh)"
