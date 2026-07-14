# 20260714_147 — 3-repo 배포 일관성 정렬 + hourly DB 백업

계약(`../devdocs/wiki/deploy-data-contract.md`)과 정렬된 3개 프로젝트(cdGTS·fcmanager·fsis2026)의 **배포 스크립트를
서로 대조해 형태를 통일**한 작업의 cdGTS 측 반영. 같은 계약을 따르는데 세부 구현(헬스 대기 대상·smoke 검증 방식·
DB 게이트 조회법·매니페스트 표기·백업 트랙)이 repo 마다 조금씩 달랐던 것을 하나로 맞췄다.

## 배경 — 균질화의 다음 단계

계약의 목표는 "동사 몇 개로 압축된 균일 인터페이스". P08 로 cdGTS 에 동사·매니페스트·git-free 를 세웠지만,
fcmanager·fsis 를 나란히 놓고 보니 **같은 동사의 속살이 미세하게 갈라져** 있었다(예: smoke 가 cdGTS 는 grep,
fsis 는 python3 JSON). 이 미세 드리프트가 쌓이면 "한 번 익히면 전 프로젝트에 상각" 이라는 계약 전제가 무너진다.

## cdGTS 측 변경 (형제 repo 와 동형화)

- **hourly DB 백업 신설** — `scripts/backup_db.py`(sqlite online backup API, 최근 12개 유지, 디스크 여유 2GB 가드).
  종전 cdGTS 운영 백업은 **pre_deploy 스냅샷(배포 시) + m710q daily pull**(`sync-cdgts-db.sh`, NAS 오프사이트)뿐 →
  최악 손실창 24h. hourly 트랙 추가로 fcmanager/fsis 와 정렬. **pre_deploy retention(deploy.sh, 20개)과 분리**
  — 다른 수치로 같은 디렉터리를 prune 하던 fsis 충돌 교훈대로, backup_db.py 는 `backup/cdgts_*.sqlite3`(루트)만,
  스냅샷은 `backup/pre_deploy/` 서브디렉터리. 배포 시 이미지에서 self-heal 추출.
- **`deploy.sh`** — ⓐ `DEPLOY_SNAPSHOT` 미설정 시 기본 **0→1**(직접 호출도 안전측; dev 는 래퍼가 0 명시). ⓑ 기동
  대기 대상 `/admin/login/`→**`/healthz`**. ⓒ DB 바인딩 게이트 순수 `python -c`→**`manage.py shell -c`**(계약의
  DB 게이트 이식 함정 — `DJANGO_SETTINGS_MODULE` 없는 컨테이너에서 `python -c` false-fail, fcmanager 0.6.12 실측).
- **`smoke.sh`** — grep 기반→**python3 stdlib JSON 파싱**(jq 비의존), 버전 인자 **필수화**(종전 선택). status·version·
  counts(boundaries/node_types>0)를 구조적으로 검증.
- **`deploy.toml`** — `db_path` = **DB 파일 전체 경로** 표준 표기(종전 디렉터리), smoke 동사 인자 필수 반영.
- **`_extract_and_deploy.sh`** — `scripts/backup_db.py` 이미지 추출 추가. **`preflight.sh`** — backup_db.py 변경 플래그.
  **`README.md`**·**`DEPLOY.md`** 반영.

## 배포·검증 (0.1.63, 양 서버)

- `build.sh 0.1.63`(pytest 178) → `deploy-dev.sh`(m710q) → `remote-prod.sh`(prod). 둘 다 새 **python3 JSON smoke**
  (`PASS: version=0.1.63…`)·healthz 대기·write probe(uid 1000/1001)·비-root 통과.
- **backup_db.py self-heal 한 세대 지연** — 이번 배포를 **실행한** 추출기는 호스트의 0.1.62 판(추출 코드 없음)이라
  backup_db.py 를 안 꺼냈다. 새 추출기(코드 포함)는 이번에 self-heal → **다음 배포부터 자동**. 이번은 `docker create`+
  `docker cp /app/scripts/backup_db.py`(0.1.63 이미지)로 **1회 수동 부트스트랩**(git-free 부트스트랩과 동일 관례).
- **backup 디렉터리 소유권** — prod `/srv/cdGTS/backup` = **1001(honestjung) 소유**라 cron(honestjung) 쓰기 OK →
  test-run 성공(`cdgts_20260714_03.sqlite3` 1.1MB). ⚠️ m710q 는 `/srv/cdGTS/backup` 이 **root 소유**(과거 root era 잔재)
  라 backup_db.py 가 dest 를 못 쓴다 — 그러나 m710q 는 deploy-dev 가 snapshot 안 뜨고 cron 도 없어 무해(테스트 전용).
- **prod cron 등록 완료**(2026-07-14): `0 * * * * /usr/bin/python3 /srv/cdGTS/scripts/backup_db.py >> /srv/cdGTS/backup/backup.log 2>&1`
  (fcmanager backup 항목과 공존, 기존 crontab 보존). prod web+worker uid 1001·공개 healthz 0.1.63 확인.

*근거: `../devdocs/wiki/deploy-data-contract.md`(§동사 전반·백업) · [145](20260713_145_deploy-contract-external-review.md)·[146](20260714_146_nonroot-container.md). fcmanager·fsis2026 동측 정렬은 각 repo devlog.*
