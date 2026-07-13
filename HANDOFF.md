# HANDOFF — Current Work Status

**Last updated**: 2026-07-13. 운영 `cdgts.paleobytes.info` @ **0.1.52** 배포 완료 · 테스트 서버 **m710q**(tailscale serve → `127.0.0.1:8011`) @ **0.1.54**. 이미지 `honestjung/cdgts:0.1.35~0.1.55` dockerhub push 완료. ⚠️ **운영은 0.1.52** — 0.1.53~0.1.55 는 테스트 서버까지만 반영(운영 배포는 사용자 승인 후).
- **0.1.54~0.1.55** 공유 보정 노드 + 공분산 배선 L1 vertical slice([devlog 139](devlog/20260712_139_calibration-constant-covariance-slice.md) · 근거 [R04](devlog/20260711_R04_radiometric-provenance-depth.md)): R04("방사연대 provenance 를 어느 깊이까지"—결론 = 공유 보정 파라미터 한 프리미티브만 1급으로)를 노드·커널·데모로 착지. **`calibration-constant` NodeType**(data leaf; params distribution·kind·symbol; out `value`; 커널이 불확실성 전액을 자기 자신 ref=symbol 의 `shared_component` 로 자동 태깅=L4 joint 승격) + **소비자 배선**: `radiometric-uPb` 에 `calibration` 입력 포트, 커널이 보정 σ 를 (a) 자기 marginal budget 에 제곱합 + (b) shared_component 로 태깅. **값 불변 = 재계산 아닌 공분산 배선(L1)**. 캡스톤 데모(`seed_demo` demo-cov)를 매직 스트링 → **진짜 공유 노드**로 재구성: ²³⁸U 붕괴상수는 물리적으로 하나 → `decay-238U` **딱 한 노드**가 두 연대에 갈라짐(shared→Cov 1.96→L1b **pass**) vs 공유 의존을 모델에 기록 안 함(independent=노드 없음, 순진 독립→Cov 0→L1b **warn**). marginal 값·± 는 양쪽 동일, 차이는 provenance(노드+엣지)뿐. **pytest 174**(커널 단위 5케이스 신규). 프런트 변경·마이그레이션 없음(팔레트·포트·인스펙터 동적). **남은 것(L2)**: 상수 값 변경이 연대 **값**을 재계산하는 rescale(raw invariant/민감도 노드) — 유스케이스 대기.
- **0.1.53** Editor.jsx 분해 2차([devlog 138](devlog/20260711_138_editor-decompose-2.md)): 인스펙터 핸들러 훅 `useNodeInspectorHandlers.js` 추출(Editor 990→966줄) + e2e 상호작용 스모크 확장(auto-eval 2500·그룹 렌더, **5/5**). graph-actions/selection 훅은 core state 얽힘으로 leaky → 의도적 미추출(Editor 분해 종결). 프론트 전용. **운영 0.1.52 배포 함정 대응**: compose 볼륨을 파일→디렉터리 바인드로 바꾼 뒤 prod `.env` 의 `DATABASE_PATH` 가 `/app/hostdb/db.sqlite3` 로 안 바뀌면 컨테이너가 이미지 내부 빈 DB 로 폴백 → `deploy.sh` 에 **`[5/5] DB 바인딩 검증 게이트`** 추가(636779b, 실데이터는 호스트에 안전했음).
- **0.1.52** Editor.jsx 분해 1차([devlog 137](devlog/20260711_137_editor-decompose.md)): 순수 뷰 레이어 `graphView.js`(apiToRF/rfToApi/buildView) + 컨텍스트 메뉴 `EditorMenu.jsx` 추출, Editor.jsx **1252→990줄**. 프론트 전용, 브라우저 스모크 3/3 통과. **Tier 2 스모크 스캐폴딩**(devlog 136, `frontend/e2e/`, Playwright·비블로킹)도 이 세션 산출.
- **0.1.51** clamp 축소([devlog 135](devlog/20260711_135_clamp-scopedown.md) · 근거 [cycles §12](docs/cycles.md#12-재검토-노트-2026-07--clamp는-별도-개념으로-필요한가)): clamp를 별도 개념에서 제거하고 **authored leaf로 수렴**. GSSA pin 2개→`published-age`(값 동일 2500 Ma), `pin`/`range`/`freeze-version` NodeType 제거(19→16, `order` 유지), cycle-breaker=joint-inference 전용, `releases.Clamp`/reconcile은 **DEMO-ONLY 격리**. pytest 165. ⚠️ **seed 변경 → 배포 시 `seed --mode=replace`**(테스트 반영 완료).
- **0.1.48** 읽기전용 그룹 드릴인([devlog 132](devlog/20260711_132_readonly-group-drillin.md), 프론트 전용).
- **0.1.49** 레퍼런스 후속([devlog 133](devlog/20260711_133_reference-followups.md)): 노드 얼굴 DOI 링크 · **Crossref 자동 메타데이터**(`references/crossref.py` + `GET /api/references/crossref/`, 로그인 필요) · narrate 응답에 bibliography. ⚠️ Crossref 는 컨테이너 외부망(api.crossref.org) 필요.
- **0.1.50** Tier-1 CI 플로우 시나리오 테스트([devlog 134](devlog/20260711_134_ci-flow-scenario-test.md), `test_ci_flow.py`, 실제 세션+CSRF) + **gateway-wipe 버그 수정**: 그래프 PUT 저장이 `Gateway.node` CASCADE 로 boundary gateway 를 지우던 것을 node key 재링크로 보존(편집→bake/propose 실동작 변경). pytest **166**.
- **0.1.48~0.1.52 운영 반영 완료 + 재시드 완료**(`seed --mode=replace`). gateway-wipe 잠복 버그 닫힘, clamp 축소(pin/range/freeze-version NodeType 제거·GSSA=`published-age` leaf)·P07 realistic 모델 모두 운영 반영됨.

**P07 — Base of Cambrian realistic model**([devlog 131](devlog/20260710_131_p07-base-cambrian-realistic-model.md) · [계획 P07](devlog/20260710_P07_base-cambrian-provenance-slice.md)): provenance vertical slice 를 실제 base-of-Cambrian 추론 구조로 구현.
- **노드 타입**: `section`(data — locality, h1/h2/h3 로 horizon emit, **cite 대상** = 섹션 레벨 provenance) · `horizon`(data — `depth`(섹션 base 기준)+`datum`, age 없는 undated horizon = 보간 target) · `radiometric-uPb`·`biostratigraphic` 에 `section` 입력 포트. `reference` = 유일 인용 노드 + DOI 레지스트리(`seed/02b_references.json`: Brasier94·Bowring07·Grotzinger95·Bowring93).
- **추론 구조**: 3 dated 섹션(Oman·Namibia·Siberia) 각 2 U-Pb ash bed 가 δ13C BACE horizon 을 bracket → `age-depth-model` interpolate(섹션별 경계 연대) → `cross-section-correlation` 종합 → Fortune Head **T. pedum FAD**(biostratigraphic, 연대 없음 = **경계 정의**) 로 `calibration-transfer`(reference=dated 연대, target=FAD; "정의는 FAD·연대는 δ13C 로 딴 데서") → **base of Cambrian = 538.82351 Ma**. 커널: `age-depth-model` 이 depth-만 있는 입력(boundary horizon)을 보간 target 으로 읽음(`target_depth` param 폴백).
- **그룹·example④**: 3 dated 섹션 evidence 18 노드 → NodeGroup "Base Cambrian · δ13C-dated sections" 하나. **realistic 모델을 example④(전 ICC 조립 그래프)에도 반영** — 옛 flat(global-age-model) 제거, `calib-transfer → bnd-base-cambrian.age`, 섹션 그룹 동일 적용(279 노드). 각 섹션 논문 cite → bibliography 4건 전파.
- 예제③(example-cambrian-base) **23 노드** · 예제④(example-icc-partial) **279 노드**. **pytest 159 passed.**

**배경(0.1.35~0.1.46)**: **레퍼런스 노드 + bake→bibliography**(devlog 127·128) 위에 P07 을 쌓음. 이전 P04(불변 Bake·Vault) · P05(멀티유저 CI) · P06(Science Engine: 공분산 백본·정합성 게이트 L1/L2·clamp reconcile) · P06.4a(비동기 워커) 는 그대로. **다음: R04 L2(상수 변경→연대 값 rescale 커널) · P06.4b(PyMC joint) · 아크 A(L2/L3) · 0.1.53~0.1.55 운영 배포(승인 후).** (P07 운영 반영·devlog·clamp 통합→축소·Editor 분해 1·2차·Tier1/2 테스트·R04 L1 공분산 배선은 완료.)

> 과거 작업 내역은 `devlog/` 에 모두 기록됨. 본 문서는 **현재 상태 + 다음 작업**만 유지.
> 개념 지도 `docs/concept-map.md` · 앱 설계 `docs/app-architecture.md` · 개발 계획 `devlog/*_P01_*` · backlog `TODOs.md`.

## 현재 상태

- **성격**: 브레인스토밍 저장소 → **실행 가능한 코드베이스 + 실배포**(개념 코퍼스는 `docs/` 에 그대로 유지).
- **스택**: Django **5.2.12**, DB **SQLite**(공간 기능 착수 시 PostGIS), **DRF 3.17.1**, 프론트 **React 18 +
  @xyflow/react 12 + Vite**(`frontend/`, dev 는 `/api` 프록시). venv `/home/jikhanjung/venv/cdGTS`.
- **앱 7개** (의존: chrono ◁ nodes ◁ graph ◁ engine ◁ releases · accounts · references):
  - `chrono` — 정본 registry(Unit 이중명명·Boundary·Lineage·Authority·Ratification·Locality).
    ICS chart.ttl 기반, **Subperiod(아계) rank 포함**(Carboniferous Mississippian/Pennsylvanian).
  - `nodes` — 타입 시스템(NodeType + Port) + `Distribution` 값객체(충실도 L0–L5). `published-age`(공표값 leaf) ·
    **`calibration-constant`**(공유 보정 파라미터 leaf: 붕괴상수·monitor·tracer; 커널이 σ 를 shared_component 로 자동 태깅 → 공분산 백본) 포함.
  - `graph` — DAG(Graph·NodeInstance·Edge·NodeGroup·Gateway) + DAG 불변식 + DRF React Flow 왕복.
    **경계·구간 이중성 모델**(`NodeInstance.nature`=generic|boundary · `NodeGroup.kind`=container|unit·`unit`·
    `lower`/`upper` 경계 노드 FK · `Edge.kind`=data|order). **노드그룹 = 컨테이너+접기+드릴인, N단 중첩**(parent
    self-FK, 엔진은 평탄). **order 제약 = order edge**(younger→older 세로 포트, 두 경계 선후 검사).
  - `engine` — 평가(EvalRun·NodeResult 콘텐츠해시 증분·CoherenceCertificate) + 계산 커널(numpy/scipy,
    age-depth 선형보간+spline MC). **정합성 게이트: L1 = authored order edge 체인(sparse) · L2 = 게이트웨이가
    덮는 전 유닛 duration>0 자동검사**(영-길이 유닛 검출, rank 별 타일링). **merge 노드 = geometry/composition
    타일링**(구간 조립: age→period→era→chart).
  - `releases` — ModelCandidate·Release·BoundaryRecord·Clamp + bake/diff API.
    **공표 ICC 릴리스 `ICS-2024/12`**(Epoch/Age 까지 값 정식화) + `GET /api/releases/{id}/icc-chart/`.
    **narrate**: `BoundaryRecord.narrative` 를 구조화 필드에서 결정적 템플릿 렌더(LLM 창작 없음).
    **P04/P05**: `Release.kind`(published/bake/transient)·`owner`·`source_graph`(불변 Bake 아티팩트) ·
    `snapshot_graph` · **`Proposal`**(propose/ratify/reject = CI) · `verify_graph`/`publish_graph`.
  - `accounts` — **`Membership`**(User↔Authority·role) + 개인 fork Authority 시그널 + 세션 인증
    `/api/auth/{whoami,login,logout}` + 중앙 **`can_ratify`**(P05.1·.4).
  - `references` — **`Reference`**(DOI 레지스트리: slug·doi·title·authors·year·kind, `link`). 그래프의
    `reference` NodeType 이 `cite` 엣지(비-데이터)로 데이터/모델 노드를 인용 → provenance 가 그래프 1급 시민.
    `GET /api/graphs/{id}/references/`(bibliography+citations = bake→참고문헌 seam). (devlog 127)
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
- **프론트 — Vault 허브 + Proposals**(P04·P05; nav = Editor·**Vault**·**Proposals** + LoginBar): ICC 테이블·**차트**·서술·
  릴리스 Diff 를 **Vault**(Release 선택 → 표현 토글)로 통합. **Proposals** = CI 리뷰(제안 목록 + verify diff + ratify/reject).
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
  - **운영서버** `cdgts.paleobytes.info` @ **0.1.52**(nginx + certbot). 개발/테스트 `127.0.0.1:8011` @ **0.1.54**.
    테스트 DB(prod 미러)에 P05 검증용 계정 세팅: `admin`(staff·ICS chair)·`demo`(비-staff·ICS chair·개인 fork).
  - deploy-prod.sh / deploy-dev.sh 분리, 스왑 중 nginx maintenance. DB 분리 + prod→test sync.
    이 호스트(m710q)는 **빌드 호스트이자 테스트 서버** — deploy-dev.sh 로 스냅샷 없이 즉시 스왑.
  - **백업**: 원자적 스냅샷(WAL torn-copy 방지) + NAS 오프사이트 + 04:00 cron.
  - ⚠️ **시드 데이터(레이아웃 포함) 변경 릴리스는 `seed --mode=replace` 재시드 필요**(add 는 그래프 원자 skip).
- **초기 데이터(seed)**: 통합 `seed/`(manifest `2026.07.0`, 자연키) — `01_chrono`~`04_releases` + **`05_icc_release`**.
  `manage.py seed --mode=replace|add`. 순환 자연키 FK(그룹↔노드)는 forward-ref 2패스로 로드. `FIXTURE_DIRS=seed/`.
- **테스트**: 백엔드 `pytest` **174 passed**(L2 게이트·seed 회귀 + P04/P05 소유·CI·가시성 + calibration 커널 공분산 상속/비상속 포함). 테스트 fixture 는 seed 파일 loaddata.
- **문서 코퍼스**: `docs/` 14주제 × 한/영 + README + app-architecture + naming(태그라인·표기 규칙) +
  evaluation-order(의존 vs 연대순, order=사후 검사) + boundary-span-duality. 진입점 `docs/concept-map.md`.
  **clamp 축소([cycles §12](docs/cycles.md#12-재검토-노트-2026-07--clamp는-별도-개념으로-필요한가))를 문서 전반에 정합화** —
  concept-map(수렴점 #2·미션)·tier-category-model·app-architecture·tutorial-science-engine·boundary-gateway-schema
  + 개념 문서 5종(idea·distribution·topology-diff·coherence-gate·evaluation-order)에 반영. GSSA=authored `published-age` leaf ·
  clamp 카테고리=`order`만 · `releases.Clamp`=DEMO-ONLY 로 일관(한/영 동기화, 앵커 검증).
- **원격**: `git@github.com:jikhanjung/cdGTS.git`, main 직접 커밋·push.

## 개념/구현 진척 한 줄 정리

> **개념 → 스키마 v0 → 앱 설계 → Phase 0~6 → 계산 커널 → 배포 인프라 → ICC 전 계층 재구성(경계·구간 이중성) →
> 공표 릴리스 대비 Science CI 검증** 완주. 미션 "사람이 authored 노드(값=leaf·선후=order), 기계가 전파·정합·diff" 가 실배포 환경에서
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

### 다음 방향 — 계획 (R01 → P04 → P05)

- **[R01](devlog/20260707_R01_vision-implementation-review.md)** — 초기 비전 대비 구현 현황 리뷰. 뼈대·배관은
  놓임; 미착수 두 아크 = A(과학 엔진 심화)·C(멀티유저 CI). **사용자 선택 = C.**
- **[P04](devlog/20260707_P04_editor-bake-vault-restructure.md) ✅ 구현 완료 · 테스트(0.1.26) 배포** — Editor→Bake→**Vault**
  재구성. **P04.1**([102](devlog/20260707_102_p04-1-immutable-bake-artifact.md)) 불변 Release 아티팩트
  (`kind`·`source_graph`, `snapshot_graph`, `GeologicTimeScale.Release.YYYYMMDD.NN`). **P04.2**([103](devlog/20260707_103_p04-2-editor-bake-action.md))
  Editor `Bake…` 버튼·다이얼로그. **P04.3**([104](devlog/20260707_104_p04-3-vault-hub.md)) nav=Editor·Vault,
  4개 뷰를 Vault 허브로(Chart/Table/Narrative/Diff 토글, `embedReleaseId`). pytest 96·build OK.
  스키마 migration(releases 0004·0005)은 entrypoint `migrate`로 자동 적용(seed 무변경 → 재시드 불필요).
  테스트 서버 검증 완료(bake→Vault Chart/Table/Narrative). **운영 배포는 사용자 승인 후.**
- **[P05](devlog/20260707_P05_arc-c-multiuser-ci-platform.md)** — 아크 C: 멀티유저 CI. 결정 5개 확정, 인터벌
  스코프 권한 retrofit-ready. **진행 중(미배포)**:
  - **P05.1 ✅**([106](devlog/20260707_106_p05-1-auth-foundation.md)) — `accounts` 앱(Membership + 개인 fork
    Authority 시그널), 세션 인증, `/api/auth/{whoami,login,logout}`, DRF 기본 `IsAuthenticatedOrReadOnly`,
    프론트 LoginBar + CSRF.
  - **P05.2 ✅**([107](devlog/20260707_107_p05-2-ownership-visibility.md)) — Graph 소유/가시성(공개+시스템+내
    것; 남 샌드박스 404), 쓰기=owner, Release.owner + `<user>` 이름 세그먼트. 프론트 Save/Bake 게이팅·🔒배지.
  - **P05.3 ✅**([108](devlog/20260707_108_p05-3-fork.md)) — Fork 깊은 복제(`forked_from`), `POST fork/`,
    프론트 Fork 버튼.
  - **P05.4 ✅**([109](devlog/20260707_109_p05-4-propose-review-ratify.md)) — Proposal 모델 + propose/ratify/
    reject + `can_ratify`(중앙) + Proposals 리뷰 뷰(verify diff 재사용). **아크 C MVP 완성.**
  - **P05.5 ✅**([110](devlog/20260707_110_p05-5-sandbox-overrides.md)) — 샌드박스 오버라이드(baseline + 경계별
    경쟁 후보 교체·재bake·diff, Vault Overrides 모드). 아크 B seam.
  - **P05 전체 완료 · 테스트 0.1.32 배포·검증**. 흐름: 로그인 → fork → 편집 → (bake→Vault) / propose → review →
    **ratify**(새 baseline) · baseline **sandbox → override**. pytest **112**. 스키마 migration 5개(accounts.0001,
    releases.0006·0007·0008, graph.0008)는 entrypoint `migrate`로 자동 적용. **운영 배포는 사용자 승인 후**
    (관리자·ICS Authority·Membership 세팅 필요, 초대제).

### 후속 (선택, 우선순위 대략순)

- [x] **`engine._certify` 층서순 정합** — order 제약 체인(040·041) + L2 duration 게이트(047)로 해소.
- [x] **finer 경계 값 릴리스화** — 공표 ICC 릴리스 `ICS-2024/12`(044)로 Epoch/Age 까지 정식화.
- [x] **narrate(GTS)** — BoundaryRecord.narrative 결정적 템플릿 렌더(045).
- [ ] **L2/L3 확장** — L2 warn 임계(과소/과대 duration 의심) · L3 joint reconcile · 프론트 cert 뷰 L2 상세(047 이월).
- [ ] **계산 커널 확장** — age-depth 외 joint/베이지안 등 노드타입별 실제 커널(별도 워커·PyMC).
- [~] **인증·소유권** — 현재 API AllowAny(dev). 로그인·그래프 소유·샌드박스 권한. → **아크 C, [P05](devlog/20260707_P05_arc-c-multiuser-ci-platform.md) 계획**(P04 선행).
- [x] **clamp 통합 → 축소로 종결** — graph clamp ↔ releases.Clamp *통합*이 목표였으나 재검토 결과 **별도 개념 불필요**(authored leaf 수렴). graph clamp NodeType 제거·GSSA=leaf·`releases.Clamp` DEMO-ONLY 격리 + 문서 전반 정합화. [cycles §12](docs/cycles.md#12-재검토-노트-2026-07--clamp는-별도-개념으로-필요한가) · devlog 135.
- [ ] **PostGIS** — chrono.Locality lat/lon → PointField(공간 차원 착수 시).
- [ ] **retype diff 실데모** — Ediacaran/Cryogenian 경계 추가로 GSSA→GSSP retype 시나리오(030 메모).
- [ ] **미해결 열린 질문** — 각 설계 문서 말미. → `TODOs.md` §2.
- [x] **리뷰(R01)** — 비전 대비 구현 현황 리뷰 작성([devlog R01](devlog/20260707_R01_vision-implementation-review.md)). 코드 리뷰 회차는 후속(R02).
