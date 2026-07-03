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
| `host/deploy.sh X.Y.Z` | 버전 스왑: pull → .env 갱신 → 컨테이너 교체 → 헬스체크. **DB 는 안 건드림.** |
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

**배포 (매 버전)** — DB 는 안 건드림:
```
cd ~/projects/cdGTS && git pull
./deploy/sync_to_srv.sh
/srv/cdGTS/deploy.sh 0.1.1
# 빈 DB 최초 시드(개발/테스트에서 아직 운영 sync 전이면):
docker compose -f /srv/cdGTS/docker-compose.yml exec cdgts \
    sh -c "python manage.py loaddata initial_boundaries initial_node_types"
```

## DB 관리 — 배포와 분리 (fsis 패턴)

- **배포(`deploy.sh`)는 DB 를 건드리지 않는다.** 컨테이너(이미지)만 스왑, `/srv/cdGTS/db.sqlite3` 볼륨 유지.
- **개발/테스트 DB = 운영 복사본** (폐기 가능). `scripts/sync-cdgts-db.sh` 가 운영서버에서 DB 를 pull 해
  히스토리(`~/backups/cdGTS/db_history`, 계층 보관) + 테스트 DB(`/srv/cdGTS/db.sqlite3`)로 교체하고
  컨테이너를 안전 재기동한다. cron:
  ```
  0 4 * * *  /home/jikhanjung/projects/cdGTS/scripts/sync-cdgts-db.sh
  ```
  최초엔 `scripts/sync-cdgts-db.sh` 의 `REMOTE_HOST`(운영서버 주소) 확인 필요.

## 참고 / 후속
- 컨테이너는 `127.0.0.1:8011` 만 노출 — 앞단 **nginx 리버스 프록시**(도메인·HTTPS·정적 캐시)는 호스트에서 별도 구성. (8010은 strati2026 이 사용 중.) 개발/테스트 서버는 도메인 미사용(직접 포트/SSH 터널).
- fsis2026 의 maintenance 페이지 토글은 nginx 연동이라 0.1.x 에선 생략(후속).
- DB 는 SQLite. 공간(GSSP) 기능 착수 시 PostGIS 컨테이너 추가 예정.
