# HANDOFF — Current Work Status

**Last updated**: 2026-07-07. 운영 **cdgts.paleobytes.info @ 0.1.25** — 0.1.22~0.1.25 UI/UX 다듬기 일괄
릴리스(이미지 빌드·푸시 완료, 운영 배포는 사용자 진행). 개발/테스트 `127.0.0.1:8011`.
백엔드 **pytest 91 passed**. devlog 001~101 push.

> 과거 작업 내역은 `devlog/` 에 모두 기록됨. 본 문서는 **현재 상태 + 다음 작업**만 유지.
> 개념 지도 `docs/concept-map.md` · 앱 설계 `docs/app-architecture.md` · 개발 계획 `devlog/*_P01_*` · backlog `TODOs.md`.

## 현재 상태

- **성격**: 브레인스토밍 저장소 → **실행 가능한 코드베이스 + 실배포**(개념 코퍼스는 `docs/` 에 그대로 유지).
- **스택**: Django **5.2.12**, DB **SQLite**(공간 기능 착수 시 PostGIS), **DRF 3.17.1**, 프론트 **React 18 +
  @xyflow/react 12 + Vite**(`frontend/`, dev 는 `/api` 프록시). venv `/home/jikhanjung/venv/cdGTS`.
- **앱 5개** (의존: chrono ◁ nodes ◁ graph ◁ engine ◁ releases):
  - `chrono` — 정본 registry(Unit 이중명명·Boundary·Lineage·Authority·Ratification·Locality).
    ICS chart.ttl 기반, **Subperiod(아계) rank 포함**(Carboniferous Mississippian/Pennsylvanian).
  - `nodes` — 타입 시스템(NodeType + Port) + `Distribution` 값객체(충실도 L0–L5). `published-age`(공표값 leaf) 포함.
  - `graph` — DAG(Graph·NodeInstance·Edge·NodeGroup·Gateway) + DAG 불변식 + DRF React Flow 왕복.
    **경계·구간 이중성 모델**(`NodeInstance.nature`=generic|boundary · `NodeGroup.kind`=container|unit·`unit`·
    `lower`/`upper` 경계 노드 FK · `Edge.kind`=data|order). **노드그룹 = 컨테이너+접기+드릴인, N단 중첩**(parent
    self-FK, 엔진은 평탄). **order 제약 = order edge**(younger→older 세로 포트, 두 경계 선후 검사).
  - `engine` — 평가(EvalRun·NodeResult 콘텐츠해시 증분·CoherenceCertificate) + 계산 커널(numpy/scipy,
    age-depth 선형보간+spline MC). **정합성 게이트: L1 = authored order edge 체인(sparse) · L2 = 게이트웨이가
    덮는 전 유닛 duration>0 자동검사**(영-길이 유닛 검출, rank 별 타일링). **merge 노드 = geometry/composition
    타일링**(구간 조립: age→period→era→chart).
  - `releases` — ModelCandidate·Release·BoundaryRecord·Clamp + bake/diff/`bake_graph` API.
    **공표 ICC 릴리스 `ICS-2024/12`**(Epoch/Age 까지 값 정식화) + `GET /api/releases/{id}/icc-chart/`.
    **narrate**: `BoundaryRecord.narrative` 를 구조화 필드에서 결정적 템플릿 렌더(LLM 창작 없음).
