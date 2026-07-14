#!/bin/bash
# /srv/cdGTS/smoke.sh — 배포 계약 `smoke` 동사 (P08.4).
# Usage: /srv/cdGTS/smoke.sh X.Y.Z
#
# /healthz 200 + 버전 일치 + 핵심 행 수>0 를 결정론적으로 검증.
# fsis/fcmanager 와 동형(python3 JSON 파싱, 버전 인자 필수 — 2026-07-14 통일; 종전 grep 기반).
# 가볍게 유지 — 스테이크 낮으니 무거운 모니터링은 만들지 않는다.
#
# ⚠️ prod HTTPS 리다이렉트 함정: SECURE_SSL_REDIRECT=True 면 평문 HTTP 는 301(HTTPS)로 튄다.
# `X-Forwarded-Proto: https`(= SECURE_PROXY_SSL_HEADER) 를 실어 리다이렉트 없이 로컬 검증
# (공인 DNS/인증서 비의존, dev 에선 헤더 무해).
set -euo pipefail

EXPECT_VERSION=${1:-}
if [ -z "$EXPECT_VERSION" ]; then
    echo "Usage: $0 X.Y.Z"
    exit 1
fi

PORT="${SMOKE_PORT:-8011}"
URL="${SMOKE_URL:-http://127.0.0.1:${PORT}/healthz}"

echo "=== smoke: GET $URL (expect $EXPECT_VERSION) ==="

BODY=$(curl -fsS -m 5 -H 'X-Forwarded-Proto: https' "$URL") \
    || { echo "FAIL: /healthz 요청 실패 (연결/타임아웃/HTTP 오류 — 미기동 또는 503=빈 DB 폴백/시드 부재?)"; exit 1; }

echo "  response: $BODY"

# stdlib python3 로 JSON 검증 (호스트에 jq 의존 안 함)
EXPECT_VERSION="$EXPECT_VERSION" python3 - "$BODY" <<'PY'
import json, os, sys
body = sys.argv[1]
expect = os.environ["EXPECT_VERSION"]
try:
    d = json.loads(body)
except Exception as e:
    print(f"FAIL: JSON 파싱 불가 — {e}")
    sys.exit(1)

errs = []
if d.get("status") != "ok":
    errs.append(f"status={d.get('status')!r} (기대 'ok', error={d.get('error')!r})")
if d.get("version") != expect:
    errs.append(f"version={d.get('version')!r} (기대 {expect!r} — 이미지 태그/캐시 확인)")
# 도메인 불변식: 시스템 시드 행 수>0 (빈 이미지 DB 폴백/시드 부재 검출)
counts = d.get("counts") or {}
for key in ("boundaries", "node_types"):
    v = counts.get(key)
    if not isinstance(v, int) or v <= 0:
        errs.append(f"counts.{key}={v!r} (기대 정수>0 — 시스템 시드 부재?)")

if errs:
    print("FAIL:")
    for e in errs:
        print(f"  - {e}")
    sys.exit(1)
print(f"PASS: version={expect}, boundaries={counts.get('boundaries')}, "
      f"node_types={counts.get('node_types')}, graphs={counts.get('graphs')}")
PY

echo "=== smoke OK ==="
