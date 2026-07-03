#!/bin/bash
# =============================================================================
# cdGTS DB 동기화 — 운영서버 DB 를 이 개발/테스트 서버로 받아와 테스트 DB 로 사용.
# fsis2026 scripts/backup-fsis.sh 의 "DB pull + dev 동기화" 패턴 (cdGTS 는 uploads 없음 → DB 만).
#
# cron 등록:  crontab -e
#   0 4 * * *  /home/jikhanjung/projects/cdGTS/scripts/sync-cdgts-db.sh
# 수동:        REMOTE_HOST=<운영주소> ./scripts/sync-cdgts-db.sh
# =============================================================================
set -euo pipefail

# --- 설정 (운영서버 주소는 환경변수/여기서 지정) ---
REMOTE_USER="${CDGTS_REMOTE_USER:-devops}"
REMOTE_HOST="${CDGTS_REMOTE_HOST:-cdgts.paleobytes.info}"   # TODO: 실제 운영서버 host/IP 확인
REMOTE_PATH="/srv/cdGTS"
REMOTE="${REMOTE_USER}@${REMOTE_HOST}"

BACKUP_DIR="${HOME}/backups/cdGTS"
DB_HISTORY_DIR="${BACKUP_DIR}/db_history"
CURRENT_DIR="${BACKUP_DIR}/current"
LOG_FILE="${BACKUP_DIR}/sync.log"

# 이 서버의 테스트/개발 컨테이너가 mount 하는 DB (host/docker-compose.yml 볼륨)
DEV_ROOT="/srv/cdGTS"
DEV_DB="${DEV_ROOT}/db.sqlite3"
COMPOSE="${DEV_ROOT}/docker-compose.yml"
CONTAINER="cdgts"

LOCAL_DAILY_DAYS=30

mkdir -p "$DB_HISTORY_DIR" "$CURRENT_DIR"
log() { echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"; }

# 계층 정리(fsis 와 동일): N일 초과 → 매달 1일만 보관, 12/01 영구. 파일명 db_YYYYMMDD.sqlite3
cleanup_db() {
    local dir=$1 daily_days=$2 deleted=0
    while IFS= read -r file; do
        local base datestr month day
        base=$(basename "$file"); datestr=${base#db_}; datestr=${datestr%.sqlite3}
        month=${datestr:4:2}; day=${datestr:6:2}
        [ "$month" = "12" ] && [ "$day" = "01" ] && continue
        [ "$day" = "01" ] && continue
        rm -f "$file" "${file}-wal" "${file}-shm"; ((deleted++))
    done < <(find "$dir" -name "db_*.sqlite3" ! -name "*-wal" ! -name "*-shm" -mtime +${daily_days} 2>/dev/null)
    echo $deleted
}

log "========== cdGTS DB sync 시작 (from ${REMOTE}) =========="
TODAY=$(date +%Y%m%d)
SNAP="${DB_HISTORY_DIR}/db_${TODAY}.sqlite3"

# --- 1. 운영서버에서 DB pull (WAL/SHM 부속 포함) ---
if scp -q "${REMOTE}:${REMOTE_PATH}/db.sqlite3" "$SNAP"; then
    scp -q "${REMOTE}:${REMOTE_PATH}/db.sqlite3-wal" "${SNAP}-wal" 2>/dev/null || true
    scp -q "${REMOTE}:${REMOTE_PATH}/db.sqlite3-shm" "${SNAP}-shm" 2>/dev/null || true
    log "pull 완료: $SNAP ($(du -h "$SNAP" | cut -f1))"
else
    log "ERROR: pull 실패 (${REMOTE})"; exit 1
fi

# --- 2. current 갱신 + 히스토리 정리 ---
cp -f "$SNAP" "${CURRENT_DIR}/db.sqlite3"
DEL=$(cleanup_db "$DB_HISTORY_DIR" $LOCAL_DAILY_DAYS)
[ "$DEL" -gt 0 ] && log "히스토리 정리: ${DEL}개 삭제 (${LOCAL_DAILY_DAYS}일 초과, 월초/연말 보존)"

# --- 3. 개발/테스트 DB 교체 ---
# SQLite 파일을 컨테이너가 열고 있으면 라이브 교체는 위험 → 잠시 정지 후 교체, 재기동.
if [ -f "$COMPOSE" ] && docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER"; then
    log "컨테이너 정지 → DB 교체 → 재기동"
    docker compose -f "$COMPOSE" stop "$CONTAINER" >/dev/null 2>&1 || true
    cp -f "$SNAP" "$DEV_DB"
    rm -f "${DEV_DB}-wal" "${DEV_DB}-shm"
    [ -f "${SNAP}-wal" ] && cp -f "${SNAP}-wal" "${DEV_DB}-wal" || true
    [ -f "${SNAP}-shm" ] && cp -f "${SNAP}-shm" "${DEV_DB}-shm" || true
    docker compose -f "$COMPOSE" up -d "$CONTAINER" >/dev/null 2>&1
    log "DB 교체 + 재기동 완료"
else
    cp -f "$SNAP" "$DEV_DB"
    rm -f "${DEV_DB}-wal" "${DEV_DB}-shm"
    log "컨테이너 미실행 — DB 파일만 교체"
fi

log "========== 완료 =========="