- **프론트 — 노드 에디터(`Editor.jsx`)**: 팔레트/캔버스/인스펙터. 주요 UX:
  - 헤더에 **버전 배지**(`v0.1.x`), **auto-evaluate**(로드/저장 시 자동) + **saved/unsaved 표시**(● Unsaved / ✓ Saved).
  - **boundary 노드**: 컴팩트(반높이 ◈), 입력 age(또는 공표값)를 노드 얼굴·인스펙터에 표시, Phanerozoic 경계는
    "Base of <Period>" 명명. 팔레트 boundary/published-age 드롭 시 `nature=boundary` 기본.
  - **선택 UX**: 모든 노드/그룹/합성(gio·bound) 노드에 **선택 테두리 링**, **Shift+클릭 추가 선택**,
    좌-드래그 러버밴드 + **가장자리 auto-pan**, 다중선택 시 **전체 바운딩 사각형 숨김**(개별 링만), 선택 노드
    위 우클릭도 그룹 생성 메뉴. 파생 노드 참조 안정화로 박스 밖 강제선택 버그 해소.
  - **인스펙터**: 데스크톱에서 **접기 토글**(Properties ◂/▸ · 패널 ✕), **노드 선택 시 자동 표시**.
  - **컨텍스트 메뉴**: 노드/엣지 **삭제**, 그룹 생성·병합·해제, parent 로 돌아가기. **엣지 선택·삭제**(order edge 포함).
  - **order edge**: younger→older 연결로 생성(점선 보라), 그룹 접힘 시 order 포트 항상 노출(삭제해도 재연결 가능).
  - **그룹/합성 노드 고정 폭**(collapsed group 200px · Group I/O 200px, 긴 라벨 ellipsis).
- **프론트 — ICC 뷰**: ICC 테이블 + **ICC 차트** + 릴리스 Diff 뷰.
  - **ICC 차트**: Eon~Age **5 컬럼 중첩**(**Subperiod 는 Epoch 컬럼에 병합** — Carboniferous 전용 컬럼 제거),
    경계 불확실성 ± 밴드·툴팁. **스케일 3종**: Log(최근 확대) · Linear(비례) · **Table(equal Age — 시간척도 무시,
    leaf 셀 균등 높이의 표 형식)**. **줌(viewBox scale) + 팬**(Ctrl/⌘+휠 커서 기준), 줌에 따라 라벨 폰트 조정
    (얇은 밴드도 확대 시 표시). **merge 노드 geometry 뷰**: 특정 column merge 의 부분 차트 조회.
  - **Science CI 버튼**: 그래프 편집 → 재bake → 공표 baseline 과 원클릭 diff(이동 경계·배선 변화 요약).
  - **모바일 대응**: 반응형 드로어 + 터치 팬 + 탭-투-추가/롱프레스 메뉴.
- **예제 그래프**: 3종 파이프라인(permian-triassic 3·cambrian-base 5·gssa-precambrian 1) + **`example-icc-partial`
  (예제④)** — 전 ICC 재구성: **261 노드 · 493 엣지(order 233) · 노드그룹 14**. period=노드그룹(span)·내부 age
  order edge 체인, merge 노드로 age→period→era→chart 조립.
- **배포/운영**:
  - Docker 이미지 `honestjung/cdgts`, `deploy/build.sh <ver>` 로 pytest→bump→build→push. 버전 `config/version.py`.
  - **운영서버** `cdgts.paleobytes.info` @ **0.1.25**(nginx + certbot). 개발/테스트 `127.0.0.1:8011`.
  - deploy-prod.sh / deploy-dev.sh 분리, 스왑 중 nginx maintenance. DB 분리 + prod→test sync.
    이 호스트(m710q)는 **빌드 호스트이자 테스트 서버** — deploy-dev.sh 로 스냅샷 없이 즉시 스왑.
  - **백업**: 원자적 스냅샷(WAL torn-copy 방지) + NAS 오프사이트 + 04:00 cron.
  - ⚠️ **시드 데이터(레이아웃 포함) 변경 릴리스는 `seed --mode=replace` 재시드 필요**(add 는 그래프 원자 skip).
- **초기 데이터(seed)**: 통합 `seed/`(manifest `2026.07.0`, 자연키) — `01_chrono`~`04_releases` + **`05_icc_release`**.
  `manage.py seed --mode=replace|add`. 순환 자연키 FK(그룹↔노드)는 forward-ref 2패스로 로드. `FIXTURE_DIRS=seed/`.
- **테스트**: 백엔드 `pytest` **91 passed**(L2 게이트·seed 회귀 포함). 테스트 fixture 는 seed 파일 loaddata.
- **문서 코퍼스**: `docs/` 14주제 × 한/영 + README + app-architecture + naming(태그라인·표기 규칙) +
  evaluation-order(의존 vs 연대순, order=사후 검사) + boundary-span-duality. 진입점 `docs/concept-map.md`.
- **원격**: `git@github.com:jikhanjung/cdGTS.git`, main 직접 커밋·push.

