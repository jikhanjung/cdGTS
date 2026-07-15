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

# --- 설정 ---
# 운영서버: GCP 인스턴스 dolfinid-2, cdgts.paleobytes.info(34.64.158.160), 사용자 honestjung.
REMOTE_USER="${CDGTS_REMOTE_USER:-honestjung}"
REMOTE_HOST="${CDGTS_REMOTE_HOST:-cdgts.paleobytes.info}"
REMOTE_PATH="/srv/cdGTS"
REMOTE="${REMOTE_USER}@${REMOTE_HOST}"

BACKUP_DIR="${HOME}/backups/cdGTS"
DB_HISTORY_DIR="${BACKUP_DIR}/db_history"
CURRENT_DIR="${BACKUP_DIR}/current"
LOG_FILE="${BACKUP_DIR}/sync.log"

# 이 서버의 테스트/개발 컨테이너가 mount 하는 DB (host/docker-compose.yml 볼륨)
# 정본 = db/ 서브디렉터리(0.1.64~). 컷오버 전이면 루트로 폴백(전환기 안전).
DEV_ROOT="/srv/cdGTS"
DEV_DB="${DEV_ROOT}/db/db.sqlite3"; [ -d "${DEV_ROOT}/db" ] || DEV_DB="${DEV_ROOT}/db.sqlite3"
COMPOSE="${DEV_ROOT}/docker-compose.yml"
CONTAINER="cdgts"          # 웹 서비스명(존재 확인용). 정지/기동은 **전 서비스** — 아래 참조.

LOCAL_DAILY_DAYS=30

# NAS 오프사이트 백업 (다른 백업 스크립트와 동일 관례: /nas/JikhanJung/<project>_backup)
NAS_DIR="/nas/JikhanJung/cdgts_backup"
NAS_DAILY_DAYS=90

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

# --- 1. 운영서버에서 원자적 스냅샷 생성 후 pull ---
# WAL 모드 hot-copy(torn/불일치) 회피: live db + -wal + -shm 를 따로 긁어오면
# 세 파일이 서로 다른 시점일 수 있다. 대신 prod 에서 sqlite online backup API 로
# 일관 스냅샷(단일 파일)을 만들고 그것만 가져온다. (fsis backup_db.py 의 .backup 방식)
REMOTE_SNAP="${REMOTE_PATH}/.db_sync_snapshot.sqlite3"
# 정본 = db/ 서브디렉터리(0.1.64~ 컷오버). 원격이 컷오버 전이면 루트로 폴백(전환기 안전).
REMOTE_DB=$(ssh "$REMOTE" "if [ -f '${REMOTE_PATH}/db/db.sqlite3' ]; then echo '${REMOTE_PATH}/db/db.sqlite3'; else echo '${REMOTE_PATH}/db.sqlite3'; fi")
ssh "$REMOTE" "python3 - '${REMOTE_DB}' '${REMOTE_SNAP}'" <<'PYEOF' || { log "ERROR: prod 원자적 스냅샷 실패 (${REMOTE})"; exit 1; }
import sqlite3, sys
src = sqlite3.connect(sys.argv[1])
dst = sqlite3.connect(sys.argv[2])
try:
    src.backup(dst)              # online backup API — writer 있어도 일관 스냅샷

    # --- 반출 위생(egress sanitize) ---
    # ⚠️ 대상은 dst(= 곧 반출될 스냅샷 사본)뿐. **라이브 운영 DB(src)는 읽기만 한다** —
    #    운영에 로그인해 있는 사람은 아무 영향 없다.
    #
    # 이 스냅샷은 운영의 신뢰 경계를 떠난다: m710q(/srv·~/backups) → NAS(90일 보존).
    # `django_session.session_key` 는 **쿠키에 담기는 값 그 자체(bearer 토큰)** 라,
    # 사본을 읽은 사람이 그걸 **운영에** 되제시하면 그대로 로그인된다 — 운영이 자기 DB 에서
    # 그 행을 찾아 자기 SECRET_KEY 로 디코드하므로 **prod/test SECRET_KEY 가 달라도 안 막힌다**.
    # 반면 테스트서버엔 애초에 무용지물이다(SECRET_KEY 불일치 → 서명 검증 실패 → 빈 세션).
    # 즉 이 행들은 **테스트엔 쓸모없고 운영엔 위험한** 순수 손해라 반출 전에 지운다.
    #
    # 비밀번호 해시는 남긴다: pbkdf2_sha256 1,000,000회(Django 5.2 기본)로 강하고,
    # 지우면 테스트서버 로그인이 막힌다. 세션과 달리 "그냥 쓸 수 있는" 값이 아니다.
    try:
        # secure_delete=ON: 지운 행의 자리를 0 으로 덮는다. 이 빌드 기본값이 1 이지만
        # **컴파일 타임 옵션**이라 빌드에 기대지 않고 명시한다(OFF 빌드 실측: 200행 DELETE 후 200개 전량 잔존).
        dst.execute("PRAGMA secure_delete=ON")
        n = dst.execute("DELETE FROM django_session").rowcount
        dst.commit()

        # ⚠️ VACUUM 이 **필수**다 — 위 DELETE 로는 부족하다.
        # `backup()` 은 소스를 페이지 단위로 복사하므로 **free page 까지 그대로 옮긴다.** 즉 운영 DB 에서
        # 과거에 지워진 세션(로그아웃·만료 정리·로그인 시 세션 회전)의 잔류가 스냅샷에 딸려오는데,
        # 그건 이미 "행"이 아니라 free page 라 `DELETE FROM django_session` 이 **닿지 못한다**
        # (secure_delete 를 켜도 마찬가지 — 지금 지우는 행만 덮을 뿐이다).
        # 실측: 소스 free page 에 200개 잔류 → backup 직후 스냅샷 200개 → DELETE 후에도 200개 → VACUUM 후 0개.
        # 파일을 재구축하는 VACUUM 만이 상속된 잔류까지 없앤다. (스냅샷 대상이라 라이브 영향 없음.)
        dst.execute("VACUUM")    # 열린 트랜잭션이 있으면 실패 → 위 commit() 뒤에 와야 한다
        print(f"  sanitize: django_session {n}행 제거 + VACUUM(상속 잔류 포함 재구축)")
    except sqlite3.Error as e:
        print(f"  ERROR: sanitize 실패 — {e}", file=sys.stderr)
        sys.exit(1)              # 위생 실패한 스냅샷은 반출하지 않는다

    # 아카이브에 동시 writer 는 없다 → -wal/-shm 이 아예 없는 단일 파일로.
    # (이 스크립트가 이미 "스냅샷 = 일관된 단일 파일"을 전제하고 있다.)
    dst.execute("PRAGMA journal_mode=DELETE")
