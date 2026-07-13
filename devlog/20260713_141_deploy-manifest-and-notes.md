# 20260713_141 — 배포 매니페스트 + 운영 델타 노트 (P08.2·P08.3)

[P08](20260713_P08_deploy-data-contract-retrofit.md) 의 정형 층 두 개. 배포 지식을 **기억이 아니라 파일**로
내려 단일 오케스트레이터(또는 Claude Code)가 프로젝트 지식 없이 배포·검증하게 하는 계약의 뼈대.

## P08.2 — `deploy/deploy.toml` (선언적 매니페스트)

프로젝트당 하나의 선언 파일. 실측으로 채움:
- `image`·`db_path`·`has_seed`·`services=["cdgts","cdgts-worker"]`(web + async worker).
- `health_url=/healthz`(P08.5 예정) + 현재 smoke probe(`/admin/login/`) 병기 — 매니페스트가 목표와 현실을 모두 명시.
- `[verbs]` — 계약 동사 이름 → 현 스크립트 매핑(build/sync/deploy/seed). preflight/smoke/rollback 은 P08.4.
- `[targets.prod]` = GCP **dolfinid-2**(`cdgts.paleobytes.info`, 34.64.158.160, SSH 키, nginx+certbot,
  `deploy-prod.sh` 스냅샷=1) · `[targets.test]` = **m710q**(빌드+테스트 겸용, tailscale serve→127.0.0.1:8011,
  `deploy-dev.sh` 스냅샷=0, DB=운영 복사본). 근거: `deploy/README.md`.

## P08.3 — `DEPLOY.md` (릴리스별 append-only 운영 델타 노트)

devlog 는 배포 caveat 에 lossy(산문에 묻힘·안 적힘·다중 릴리스 배포 시 범위 밖). 그 반대 파일:
- **상시 불변식**(릴리스 무관): 시드/레이아웃 변경→`replace` 재시드(P08.1 이후 운영 데이터 보존) ·
  `.env` `DATABASE_PATH=/app/hostdb/db.sqlite3` 바인딩(0.1.52 함정, [5/5] 게이트) · migrate 자동 · Crossref 외부망.
- **릴리스 노트**(최신→과거, 🔴 필수/🟡 주의/🟢 무조치): 0.1.3~P08.1 소급 추출. HANDOFF 산문에서 배포에 필요한
  줄만 뽑음. 앞으로 릴리스마다 맨 위에 한두 줄 append.

## 검증

- 문서·설정 파일만(코드·마이그레이션 무관). 배포 절차 자체는 무변경 — 기존 `build/sync/deploy` 스크립트가
  진실원, 이 두 파일은 그 위의 선언·체크리스트 층.
- `deploy.toml` 값은 `deploy/host/docker-compose.yml`·`.env.example`·`deploy/README.md` 실측과 대조.

## 남은 것 (P08 후속)

- **P08.4** — `preflight`(위험 표면 diff + seed 냄새 lint + DEPLOY.md 델타 출력)·`smoke`(버전 일치+행 수)·
  `rollback`(이전 이미지 + `backup/pre_deploy` 스냅샷 복원) 신규.
- **P08.5** — `/healthz`(버전+DB+핵심 행 수). 그러면 `deploy.toml health_url` 이 실체를 얻고 smoke 가 정형화.
- **P08.6** — 운영 git pull 제거(host/* 를 이미지/아티팩트로).

*근거: `../devdocs/wiki/deploy-data-contract.md`(매니페스트+동사) · [P08](20260713_P08_deploy-data-contract-retrofit.md) ·
[deploy/README.md](../deploy/README.md).*
