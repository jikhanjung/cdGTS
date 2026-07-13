#!/bin/bash
# /srv/cdGTS/deploy-prod.sh — 프로덕션 배포(git-free, P08.6). 배포 전 DB 스냅샷을 뜬다.
# Usage: /srv/cdGTS/deploy-prod.sh X.Y.Z
#
# 운영 서버는 앱 소스(git pull)가 필요 없다 — host 운영 파일(compose·deploy.sh·smoke·rollback·
# maintenance)을 **이미지**(/app/deploy/host/*)에서 추출해 쓴다(_extract_and_deploy.sh). 호스트에 상시
# 존재하는 것은 이 래퍼 + deploy-dev.sh + _extract_and_deploy.sh + .env 뿐(부트스트랩 1회).
set -euo pipefail
DEPLOY_SNAPSHOT=1 exec "$(dirname "$0")/_extract_and_deploy.sh" "$@"
