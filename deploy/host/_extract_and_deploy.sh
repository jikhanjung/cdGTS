#!/bin/bash
# /srv/cdGTS/_extract_and_deploy.sh — git-free 배포 코어(P08.6). deploy-{prod,dev}.sh 가 호출.
# 이미지에서 host 파일을 추출한 뒤 그 (갓 추출한) deploy.sh 로 위임한다. **운영 서버 repo 불필요.**
#
# 자기 치유(self-heal): 부트스트랩 파일(deploy-prod/dev.sh · 이 스크립트)도 이미지에서 매 배포 갱신한다.
#   - deploy-prod/dev.sh: 이미 exec 로 넘어와 프로세스가 사라졌으니 덮어써도 안전(즉시 반영).
#   - 이 스크립트 자신: 임시파일→원자 rename. 실행 중 bash 는 옛 inode 를 계속 읽고, 새 버전은 **다음 배포부터**.
# → 최초 1회만 이미지에서 부트스트랩(docker cp)하면, 이후 모든 파일이 이미지에서 자기 치유 → git 영영 불필요.
#
# 호출: DEPLOY_SNAPSHOT=0|1 /srv/cdGTS/_extract_and_deploy.sh X.Y.Z [--reseed]
# 상시 존재해야 하는 호스트 파일 = 이 스크립트 + deploy-prod.sh + deploy-dev.sh + .env.
set -euo pipefail

VERSION="${1:-}"
if [ -z "$VERSION" ]; then echo "Usage: DEPLOY_SNAPSHOT=0|1 $0 X.Y.Z [--reseed]"; exit 1; fi

ROOT=/srv/cdGTS
IMAGE="honestjung/cdgts:${VERSION}"

echo "=== [0/6] Pull + extract host files from ${IMAGE} (git-free) ==="
docker pull "$IMAGE"

CID=$(docker create "$IMAGE")
trap 'docker rm -f "$CID" >/dev/null 2>&1 || true' EXIT

# 운영 파일 — 매 배포마다 이미지에서 새로 추출.
for f in docker-compose.yml deploy.sh smoke.sh rollback.sh maintenance.html; do
    if docker cp "${CID}:/app/deploy/host/${f}" "${ROOT}/${f}" 2>/dev/null; then
        echo "  extracted ${f}"
    else
        echo "  (이미지에 ${f} 없음 — 구버전, 건너뜀)"
    fi
done

# 부트스트랩 래퍼 — exec 로 넘어와 안전. 즉시 반영.
for f in deploy-prod.sh deploy-dev.sh; do
    docker cp "${CID}:/app/deploy/host/${f}" "${ROOT}/${f}" 2>/dev/null && echo "  self-heal ${f}" || true
done
# 이 스크립트 자신 — 임시파일 후 원자 rename(옛 inode 로 계속 실행, 새 버전은 다음 배포부터).
if docker cp "${CID}:/app/deploy/host/_extract_and_deploy.sh" "${ROOT}/.ead.new" 2>/dev/null; then
    chmod +x "${ROOT}/.ead.new"; mv -f "${ROOT}/.ead.new" "${ROOT}/_extract_and_deploy.sh"
    echo "  self-heal _extract_and_deploy.sh (다음 배포부터 반영)"
fi

docker rm -f "$CID" >/dev/null; trap - EXIT
chmod +x "${ROOT}/deploy.sh" "${ROOT}/smoke.sh" "${ROOT}/rollback.sh" \
         "${ROOT}/deploy-prod.sh" "${ROOT}/deploy-dev.sh" 2>/dev/null || true

echo ""
exec "${ROOT}/deploy.sh" "$@"        # 버전 + 플래그(--reseed 등) 그대로 전달
