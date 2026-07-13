# 20260713_142 — 배포 동사(preflight·smoke·rollback) + /healthz (P08.4·P08.5)

[P08](20260713_P08_deploy-data-contract-retrofit.md) 계약의 **동사 층**과 그 동사가 소비하는 **헬스 엔드포인트**.
[P08.2·P08.3](20260713_141_deploy-manifest-and-notes.md)(매니페스트·DEPLOY.md)이 선언·체크리스트였다면,
이번은 그걸 실제로 돌리는 스크립트/뷰.

## P08.5 — `/healthz` (`config/health.py`)

버전 + DB 연결 + 핵심 시스템 행 수 → 200/503 JSON. 가벼운 뷰 하나(스테이크 낮음):
- `{"status", "version"(config.version.VERSION), "counts":{node_types, boundaries, graphs}}`.
- **도메인 불변식 게이트**: `node_types>0 and boundaries>0` 아니면 503 — 0.1.52 함정(빈 이미지 DB 폴백)을
  런타임에서도 잡는다(deploy 시점의 [5/6] DB 바인딩 게이트와 상보).
- 인증 없음(헬스체크는 항상 도달), GET, 부작용 없음. `config/urls.py` 에 `path('healthz', ...)`.
- 버전은 프론트 배지처럼 빌드 시 `config/version.py` 에서 이미지에 구워짐 → smoke 의 "버전 일치" 검사가
  "배포된 컨테이너가 진짜 이 태그인가"를 확인.

## P08.4 — 동사 스크립트

- **`deploy/preflight.sh`**(빌드 호스트, 기억 의존 0) — 마지막 `Bump version` 커밋 이후 `git diff` 로 **위험 표면**
  (migrations/·seed/·.env·compose/Dockerfile·host 스크립트) 자동 플래그 + **seed 냄새 lint**(seed_demo 외
  `seed_*` 관리 명령 = 운영 데이터가 시드로 새는 냄새) + **DEPLOY.md 권위 노트** 출력. go/no-go 판단은 사람/에이전트.
- **`deploy/host/smoke.sh`**(대상 호스트) — `/healthz` 200 + `status ok` + (인자 주면) 버전 일치 + `boundaries>0`.
  jq 없이 grep(`[[:space:]]*` 유연 매칭)으로 파싱 — 호스트 의존 최소.
- **`deploy/host/rollback.sh`**(대상 호스트) — 이전 이미지 태그 + `backup/pre_deploy` **최신 스냅샷** 복원(문제
  배포 직전 상태) + `up`. 스냅샷 없으면(dev) 이미지만.
- **배선**: `deploy.sh` 에 **[6/6] smoke** 단계 추가(실패 시 rollback 안내 후 exit 1). `sync_to_srv.sh` 가
  smoke·rollback 을 함께 `/srv/cdGTS` 로 동기화. `deploy.toml [verbs]` 에 preflight/smoke/rollback 등재,
  `health_probe` 를 `/admin/login/` → `/healthz` 로 승격.

## 검증

- `/healthz` pytest **3**(seeded→ok / 빈 DB→503 / 무인증 도달). 전체 스위트 회귀 없음.
- 스크립트 `bash -n` 문법 + `preflight.sh` 실드런(host 변경 🟡·seed lint 🟢·DEPLOY.md 출력 정상) +
  smoke grep 로직을 실제 `JsonResponse` body 형식(`{"status": "ok", ...}`)으로 positive/negative 확인.
- 배포 절차의 실제 end-to-end(컨테이너 스왑→smoke)는 **다음 릴리스 배포 시** 확인(마이그레이션 없음).

## 남은 것

- **P08.6** — 운영 git pull 제거(host/* 를 이미지/아티팩트로 배송, dolfinid 소스 체크아웃 의존 제거). 인프라
  변경·스테이크 낮음 → 선택·후순위. 이로써 P08 의 핵심(레인 경계·매니페스트·동사·헬스)은 완료.

*근거: `../devdocs/wiki/deploy-data-contract.md`(동사·smoke·preflight) · [P08](20260713_P08_deploy-data-contract-retrofit.md) ·
[deploy/deploy.toml](../deploy/deploy.toml) · [DEPLOY.md](../DEPLOY.md).*
