# 배포 (Deploy)

fsis2026 패턴 + 프론트(Vite SPA) 멀티스테이지 빌드. 이미지 `honestjung/cdgts` (`X.Y.Z` + `latest`).
개발/테스트 서버와 프로덕션 서버 **모두 `/srv/cdGTS` 에서 docker 컨테이너**로 실행.

## 구성

> **git-free + self-heal(0.1.58~)**: 운영 서버는 repo 가 필요 없다. 모든 host 파일이 이미지 `/app/deploy/host/*`
> (`COPY . .`)에 실려, 배포 시 `_extract_and_deploy.sh` 가 이미지에서 추출하고 부트스트랩 파일까지 자기 치유한다.
> 배포·데이터 계약(devlog P08) 정형 층: 매니페스트 [`deploy.toml`](deploy.toml) · 릴리스별 델타 [`../DEPLOY.md`](../DEPLOY.md).

| 파일 | 역할 |
|---|---|
| `Dockerfile` | 멀티스테이지: node 로 `frontend/dist` 빌드 → python 이미지에 포함. `COPY . .` 로 `deploy/host/*` 도 이미지에. |
| `entrypoint.sh` | collectstatic → migrate → gunicorn(:8000). 워커는 인자(`run_worker`)로 실행(migrate 경합 회피). |
| `build.sh X.Y.Z [--fast]` | **빌드 호스트**: pytest(+`--fast` 로 생략) + version bump + `docker build/push` (`:X.Y.Z` + `:latest`). |
| `preflight.sh` | **빌드 호스트**: 마지막 배포 이후 위험 표면 diff(migrations·seed·.env·compose) + seed 냄새 lint + `DEPLOY.md` 출력. |
| `remote-prod.sh X.Y.Z [--reseed]` | **빌드 호스트**: `ssh dolfinid '/srv/cdGTS/deploy-prod.sh …'` 얇은 래퍼(원격 prod 배포). `PROD_HOST`/`PROD_DEPLOY` env 로 대상 변경. |
| `deploy.toml` | 선언 매니페스트(image·db_path·has_seed·services·동사·targets prod/test). |
| `docker-compose.dev.yml` | 로컬 빌드/실행 테스트(`--build`). |
| `sync_to_srv.sh` | **repo 있는 머신에서 최초 부트스트랩만**(host/* → /srv/cdGTS). 상시 배포엔 불필요(self-heal). |
| `host/docker-compose.yml` | `/srv/cdGTS` 실행(이미지 pull, `${IMAGE_TAG}`, `127.0.0.1:8011:8000`). **web(cdgts) + worker(cdgts-worker)**. |
| `host/_extract_and_deploy.sh` | git-free 코어: 이미지에서 host 파일 추출 + 부트스트랩 self-heal → deploy.sh 위임. |
| `host/deploy.sh X.Y.Z [--reseed]` | 배포 엔진: (스냅샷)→스왑→migrate→DB바인딩게이트→(`--reseed` 시 재시드)→smoke. **`up -d`(전 서비스)**. 직접 호출 X. |
| `host/deploy-prod.sh X.Y.Z [--reseed]` | **프로덕션** 진입점 — `DEPLOY_SNAPSHOT=1`(배포 전 DB 스냅샷). |
| `host/deploy-dev.sh X.Y.Z [--reseed]` | **개발/테스트** 진입점 — 스냅샷 없이(DB = 운영 복사본). |
| `host/smoke.sh X.Y.Z` | 배포 후 검증: `/healthz` 200 + 버전 일치(필수 인자) + 행 수(python3 JSON, fsis/fcmanager 동형). prod SSL 대응(`X-Forwarded-Proto`). |
| `host/rollback.sh <이전 X.Y.Z> [--db=keep\|restore]` | 코드/DB 롤백 분리: `--db=keep`(기본, 이미지만 전환·운영 데이터 보존) · `--db=restore`(정지 후 pre_deploy 스냅샷 복원). keep 가드=직전 배포 migration 시 차단(`--force`/`--db=restore`). |
| `host/maintenance.html` | prod 스왑/스냅샷 동안 nginx 가 띄우는 점검 페이지. |
| `host/.env.example` | `/srv/cdGTS/.env` 템플릿. |
| `../config/health.py` | `/healthz` 엔드포인트(버전+DB+핵심 행 수 → 200/503). smoke 가 소비. |
| `../scripts/sync-cdgts-db.sh` | (개발/테스트) 운영 DB 를 cron 으로 pull → 히스토리 + 테스트 DB 로 교체. |
| `../scripts/backup_db.py` | (운영) hourly DB 백업(sqlite online backup, 12개 유지) — cron 1회 등록 + 배포 시 self-heal 추출. |

## 흐름 (git-free, 0.1.58~)

**빌드 호스트** (m710q, Docker Hub 로그인 필요):
```
./deploy/preflight.sh          # (선택) 위험 표면 diff + seed 냄새 + DEPLOY.md 델타
./deploy/build.sh 0.1.60       # 테스트 + bump + build + push honestjung/cdgts:0.1.60,latest
#   버전만/프론트만 변경이면 --fast 로 pytest 생략
```

**각 호스트 최초 1회 부트스트랩** (개발/테스트 + 프로덕션):
```
sudo mkdir -p /srv/cdGTS/backup && sudo chown $USER /srv/cdGTS
cp deploy/host/.env.example /srv/cdGTS/.env    # SECRET_KEY·ALLOWED_HOSTS·DATABASE_PATH 편집
touch /srv/cdGTS/db.sqlite3
# 부트스트랩 파일 심기 — repo 있으면:  ./deploy/sync_to_srv.sh
# repo 없으면(git-free, prod 권장):
cd /srv/cdGTS && CID=$(docker create honestjung/cdgts:0.1.60)
for f in _extract_and_deploy.sh deploy-prod.sh deploy-dev.sh; do docker cp "$CID:/app/deploy/host/$f" ./; done
docker rm "$CID" && chmod +x _extract_and_deploy.sh deploy-prod.sh deploy-dev.sh
```
이후 부트스트랩 파일까지 **self-heal** 되므로 다시 손댈 일 없다. **운영 서버에 repo 불필요**(삭제 가능).

**배포 (매 버전)** — 진입점 한 줄. git pull·sync 불요:
```
/srv/cdGTS/deploy-prod.sh 0.1.60            # 프로덕션: 스냅샷 → 추출 → 스왑 → smoke
/srv/cdGTS/deploy-dev.sh  0.1.60            # 개발/테스트: 스냅샷 없이
#   시드/레이아웃 변경 릴리스나 빈 DB 최초 배포면 --reseed 를 붙인다:
/srv/cdGTS/deploy-prod.sh 0.1.60 --reseed   # migrate 후 smoke 전 seed --mode=replace + seed_demo
```
m710q 에서 prod 까지 원격으로 — 얇은 래퍼 `./deploy/remote-prod.sh 0.1.60 [--reseed]`
(= `ssh dolfinid '/srv/cdGTS/deploy-prod.sh 0.1.60 [--reseed]'` 를 대신 실행. `PROD_HOST`/`PROD_DEPLOY` env 로 대상 변경).

**seed** (통합 seed, 자연키, `seed/`. devlog P02·140):
```
# --reseed 플래그가 자동 실행하는 것과 동일 — 수동으로 돌릴 때:
docker exec cdgts python manage.py seed --mode=replace   # 시스템 데이터만 정합(운영 데이터 보존 upsert)
docker exec cdgts python manage.py seed_demo             # 데모 그래프/릴리스 복원(replace 가 지우므로)
#   add = 없는 것만 insert(그래프/릴리스 원자 skip): python manage.py seed --mode=add [--dry-run]
# seed 세트: chrono(경계·단위) · nodes(노드타입) · graph(예제 3종) · releases(ICC-2012/2024 diff 데모).
```

## DB 관리 — 배포와 분리 (fsis 패턴)

- **배포는 기본적으로 DB 를 건드리지 않는다** — 컨테이너(이미지)만 스왑, `/srv/cdGTS/db.sqlite3` 볼륨 유지.
  단 **prod(`deploy-prod.sh`)는 스왑 직전 pre_deploy 스냅샷**을 떠 나쁜 마이그레이션에 대비(개발/테스트 일일 pull 과 별개의 로컬 방어선).
- **개발/테스트 DB = 운영 복사본** (폐기 가능). `scripts/sync-cdgts-db.sh` 가 운영서버에서
  **sqlite online backup API(`.backup`)로 원자적 스냅샷을 만든 뒤 단일 파일만 pull**(WAL hot-copy
  torn/불일치 회피) → 히스토리(`~/backups/cdGTS/db_history`, 30일 계층) + **NAS 오프사이트
  (`/nas/JikhanJung/cdgts_backup`, 90일 계층)** + 테스트 DB(`/srv/cdGTS/db.sqlite3`)로
  교체하고 컨테이너를 안전 재기동한다. cron:
  ```
  0 4 * * *  /home/jikhanjung/projects/cdGTS/scripts/sync-cdgts-db.sh
  ```
  운영서버: GCP `dolfinid-2` = `cdgts.paleobytes.info`(34.64.158.160), 사용자 `honestjung`
  (SSH 키 인증). `dolfinid` 단독 이름은 이 서버에서 해석 안 됨 → `cdgts.paleobytes.info` 사용.

## 참고 / 후속
- 컨테이너는 `127.0.0.1:8011` 만 노출 — 앞단 **nginx 리버스 프록시**(도메인·HTTPS·정적 캐시)는 호스트에서 별도 구성. (8010은 strati2026 이 사용 중.) 개발/테스트 서버는 도메인 미사용(직접 포트/SSH 터널).
- **maintenance 점검 페이지**: `maintenance.html` 은 이미지에서 추출·설치된다(`/srv/cdGTS/maintenance.html`).
  prod 스냅샷 창(`deploy.sh` [3/6] `docker compose down` 동안 사이트 다운) 동안 nginx 로 이 페이지를 띄우려면
  앞단 nginx 에 수동으로 fallback 을 걸어야 한다(자동 토글은 아직 미배선 — 후속). 파일 자체는 상시 배포에 포함.
- DB 는 SQLite. 공간(GSSP) 기능 착수 시 PostGIS 컨테이너 추가 예정.
