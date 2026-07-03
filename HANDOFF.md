# HANDOFF — Current Work Status

**Last updated**: 2026-07-03 (**브레인스토밍 → 코드 착수 + P01 계획 완주**. 개념 코퍼스 13주제(한/영 26파일) +
경계 게이트웨이 스키마 v0 위에, 앱 아키텍처 설계(docs/app-architecture 한/영) → **개발 계획 P01** →
**Phase 0~6 전부 구현**. 스택 확정: **Django 5.2.12 + SQLite(dev) + DRF 3.17 + React Flow(Vite)**. 5개 앱
[chrono·nodes·graph·engine·releases] + 프론트 노드 에디터. 백엔드 **pytest 40 passed**. 미션 재정의
"사람이 clamp, 기계가 전파·정합·diff"의 **전파(engine pass-through)·정합(coherence cert)·diff(releases 값/토폴로지)**
골격이 실제로 돎. devlog 001~020 + P01 + 커밋 다수 push.)

> 과거 작업 내역은 `devlog/` 에 모두 기록됨. 본 문서는 **현재 상태 + 다음 작업**만 유지.
> 개념 지도 `docs/concept-map.md` · 앱 설계 `docs/app-architecture.md` · 개발 계획 `devlog/*_P01_*` · backlog `TODOs.md`.

## 현재 상태

- **성격**: 브레인스토밍 저장소 → **실행 가능한 코드베이스로 전환**(개념 코퍼스는 `docs/` 에 그대로 유지).
- **스택**: Django **5.2.12**, dev DB **SQLite**(공간 기능 착수 시 PostGIS), **DRF 3.17.1**, 프론트 **React 18 +
  @xyflow/react 12 + Vite**(`frontend/`, dev 는 `/api` 프록시). venv `/home/jikhanjung/venv/cdGTS`.
- **앱 5개** (의존: chrono ◁ nodes ◁ graph ◁ engine ◁ releases):
  - `chrono` — 정본 registry(Unit 이중명명·Boundary·Lineage·Authority·Ratification·Locality). fixture 세 경계.
  - `nodes` — 타입 시스템(NodeType 12 + Port) + `Distribution` 값객체(충실도 L0–L5). fixture 12타입.
  - `graph` — DAG(Graph·NodeInstance·Edge·NodeGroup·Gateway) + DAG 불변식(clamp/joint-inference 로만 순환 절단)
    + DRF `GET/PUT /api/graphs/{id}` React Flow 왕복.
  - `engine` — pass-through 평가(EvalRun·NodeResult 콘텐츠해시 증분·CoherenceCertificate 스텁)
    + `POST /api/graphs/{id}/evaluate/`.
  - `releases` — ModelCandidate·Release(selection+clamps)·BoundaryRecord(bake)·Clamp + bake/diff API
    (`/api/releases/{id}/bake/`, `/diff/?a=&b=`).
- **프론트**: 팔레트(NodeType 구동) → 캔버스 drag&drop → 저장(PUT)/평가 + 결과 뱃지. `npm run build` 통과.
- **테스트**: 백엔드 `pytest` **40 passed**(pytest.ini). fixture: `initial_boundaries`(chrono), `initial_node_types`(nodes).
- **문서 코퍼스**: `docs/` 13주제 × 한/영 + README + **app-architecture 한/영**. 진입점 `docs/concept-map.md`.
- **원격**: `git@github.com:jikhanjung/cdGTS.git`, main 직접 커밋·push.

## 개념/구현 진척 한 줄 정리

> **개념 → 사례검증 → 스키마 v0 → 통합지도 → 앱 설계 → P01 계획 → Phase 0~6 구현** 완주.
> 스키마의 다형 두 축·clamp·provenance=역추적·게이트웨이2계층이 모두 모델/코드로 내려옴.

## 최근 작업 (2026-07-03)

- **개념/스키마**(devlog 001~012) — 개념 3 + 사례검증 3 + 스키마 v0 + 설계심화 6 + 통합지도.
- **문서/계획**(013·014·P01) — HANDOFF/TODOs/README + 환경 뼈대(Django) + **앱 아키텍처(app-architecture 한/영)**
  + 개발계획 P01.
- **구현**(015~020) — Phase 1 chrono / 2 nodes(+Distribution) / 3 graph(DAG+DRF) / 4 frontend(React Flow) /
  5 engine(pass-through+증분+cert) / 6 releases(bake+값/토폴로지 diff). 각 Phase = 모델+admin+fixture/테스트+검증.

## 다음 작업

### 착수 결정 — **완료** (TODOs §0 참고, 아래는 후속)

- 데이터 포맷: JSONField 임베드(Distribution 등) + fixture(JSON). 스키마 v0 → 코드 모델로 구현(승격은 자연 진행).

### 후속 (선택, 우선순위 대략순)

- [ ] **HANDOFF/TODOs 유지** — 본 갱신 반영 완료. 이후 Phase 후속마다 갱신.
- [ ] **무거운 계산 커널** — engine pass-through → 노드타입별 실제 age-depth/joint(numpy/scipy/PyMC, 별도 워커).
- [ ] **브라우저 육안 검증** — 프론트 drag&drop·엣지·복원·결과뱃지 실제 클릭 확인(헤드리스 미검증분).
- [ ] **프론트 releases/diff UI** — 릴리스 선택·bake·두 릴리스 diff 뷰.
- [ ] **인증·소유권** — 현재 API AllowAny(dev). 로그인·그래프 소유·샌드박스 권한.
- [ ] **clamp 통합** — graph 의 clamp 노드 ↔ releases.Clamp(authored 거버넌스) 관계 정리.
- [ ] **PostGIS** — chrono.Locality lat/lon → PointField(공간 차원 착수 시).
- [ ] **narrate(GTS)** — BoundaryRecord.narrative 충실화(bake 의 짝).
- [ ] **미해결 열린 질문** — 각 설계 문서 말미(최소 clamp 집합·lineage 형식·후보 큐레이션 등). → `TODOs.md` §2.
- [ ] **리뷰(R01)** — 구현 코드 리뷰 회차(devlog R 시리즈).
