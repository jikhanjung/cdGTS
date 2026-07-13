#!/bin/bash
# deploy/preflight.sh — 배포 전 위험 표면 점검(배포·데이터 계약 P08.4 = preflight 동사).
# 기억 의존 0: git diff 로 위험 표면을 **항상** 표면화 + seed 냄새 lint + DEPLOY.md 델타 출력.
# 뻔한 부분을 결정론적으로 고정하고, go/no-go 판단은 사람/에이전트에 남긴다(빌드 호스트 전용).
#
# Usage: deploy/preflight.sh [<since-ref>]    기본 since = 마지막 "Bump version" 커밋(직전 릴리스 경계).
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

SINCE="${1:-}"
if [ -z "$SINCE" ]; then
    SINCE=$(git log --grep='^Bump version' -n 1 --format='%H' 2>/dev/null || true)
fi

if [ -n "$SINCE" ]; then
    echo "=== preflight: 변경 표면 ${SINCE:0:9}..HEAD (+ working tree) ==="
    CHANGED=$( { git diff --name-only "$SINCE" HEAD; git status --porcelain | awk '{print $2}'; } | sort -u | sed '/^$/d')
else
    echo "=== preflight: working tree (버전 bump 커밋 없음) ==="
    CHANGED=$(git status --porcelain | awk '{print $2}' | sort -u | sed '/^$/d')
fi

hits() { echo "$CHANGED" | grep -qE "$1"; }

echo "--- 위험 표면 ---"
RISK=0
hits '(^|/)migrations/'                 && { echo "  🔴 migrations/ 변경 → migrate 자동 적용(entrypoint). prod 스냅샷 확인."; RISK=1; } || true
hits '(^|/)seed/'                        && { echo "  🔴 seed/ 변경 → 배포 후 'seed --mode=replace' 재시드(add 는 원자 skip). 데모면 seed_demo 도."; RISK=1; } || true
hits '\.env'                            && { echo "  🔴 .env 관련 변경 → 대상 /srv/cdGTS/.env 반영 확인(특히 DATABASE_PATH 바인딩)."; RISK=1; } || true
hits '(docker-compose|Dockerfile|entrypoint)' && { echo "  🟡 컨테이너/compose 변경 → sync_to_srv.sh 로 host/* 갱신."; RISK=1; } || true
hits '(^|/)deploy/host/'                 && { echo "  🟡 host 스크립트 변경 → sync_to_srv.sh 필요."; RISK=1; } || true
[ "$RISK" = "0" ] && echo "  🟢 위험 표면 변경 없음(코드/프론트 전용 추정)."

echo "--- seed 냄새 lint (운영 데이터가 seed 로 새는가) ---"
SMELL=$(git ls-files '*/management/commands/seed_*.py' 2>/dev/null | grep -vE '/seed_demo\.py$' || true)
if [ -n "$SMELL" ]; then
    echo "  🟡 운영 데이터가 seed 로 샐 수 있는 관리 명령:"
    echo "$SMELL" | sed 's/^/     /'
    echo "     → in-app 입력 UI 로 이관 대상인지 확인(계약 §역할이 입구를 정한다)."
else
    echo "  🟢 seed_demo 외 seed_* 관리 명령 없음."
fi

echo "--- DEPLOY.md (권위 운영 델타 노트) ---"
if [ -f DEPLOY.md ]; then
    sed -n '/^## 상시 불변식/,$p' DEPLOY.md | sed 's/^/  /' | head -28
else
    echo "  🟡 DEPLOY.md 없음 — 릴리스별 운영 델타 노트를 두는 게 계약 권고(P08.3)."
fi

echo "=== preflight 끝 — go/no-go 는 사람/에이전트 판단 ==="
