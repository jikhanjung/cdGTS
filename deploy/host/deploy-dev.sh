#!/bin/bash
# /srv/cdGTS/deploy-dev.sh — 개발/테스트 배포. 스냅샷 없음(DB = 운영 복사본, 폐기 가능).
# Usage: /srv/cdGTS/deploy-dev.sh X.Y.Z
set -euo pipefail
DEPLOY_SNAPSHOT=0 exec "$(dirname "$0")/deploy.sh" "$@"
