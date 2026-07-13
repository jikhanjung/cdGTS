#!/bin/bash
# /srv/cdGTS/deploy-prod.sh — 프로덕션 배포(git-free, P08.6). 배포 전 DB 스냅샷을 뜬다.
# Usage: /srv/cdGTS/deploy-prod.sh X.Y.Z [--reseed]
#   --reseed : 시드 변경 릴리스·빈 DB 최초 배포 시. smoke 전에 seed --mode=replace + seed_demo(멱등·운영 보존).
#
# 운영 서버는 앱 소스(repo/git)가 필요 없다 — 모든 host 파일을 **이미지**(/app/deploy/host/*)에서 추출한다
# (_extract_and_deploy.sh). 부트스트랩 파일(이 래퍼·deploy-dev.sh·_extract_and_deploy.sh)도 매 배포 자기
# 치유(self-heal)되므로, 최초 1회 이미지에서 심고 나면 repo 는 영영 불필요(prod 에서 삭제 가능).
set -euo pipefail
DEPLOY_SNAPSHOT=1 exec "$(dirname "$0")/_extract_and_deploy.sh" "$@"