finally:
    dst.close(); src.close()
PYEOF
scp -q "${REMOTE}:${REMOTE_SNAP}" "$SNAP" || { ssh "$REMOTE" "rm -f '${REMOTE_SNAP}'" 2>/dev/null || true; log "ERROR: scp 실패 (${REMOTE})"; exit 1; }
ssh "$REMOTE" "rm -f '${REMOTE_SNAP}' '${REMOTE_SNAP}-wal' '${REMOTE_SNAP}-shm'" 2>/dev/null || true
log "pull 완료(원자적 스냅샷): $SNAP ($(du -h "$SNAP" | cut -f1))"

# --- 2. current 갱신 + 히스토리 정리 ---
cp -f "$SNAP" "${CURRENT_DIR}/db.sqlite3"
DEL=$(cleanup_db "$DB_HISTORY_DIR" $LOCAL_DAILY_DAYS)
[ "$DEL" -gt 0 ] && log "히스토리 정리: ${DEL}개 삭제 (${LOCAL_DAILY_DAYS}일 초과, 월초/연말 보존)"

# --- 3. NAS 오프사이트 백업 (단일 일관 스냅샷이라 -wal/-shm 없음) ---
if timeout 10 test -d "$NAS_DIR"; then
    NAS_DB_DIR="${NAS_DIR}/db_history"
    NAS_CURRENT="${NAS_DIR}/current"
    mkdir -p "$NAS_DB_DIR" "$NAS_CURRENT"
    cp -f "$SNAP" "${NAS_DB_DIR}/db_${TODAY}.sqlite3"
    cp -f "$SNAP" "${NAS_CURRENT}/db.sqlite3"
    NAS_DEL=$(cleanup_db "$NAS_DB_DIR" $NAS_DAILY_DAYS)
    [ "$NAS_DEL" -gt 0 ] && log "NAS 정리: ${NAS_DEL}개 삭제 (${NAS_DAILY_DAYS}일 초과, 월초/연말 보존)"
    log "NAS 백업 완료 (${NAS_DIR})"
else
    log "WARN: NAS 디렉토리 없음 (${NAS_DIR}) — 건너뜀"
fi

# --- 4. 개발/테스트 DB 교체 ---
# 스냅샷은 이미 일관된 단일 파일(-wal/-shm 없음). 컨테이너가 DB 를 열고 있으므로
# 라이브 교체를 피해 잠시 정지 → 교체 → 재기동. 남아있던 -wal/-shm 은 제거.
#
# ⚠️ **전 서비스를 정지해야 한다** (`stop`/`up -d` 를 서비스명 없이). compose 에는 웹(cdgts)과
# 워커(cdgts-worker, run_worker 폴링)가 있고 **둘 다 같은 sqlite 를 WAL 로 연다**. 웹만 정지하면
# 워커가 DB 를 쥔 채로 남고, 그 발밑에서 메인 파일을 cp 로 덮고 -wal/-shm 을 지우면 워커의 캐시
# 페이지 상태와 어긋나 **DB 가 깨진다**(2026-07-15 실제 발생 — graph_nodeinstance btree 손상 2회).
# deploy.sh 의 `up -d cdgts` → `up -d` 수정(0.1.60·devlog 144)과 **같은 부류의 버그**였다.
if [ -f "$COMPOSE" ] && docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER"; then
    log "전 서비스 정지(웹+워커) → DB 교체 → 재기동"
    docker compose -f "$COMPOSE" stop >/dev/null 2>&1 || true          # 서비스명 없음 = 전부(워커 포함)
    cp -f "$SNAP" "$DEV_DB"
    rm -f "${DEV_DB}-wal" "${DEV_DB}-shm"
    docker compose -f "$COMPOSE" up -d >/dev/null 2>&1                 # 전부 기동
    log "DB 교체 + 재기동 완료(웹+워커)"
else
    cp -f "$SNAP" "$DEV_DB"
    rm -f "${DEV_DB}-wal" "${DEV_DB}-shm"
    log "컨테이너 미실행 — DB 파일만 교체"
fi

log "========== 완료 =========="
