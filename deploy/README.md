# 배포 (Deploy)

fsis2026 패턴 + 프론트(Vite SPA) 멀티스테이지 빌드. 이미지 `honestjung/cdgts` (`X.Y.Z` + `latest`).
개발/테스트 서버와 프로덕션 서버 **모두 `/srv/cdGTS` 에서 docker 컨테이너**로 실행.

## 구성

| 파일 | 역할 |
|---|---|
| `Dockerfile` | 멀티스테이지: node 로 `frontend/dist` 빌드 → python 이미지에 포함. WhiteNoise 서빙. |
| `entrypoint.sh` | collectstatic → migrate → gunicorn(:8000). |
| `build.sh X.Y.Z` | **빌드 호스트**: pytest + version bump + `docker build/push` (`:X.Y.Z` + `:latest`). |
| `docker-compose.dev.yml` | 로컬 빌드/실행 테스트(`--build`). |
| `sync_to_srv.sh` | 운영/테스트 호스트: `host/*` → `/srv/cdGTS`. |
| `host/docker-compose.yml` | `/srv/cdGTS` 실행(이미지 pull, `${IMAGE_TAG}`, `127.0.0.1:8011:8000`). |
| `host/deploy.sh X.Y.Z` | 배포 공통 엔진: pull → .env 갱신 → 컨테이너 교체 → 헬스체크. `DEPLOY_SNAPSHOT=1` 이면 스왑 직전 DB 스냅샷. 직접 호출 X. |
| `host/deploy-prod.sh X.Y.Z` | **프로덕션** 진입점 — `DEPLOY_SNAPSHOT=1`(배포 전 DB 스냅샷) 로 deploy.sh 호출. |
| `host/deploy-dev.sh X.Y.Z` | **개발/테스트** 진입점 — 스냅샷 없이 deploy.sh 호출(DB = 운영 복사본). |
| `host/.env.example` | `/srv/cdGTS/.env` 템플릿. |
| `../scripts/sync-cdgts-db.sh` | (개발/테스트) 운영 DB 를 cron 으로 pull → 히스토리 + 테스트 DB 로 교체. |

## 흐름

**빌드 호스트** (Docker Hub 로그인 필요):
```
./deploy/build.sh 0.1.0        # 테스트 + bump + build + push honestjung/cdgts:0.1.0,latest
```

**각 호스트 최초 1회** (개발/테스트 + 프로덕션):
```
sudo mkdir -p /srv/cdGTS && sudo chown $USER /srv/cdGTS
cp deploy/host/.env.example /srv/cdGTS/.env    # SECRET_KEY·ALLOWED_HOSTS 편집
touch /srv/cdGTS/db.sqlite3
./deploy/sync_to_srv.sh
```

**배포 (매 버전)** — 환경별 진입점 사용:
```
cd ~/projects/cdGTS && git pull
./deploy/sync_to_srv.sh
/srv/cdGTS/deploy-prod.sh 0.1.1     # 프로덕션: 배포 전 DB 스냅샷 후 스왑
# 개발/테스트:
/srv/cdGTS/deploy-dev.sh 0.1.1      # 스냅샷 없이 스왑 (DB = 운영 복사본)
# 초기 데이터 시드 — 통합 seed(자연키, seed/). devlog P02.
docker compose -f /srv/cdGTS/docker-compose.yml exec cdgts \
    python manage.py seed --mode=replace   # 깨끗한 재구축(seed 범위 flush 후 전체 로드 + bake)
# 이후 버전업에서 초기 데이터가 추가됐을 때 (기존 데이터 보존하며 없는 것만):
#   python manage.py seed --mode=add        # 그래프/릴리스는 원자 단위, pk 충돌 없음
#   python manage.py seed --mode=add --dry-run   # 무엇이 insert 될지 미리보기
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
- fsis2026 의 maintenance 페이지 토글은 nginx 연동이라 0.1.x 에선 생략(후속).
- DB 는 SQLite. 공간(GSSP) 기능 착수 시 PostGIS 컨테이너 추가 예정.
