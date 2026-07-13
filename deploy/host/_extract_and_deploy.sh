#!/bin/bash
# /srv/cdGTS/_extract_and_deploy.sh — git-free 배포 코어(P08.6). deploy-{prod,dev}.sh 가 호출.
# 이미지에서 host 운영 파일을 추출한 뒤 그 (갓 추출한) deploy.sh 로 위임한다. 운영 서버 repo 불필요.
#
# 호출: DEPLOY_SNAPSHOT=0|1 /srv/cdGTS/_extract_and_deploy.sh X.Y.Z [--reseed]
# 상시 존재해야 하는 호스트 파일 = 이 스크립트 + deploy-prod.sh + deploy-dev.sh + .env (부트스트랩 1회).
set -euo pipefail

VERSION="${1:-}"
if [ -z "$VERSION" ]; then echo "Usage: DEPLOY_SNAPSHOT=0|1 $0 X.Y.Z [--reseed]"; exit 1; fi

ROOT=/srv/cdGTS
IMAGE="honestjung/cdgts:${VERSION}"

echo "=== [0/6] Pull + extract host files from ${IMAGE} (git-free) ==="
docker pull "$IMAGE"

CID=$(docker create "$IMAGE")
trap 'docker rm -f "$CID" >/dev/null 2>&1 || true' EXIT
# 매 배포마다 이미지에서 새로 나오는 운영 파일(이 래퍼/deploy-*.sh 는 제외 — 실행 중이며 안정 부트스트랩).
for f in docker-compose.yml deploy.sh smoke.sh rollback.sh maintenance.html; do
    if docker cp "${CID}:/app/deploy/host/${f}" "${ROOT}/${f}" 2>/dev/null; then
        echo "  extracted ${f}"
    else
        echo "  (이미지에 ${f} 없음 — 구버전, 건너뜀)"
    fi
done
docker rm -f "$CID" >/dev/null; trap - EXIT
chmod +x "${ROOT}/deploy.sh" "${ROOT}/smoke.sh" "${ROOT}/rollback.sh" 2>/dev/null || true

echo ""
exec "${ROOT}/deploy.sh" "$@"        # 버전 + 플래그(--reseed 등) 그대로 전달
