# HANDOFF — Current Work Status

**Last updated**: 2026-07-04 (**v0.1.2 운영서버 배포 완료**. 개념 코퍼스 13주제(한/영 26파일) + 스키마 v0 위에
앱 아키텍처 → 개발계획 P01 → **Phase 0~6 구현 → 계산 커널 → Docker 배포 → 배포/DB 분리·원자적 sync·NAS 백업
→ 예제 그래프 3종 → 릴리스 diff UI**. 스택 확정: **Django 5.2.12 + SQLite + DRF 3.17 + React Flow(Vite)**.
5개 앱[chrono·nodes·graph·engine·releases] + 프론트 노드 에디터/diff 뷰. 백엔드 **pytest 59 passed**.
운영 **cdgts.paleobytes.info @ 0.1.2**, 개발/테스트 **@ 0.1.1**. devlog 001~031 push.)

> 과거 작업 내역은 `devlog/` 에 모두 기록됨. 본 문서는 **현재 상태 + 다음 작업**만 유지.
> 개념 지도 `docs/concept-map.md` · 앱 설계 `docs/app-architecture.md` · 개발 계획 `devlog/*_P01_*` · backlog `TODOs.md`.

## 현재 상태

- **성격**: 브레인스토밍 저장소 → **실행 가능한 코드베이스 + 실배포**(개념 코퍼스는 `docs/` 에 그대로 유지).
- **스택**: Django **5.2.12**, DB **SQLite**(공간 기능 착수 시 PostGIS), **DRF 3.17.1**, 프론트 **React 18 +
  @xyflow/react 12 + Vite**(`frontend/`, dev 는 `/api` 프록시). venv `/home/jikhanjung/venv/cdGTS`.
- **앱 5개** (의존: chrono ◁ nodes ◁ graph ◁ engine ◁ releases):
  - `chrono` — 정본 registry(Unit 이중명명·Boundary·Lineage·Authority·Ratification·Locality). fixture 세 경계.
  - `nodes` — 타입 시스템(NodeType 12 + Port) + `Distribution` 값객체(충실도 L0–L5). fixture 12타입.
  - `graph` — DAG(Graph·NodeInstance·Edge·NodeGroup·Gateway) + DAG 불변식 + DRF `GET/PUT /api/graphs/{id}`
    React Flow 왕복. fixture **예제 그래프 3종**(GSSA / P–T / 캄브리아기 기저 상관).
  - `engine` — 평가(EvalRun·NodeResult 콘텐츠해시 증분·CoherenceCertificate) + `POST /api/graphs/{id}/evaluate/`.
    **계산 커널**(numpy/scipy): 노드타입별 dispatch + age-depth model(선형보간 + spline MC).
  - `releases` — ModelCandidate·Release(selection+clamps)·BoundaryRecord(bake)·Clamp + bake/diff API
    (`/api/releases/{id}/bake/`, `/diff/?a=&b=`). fixture 예제 릴리스 2종(값 diff + 토폴로지 diff 데모).
- **프론트**: 팔레트 → 캔버스 drag&drop → 저장(PUT)/평가 + 결과 뱃지, **그래프 선택 드롭다운**,
  **릴리스 Diff 뷰**(값/토폴로지 직교, 인라인 bake). `npm run build` 통과.
- **배포/운영**:
  - Docker 이미지 `honestjung/cdgts`(numpy/scipy 포함), `deploy/build.sh <ver>` 로 pytest→bump→build→push.
  - **운영서버** `cdgts.paleobytes.info` @ **0.1.2**(nginx + certbot). **개발/테스트** `127.0.0.1:8011` @ 0.1.1.
  - deploy-prod.sh / deploy-dev.sh 분리, 스왑 중 nginx maintenance. DB 를 배포에서 분리 + prod→test sync.
  - **백업**: 원자적 스냅샷(WAL torn-copy 방지) + NAS 오프사이트 + **04:00 cron**.
- **초기 데이터(seed)**: 통합 `seed/`(manifest version `2026.07.0`, 자연키·pk 없음) — chrono·nodes·graph·releases 단일 소스.
  `manage.py seed --mode=replace|add`(replace=재구축, add=없는 것만·그래프/릴리스 원자). 앱별 fixture 폐지, `FIXTURE_DIRS=seed/`.
- **테스트**: 백엔드 `pytest` **59 passed**. 테스트 fixture 는 seed 파일(`01_chrono`·`02_nodes`)을 loaddata.
- **문서 코퍼스**: `docs/` 13주제 × 한/영 + README + app-architecture 한/영. 진입점 `docs/concept-map.md`.
- **원격**: `git@github.com:jikhanjung/cdGTS.git`, main 직접 커밋·push.

## 개념/구현 진척 한 줄 정리

> **개념 → 사례검증 → 스키마 v0 → 통합지도 → 앱 설계 → P01 → Phase 0~6 → 계산 커널 → 배포 인프라 → v0.1.2 운영배포** 완주.
> 미션 "사람이 clamp, 기계가 전파·정합·diff" 의 전파·정합·diff 골격이 실배포 환경에서 돎.

## 최근 작업 (2026-07-03 ~ 07-04)

- **개념/스키마**(devlog 001~013) — 개념 3 + 사례검증 3 + 스키마 v0 + 설계심화 + 통합지도 + HANDOFF/TODOs/README.
- **구현**(014~020, P01) — 환경 뼈대 + 앱 아키텍처 + Phase 1~6(chrono/nodes/graph/frontend/engine/releases).
- **계산 커널**(023·024) — engine pass-through → dispatch 프레임워크 + age-depth 커널(numpy/scipy).
- **배포**(021·022·025·026) — Docker/Dockerfile + 이미지 push + 0.1.1 dev/test 배포 + 배포/DB 분리(prod→test sync).
- **인프라**(027·028) — 원자적 스냅샷 sync + NAS 오프사이트 백업 + 04:00 cron.
- **UX/시드**(029·030) — 예제 그래프 3종 + 릴리스 diff UI(값/토폴로지).
- **릴리스**(031) — v0.1.2 운영서버(cdgts.paleobytes.info) 배포.

## 다음 작업

### 후속 (선택, 우선순위 대략순)

- [ ] **운영 배포 검증 기록** — 헬스체크·시드 확인 결과를 devlog 에 정리(현재 미기록).
- [ ] **브라우저 육안 검증** — 프론트 drag&drop·엣지·복원·결과뱃지·diff 뷰 실제 클릭 확인(헤드리스 미검증분).
- [ ] **계산 커널 확장** — age-depth 외 joint/베이지안 등 노드타입별 실제 커널(별도 워커·PyMC).
- [ ] **인증·소유권** — 현재 API AllowAny(dev). 로그인·그래프 소유·샌드박스 권한.
- [ ] **clamp 통합** — graph 의 clamp 노드 ↔ releases.Clamp(authored 거버넌스) 관계 정리.
- [ ] **PostGIS** — chrono.Locality lat/lon → PointField(공간 차원 착수 시).
- [ ] **narrate(GTS)** — BoundaryRecord.narrative 충실화(bake 의 짝).
- [ ] **retype diff 실데모** — Ediacaran/Cryogenian 경계 추가로 GSSA→GSSP retype 시나리오(030 메모).
- [ ] **미해결 열린 질문** — 각 설계 문서 말미. → `TODOs.md` §2.
- [ ] **리뷰(R01)** — 구현 코드 리뷰 회차(devlog R 시리즈).
