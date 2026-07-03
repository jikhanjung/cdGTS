# 20260703_021 — Docker 배포 (honestjung/cdgts 0.1.0)

> P01 후속. fsis2026 배포 패턴 참조 + 프론트(Vite SPA) 멀티스테이지. 개발/테스트·프로덕션 모두 `/srv/cdGTS`.

## 한 일

### 프로덕션 서빙 (settings/urls/vite)
- `whitenoise` 미들웨어 + `STATIC_ROOT`/`STATICFILES_DIRS`(frontend/dist) + `CompressedStaticFilesStorage`.
- Vite `base`: build 시 `/static/`, dev(serve) 시 `/` (조건부) — 자산이 WhiteNoise `/static/` 로 해소.
- SPA 라우트: dist 있으면 루트 `TemplateView(index.html)`. API 는 동일 오리진 `/api/`(프록시 불요).
- `SECURE_*`/`CSRF_TRUSTED_ORIGINS` env 화(리버스 프록시 뒤 HTTPS 가정). `config/version.py` = 0.1.0.
- requirements: `gunicorn`, `whitenoise` 추가.

### 배포 파일 (`deploy/`, fsis2026 기반)
- `Dockerfile` — 멀티스테이지: **node:22 로 frontend 빌드 → python:3.12 이미지에 dist 포함**. WhiteNoise 서빙.
- `entrypoint.sh` — collectstatic → migrate → gunicorn(:8000).
- `build.sh X.Y.Z` — 빌드 호스트: pytest + version bump + `docker build/push` (`:X.Y.Z` + `:latest`).
- `docker-compose.dev.yml` — 로컬 빌드/실행. `host/docker-compose.yml` — `/srv/cdGTS` 실행(pull, `${IMAGE_TAG}`,
  `127.0.0.1:8010:8000`). `host/deploy.sh` — pull→.env 갱신→down(+DB 스냅샷)→up→헬스체크.
- `sync_to_srv.sh`(host/* → /srv/cdGTS) · `host/.env.example` · `deploy/README.md` · 루트 `.dockerignore`.

## 검증
- 프론트 prod 빌드: index.html 이 `/static/assets/*` 참조.
- **gunicorn + DEBUG=False 로컬**: `/`(SPA) · `/static/assets/*.js` · `/api/node-types/` · `/admin/login/` 모두 **200**.
- **docker build 성공**(honestjung/cdgts:0.1.0 + latest, 253MB) → **컨테이너 실행 검증**:
  entrypoint(collectstatic 157파일 + migrate + gunicorn), `/`·`/admin/login/`·`/api/graphs/`·정적자산 모두 **200**.
- 백엔드 pytest 40 passed 유지.

## 못 한 것 (사용자 몫 — 정직)
- **Docker Hub push** — `docker login` 자격(사용자) 필요. 이미지는 로컬 빌드까지 검증.
- **/srv/cdGTS 셋업 + 실제 배포** — 각 서버 sudo/호스트 고유. `deploy/README.md` 에 절차.
- nginx 리버스 프록시(도메인·HTTPS·정적 캐시)·maintenance 페이지 토글은 0.1.0 에서 생략(후속).

## 다음
- 배포 실행(build.sh push → 각 호스트 sync_to_srv → deploy.sh 0.1.0) 후, **계산 커널**(engine) 착수.
