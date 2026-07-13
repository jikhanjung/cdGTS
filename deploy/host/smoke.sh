#!/bin/bash
# /srv/cdGTS/smoke.sh — 배포 후 가벼운 검증(배포·데이터 계약 P08.4 = smoke 동사).
# 헬스 200 + status ok + (선택) 버전 일치 + 핵심 행 수>0. 스테이크가 낮으니 무겁게 안 만든다.
# Usage: /srv/cdGTS/smoke.sh [X.Y.Z]     버전 인자를 주면 /healthz 의 version 과 대조.
set -euo pipefail

EXPECT_VERSION="${1:-}"
PORT="${SMOKE_PORT:-8011}"
URL="http://127.0.0.1:${PORT}/healthz"

echo "=== smoke: ${URL} ==="
BODY=$(curl -fsS -m 5 "$URL") || { echo "  ✗ healthz 도달 실패 (컨테이너 미기동?)"; exit 1; }
echo "  ${BODY}"

echo "$BODY" | grep -qE '"status":[[:space:]]*"ok"' \
    || { echo "  ✗ status != ok (빈 DB 폴백/스키마 미완?)"; exit 1; }

if [ -n "$EXPECT_VERSION" ]; then
    echo "$BODY" | grep -qE "\"version\":[[:space:]]*\"${EXPECT_VERSION}\"" \
        || { echo "  ✗ 버전 불일치 — /healthz != 기대 ${EXPECT_VERSION} (이미지 태그/캐시 확인)"; exit 1; }
fi

echo "$BODY" | grep -qE '"boundaries":[[:space:]]*[1-9]' \
    || { echo "  ✗ boundaries 0 — 시스템 시드 부재"; exit 1; }

echo "  OK: healthy${EXPECT_VERSION:+, version ${EXPECT_VERSION}}"