## 개념/구현 진척 한 줄 정리

> **개념 → 스키마 v0 → 앱 설계 → Phase 0~6 → 계산 커널 → 배포 인프라 → ICC 전 계층 재구성(경계·구간 이중성) →
> 공표 릴리스 대비 Science CI 검증** 완주. 미션 "사람이 clamp, 기계가 전파·정합·diff" 가 실배포 환경에서
> **authored order(L1) + 자동 duration(L2) + 원클릭 공표 diff** 로 돎.

## 최근 작업 (2026-07-06 ~ 07, devlog 078~101)

- **merge/geometry 모델**(079·080·081·P03) — merge 노드가 구간 geometry 를 타일링(age→period→era→chart),
  column merge 별 부분 차트, age-unit 재귀 세분. 레이아웃 정리(082, merges-on-top).
- **ICC 차트 확장**(083·085·101) — 줌(viewBox scale)+커서 기준 팬, 줌 대응 라벨 폰트(얇은 밴드 표시),
  **Table(equal-Age) 스케일 모드** 추가, **Subperiod 컬럼 제거**(Epoch 에 병합).
- **에디터 UX 시리즈**(084·086~098) — 그룹 내부 x 정렬·parent 복귀 버튼, order edge 생성/삭제/포트 영속,
  boundary age 표시 + "Base of X" 명명, auto-evaluate + saved/unsaved 표시, 노드/엣지 삭제 메뉴,
  선택 링(전 노드 타입)·Shift 다중선택·바운딩 사각형 숨김·선택 노드 우클릭 메뉴, auto-pan, 인스펙터
  접기/자동표시, merge 배지, 그룹·Group I/O 고정 폭.
- **선택 버그픽스**(097·099) — 다중선택 오버레이 우클릭 통과, 파생 노드 참조 안정화로 박스 밖 강제선택 해소.
- **seed**(100) — 예제 T. pedum FAD 노드를 Oman Ara Group 위로 재배치(양 그래프).
- **릴리스** — 0.1.19~0.1.21 순차 운영 배포 후, 0.1.22~0.1.25(UI/UX 다듬기)를 테스트 서버에서 마무리하고
  **0.1.25 로 일괄 릴리스**(이미지 빌드·푸시 완료). frontend 중심 변경이며 seed 변경(100)은 재시드로 반영.

## 진행 중 (WIP)

- **인터페이스(Group I/O) 노드 위치 영속** — 현재 드릴인별 프론트 세션 메모리(리로드/저장 시 초기화).
  영속 필요 시 NodeGroup 에 io 좌표 필드 추가(후속).

### 후속 (선택, 우선순위 대략순)

- [x] **`engine._certify` 층서순 정합** — order 제약 체인(040·041) + L2 duration 게이트(047)로 해소.
- [x] **finer 경계 값 릴리스화** — 공표 ICC 릴리스 `ICS-2024/12`(044)로 Epoch/Age 까지 정식화.
- [x] **narrate(GTS)** — BoundaryRecord.narrative 결정적 템플릿 렌더(045).
- [ ] **L2/L3 확장** — L2 warn 임계(과소/과대 duration 의심) · L3 joint reconcile · 프론트 cert 뷰 L2 상세(047 이월).
- [ ] **계산 커널 확장** — age-depth 외 joint/베이지안 등 노드타입별 실제 커널(별도 워커·PyMC).
- [ ] **인증·소유권** — 현재 API AllowAny(dev). 로그인·그래프 소유·샌드박스 권한.
- [ ] **clamp 통합** — order edge 로 활성화됨; 나머지 graph clamp ↔ releases.Clamp(authored 거버넌스) 관계 정리.
- [ ] **PostGIS** — chrono.Locality lat/lon → PointField(공간 차원 착수 시).
- [ ] **retype diff 실데모** — Ediacaran/Cryogenian 경계 추가로 GSSA→GSSP retype 시나리오(030 메모).
- [ ] **미해결 열린 질문** — 각 설계 문서 말미. → `TODOs.md` §2.
- [ ] **리뷰(R01)** — 구현 코드 리뷰 회차(devlog R 시리즈).
