#!/bin/bash
# /srv/cdGTS/rollback.sh — 롤백 동사(계약). **코드 롤백과 DB 롤백을 분리한다.**
# Usage: /srv/cdGTS/rollback.sh <이전 X.Y.Z> [--db=keep|restore] [--force]
#   --db=keep    (기본) 이전 이미지 태그로만 전환. 현재 DB 유지(운영 데이터 보존) — 삭제 아니라 전환.
#   --db=restore 서비스 정지 → 이전 이미지 전환 → pre_deploy 스냅샷 복원. 그 배포 창의 운영 쓰기는 유실.
#   --force      keep 가드(직전 배포에 migration 있으면 keep 차단)를 무시하고 강행.
#
# 기본이 keep 인 이유: rollback 이 배포 후 운영자 입력분까지 스냅샷 복원으로 지우면 rollback 자신이
# 불변식("파이프라인은 운영 데이터를 나르지도 지우지도 않는다")을 깬다. DB 복원은 명시적 opt-in.
# 기본값은 deploy.toml `rollback_db="keep"` 선언과 일치.
#
# keep 가드: 직전 배포가 migration 을 적용했으면 이전 코드가 새 스키마와 비호환일 수 있어 keep 을 막고
# restore/수동 판단으로 승격한다. 판정 = 최신 pre_deploy 스냅샷의 `.mig` 사이드카(배포 전 적용 migration
# 수, deploy.sh 가 기록) vs 현재 컨테이너의 적용 수 비교. 사이드카가 없으면(구 스냅샷) 미상으로 두고 진행.
set -euo pipefail

ROOT=/srv/cdGTS
cd "$ROOT"

PREV=""
DB_MODE=keep            # deploy.toml rollback_db 기본값과 일치
FORCE=0
for a in "$@"; do
    case "$a" in
        --db=keep)    DB_MODE=keep ;;
        --db=restore) DB_MODE=restore ;;
        --force)      FORCE=1 ;;
        --*)          echo "unknown flag: $a" >&2; exit 1 ;;
        *)            PREV="$a" ;;
    esac
done
if [ -z "$PREV" ]; then
    echo "Usage: $0 <이전 X.Y.Z> [--db=keep|restore] [--force]" >&2; exit 1
fi

echo "=== rollback → ${PREV} (db=${DB_MODE}) ==="

# 최신 pre_deploy 스냅샷 = 직전 배포 1단계 되돌리기용(다단계는 스냅샷 명시).
SNAP=$(ls -1t "$ROOT"/backup/pre_deploy/cdgts_pre_deploy_*.sqlite3 2>/dev/null | head -n1 || true)

# --- keep 가드 ---
if [ "$DB_MODE" = keep ]; then
    CUR_MIG=$(docker compose exec -T cdgts python manage.py showmigrations --plan 2>/dev/null | grep -c '\[X\]' || echo "")
    PRE_MIG=""
    [ -n "$SNAP" ] && [ -f "${SNAP}.mig" ] && PRE_MIG=$(cat "${SNAP}.mig" 2>/dev/null || echo "")
    if [ -n "$CUR_MIG" ] && [ -n "$PRE_MIG" ] && [ "$CUR_MIG" -gt "$PRE_MIG" ]; then
        echo "  ⚠ 직전 배포가 migration 을 적용함(적용 ${PRE_MIG}→${CUR_MIG})."
        echo "    이전 이미지(${PREV}) 코드가 새 스키마와 비호환일 수 있어 keep 은 위험 →"
        if [ "$FORCE" = 1 ]; then
            echo "    (--force 지정 — 강행)"
        else
            echo "    --db=restore (스냅샷으로 스키마째 되돌림) 또는 수동 판단 후 --force." >&2
            exit 1
        fi
    elif [ -z "$PRE_MIG" ]; then
        echo "  (migration 상태 미상 — .mig 사이드카 없음/구 스냅샷. 대부분 무migration 이라 keep 진행. 의심되면 --db=restore.)"
    else
        echo "  keep 안전(직전 배포 migration 없음: ${PRE_MIG}=${CUR_MIG})."
    fi
fi

# --- DB ---
if [ "$DB_MODE" = restore ]; then
    docker compose down
    if [ -n "$SNAP" ]; then
        # 정본 = db/ 서브디렉터리(0.1.64~). 컷오버 전 호스트면 $ROOT/db 없으니 루트로 폴백.
        DB_DIR="$ROOT/db"; [ -d "$DB_DIR" ] || DB_DIR="$ROOT"
        echo "  restore DB ← ${SNAP} → ${DB_DIR}/db.sqlite3 (컨테이너 정지 후 — SQLite WAL torn-copy 방지)"
        cp -p "$SNAP" "${DB_DIR}/db.sqlite3"
        [ -f "${SNAP}-wal" ] && cp -p "${SNAP}-wal" "${DB_DIR}/db.sqlite3-wal" || rm -f "${DB_DIR}/db.sqlite3-wal"
        [ -f "${SNAP}-shm" ] && cp -p "${SNAP}-shm" "${DB_DIR}/db.sqlite3-shm" || rm -f "${DB_DIR}/db.sqlite3-shm"
    else
        echo "  (pre_deploy 스냅샷 없음 — DB 복원 건너뜀; dev 이거나 최초 배포)"
    fi
else
    echo "  db=keep — 현재 DB 유지(운영 데이터 보존). 이미지 태그만 전환."
fi

# --- 이미지 전환 ---
echo "  IMAGE_TAG → ${PREV}"
if grep -q '^IMAGE_TAG=' .env 2>/dev/null; then
    sed -i "s/^IMAGE_TAG=.*/IMAGE_TAG=${PREV}/" .env
else
    echo "IMAGE_TAG=${PREV}" >> .env
fi
docker pull "honestjung/cdgts:${PREV}"
docker compose up -d       # 전 서비스(웹 cdgts + 워커) — up -d cdgts 만이면 워커가 빠진다.

echo "=== rolled back to ${PREV} (db=${DB_MODE}) — ./smoke.sh ${PREV} 로 확인 권장 ==="
