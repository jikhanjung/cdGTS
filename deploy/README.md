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
| `host/docker-compose.yml` | `/srv/cdGTS` 실행(이미지 pull, `${IMAGE_TAG}`, `127.0.0.1:8010:8000`). |
| `host/deploy.sh X.Y.Z` | 버전 스왑: pull → .env 갱신 → down(+DB 스냅샷) → up → 헬스체크. |
| `host/.env.example` | `/srv/cdGTS/.env` 템플릿. |

## 흐름

**빌드 호스트** (Docker Hub 로그인 필요):
```
./deploy/build.sh 0.1.0        # 테스트 + bump + build + push honestjung/cdgts:0.1.0,latest
```

**각 호스트 최초 1회** (개발/테스트 + 프로덕션):
```
sudo mkdir -p /srv/cdGTS/backup && sudo chown $USER /srv/cdGTS
cp deploy/host/.env.example /srv/cdGTS/.env    # SECRET_KEY·ALLOWED_HOSTS 편집
touch /srv/cdGTS/db.sqlite3
./deploy/sync_to_srv.sh
```

**배포 (매 버전)**:
```
cd ~/projects/cdGTS && git pull
./deploy/sync_to_srv.sh
/srv/cdGTS/deploy.sh 0.1.0
# 최초 배포 후 시드가 필요하면:
docker compose -f /srv/cdGTS/docker-compose.yml exec cdgts \
    sh -c "python manage.py loaddata initial_boundaries initial_node_types"
```

## 참고 / 후속
- 컨테이너는 `127.0.0.1:8010` 만 노출 — 앞단 **nginx 리버스 프록시**(도메인·HTTPS·정적 캐시)는 호스트에서 별도 구성.
- fsis2026 의 maintenance 페이지 토글은 nginx 연동이라 0.1.0 에선 생략(후속).
- DB 는 SQLite. 공간(GSSP) 기능 착수 시 PostGIS 컨테이너 추가 예정.
