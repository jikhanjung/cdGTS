#!/bin/bash
# /srv/cdGTS/deploy-dev.sh — 개발/테스트 배포(git-free, P08.6). 스냅샷 없음(DB = 운영 복사본, 폐기 가능).
# Usage: /srv/cdGTS/deploy-dev.sh X.Y.Z [--reseed]
#   --reseed : 시드 변경 릴리스·빈 DB 최초 배포 시. smoke 전에 seed --mode=replace + seed_demo.
# host 운영 파일은 이미지에서 추출(_extract_and_deploy.sh) — 운영 서버 repo/git pull 불필요.
set -euo pipefail
DEPLOY_SNAPSHOT=0 exec "$(dirname "$0")/_extract_and_deploy.sh" "$@"
