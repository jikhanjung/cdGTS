#!/bin/bash
# /srv/cdGTS/deploy-prod.sh — 프로덕션 배포. 배포 전 DB 스냅샷을 뜬다.
# Usage: /srv/cdGTS/deploy-prod.sh X.Y.Z
set -euo pipefail
DEPLOY_SNAPSHOT=1 exec "$(dirname "$0")/deploy.sh" "$@"
