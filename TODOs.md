# TODOs

cdGTS(**continuously deployed Geologic Time Scale**) 브레인스토밍의 작업 백로그.
개념 전체 지도는 [docs/concept-map.md](docs/concept-map.md), 현재 상태 헤드라인은 [HANDOFF.md](HANDOFF.md).

> **HANDOFF.md** 는 짧은 현재상태/다음작업 헤드라인,
> 본 문서는 **미해결 항목별 상세**(주로 각 설계 문서 말미의 열린 질문).
> `devlog/` 시리즈가 라운드별 변경 기록. 저장소 성격·작업 방식은 `CLAUDE.md`.

---

## 0. 착수 결정 — **완료** (브레인스토밍 → 코드)

> 결정·구현됨. 설계 [docs/app-architecture.md](docs/app-architecture.md), 계획 [devlog P01](devlog/20260703_P01_app-build-plan.md),
> 구현 [devlog 015~020](devlog/). 아래는 결정 내용.

- [x] **기술 스택** — **Django 5.2.12 + SQLite(dev) + DRF 3.17 + React Flow(Vite)**. fsis2026 패턴 재사용.
      무거운 계산은 여전히 별도 과학 스택(numpy/scipy/PyMC)으로 분리 예정(engine 후속).
- [x] **데이터 직렬화 포맷** — Django 모델 + **JSONField 임베드**(Distribution 충실도 L0–L5 등) + fixture(JSON).
      스키마 v0 를 코드 모델로 구현(별도 YAML/RDF 포맷 대신 DB + REST).
- [x] **범위 결정** — **pass-through 부터**("발표값+출처" 층). engine 이 값+provenance 전파·증분·정합성 게이트
      스텁까지. 실제 *계산*(베이지안·joint)은 노드타입별 후속 커널.
- [~] **스키마 v0 → v1 승격** — 코드 모델로 내려오며 사실상 구현. 형식 승격 문서는 보류(열린 질문은 §2 유지).

## 0b. 구현 후속 (Phase 0~6 이후)

> P01 완주 후 남은 것. HANDOFF "후속" 과 동기.

- [~] **무거운 계산 커널** — dispatch 프레임워크 + age-depth 커널(numpy/scipy) **구현**(devlog 023·024).
      joint/베이지안(PyMC)·별도 워커는 후속.
- [x] **프론트 releases/diff UI** — 릴리스 bake·두 릴리스 diff 뷰(값/토폴로지) **구현**(devlog 030).
- [x] **ICC 테이블 bake + 뷰**(devlog 036·037) — `bake_graph`(그래프 게이트웨이→경계 스냅샷) + ICC 테이블 뷰 +
      ICS chart.ttl 시드(Period 이상 공표값 데이터 노드 네트웍 / Epoch·Age registry). units 42·boundaries 175·`published-age` 타입.
- [~] **`engine._certify` 정합성 게이트** — L1 = **authored `order` 엣지 체인**(younger<older, 우선) +
      order 노드/게이트웨이 fallback, **L2 = duration>0 타일링** 실동작. 게이트웨이 나열순 fallback은 여전히
      스텁 → 연대순 정렬. **L1b(2σ 겹침 warn)·L2 warn 임계·L3(공분산 검증/reconcile) 미구현**.
- [ ] **order 강제(reconcile)** — 현재는 검사만. joint truncation → 상관 사후분포(L2 공분산·L3b). solver/사이클 필요.
- [x] **경계·구간 이중성 모델** — cell complex(nature·NodeGroup.kind/unit/lower/upper·Edge.kind=order),
      order 노드 → order 엣지, 예제 노드 수 반감. (docs/boundary-span-duality.md, migration graph.0005)
- [ ] **finer 경계 값 릴리스화** — Epoch/Age 공표값을 candidate/selection → 완전한 공표 ICC 릴리스(현재 registry note 만).
- [ ] **data 카테고리 내부 이질성** — 순수 관측(radiometric) vs 공표값 참조(published-age) provenance 깊이 차이 표기(tier-category-model §6).
- [x] **레퍼런스 노드** — `references` 앱(Reference DOI 레지스트리) + `reference` NodeType + `cite` 엣지(비-데이터) +
      그래프 참고문헌 API + 프론트(팔레트·cite 배선·인스펙터 DOI/인라인 추가). (devlog 127)
- [x] **bake→bibliography** — bake 시 게이트웨이 상류 cone 역추적으로 경계별 기여 레퍼런스 수집·`BoundaryRecord.references`
      스냅샷 + 릴리스/그래프 참고문헌 API(`by_boundary`) + Vault "References" 탭. (devlog 128)
- [ ] **레퍼런스 후속** — reference 노드 얼굴 DOI 직접 클릭 · 레지스트리 관리 뷰 · Crossref DOI 자동 메타데이터 ·
      narrate(GTS)에 참고문헌 자동 삽입.
- [ ] **브라우저 육안 검증** — 프론트 drag&drop·엣지·복원·결과뱃지·인스펙터·Vault·diff(헤드리스 미검증분).
      **특히 P05 흐름(세션 로그인·CSRF·fork·propose·ratify)은 브라우저에서만 완전 검증 가능 — 배포 후 필수.**
      부분 자동화: Tier1 백엔드 시나리오([devlog 134](devlog/20260711_134_ci-flow-scenario-test.md)) + Tier2 브라우저 스모크
      스캐폴딩([devlog 136](devlog/20260711_136_tier2-browser-smoke.md), boot/render/login).
- [~] **상호작용 e2e 스모크 확장**([devlog 138](devlog/20260711_138_editor-decompose-2.md)) — **auto-eval(2500 Ma)
      + 그룹 노드 렌더** 추가(5/5). ⚠️ **드릴인(더블클릭)·bake/propose·컨텍스트 메뉴는 미커버** — 드릴인은 React
      Flow `onNodeDoubleClick` 이 Playwright 합성 이벤트로 안 깨어나 자동화 보류(수동 검증), bake/propose 는 인증·변경
      필요(Tier1 백엔드가 커버). 후속: 드릴인 자동화 우회법 or 다이얼로그 컴포넌트 분리 시 스모크.
- [x] **Editor.jsx 분해 (1·2차) → 종결**([devlog 137](devlog/20260711_137_editor-decompose.md)·[138](devlog/20260711_138_editor-decompose-2.md))
      — `graphView.js`(순수 뷰)·`EditorMenu.jsx`(메뉴)·`useNodeInspectorHandlers.js`(인스펙터 핸들러) 추출, Editor
      1252→966줄(−23%). **남은 seam(selection·graph-actions 훅)은 core state 얽힘으로 leaky 재배치 → 의도적 미추출**
      (분해 종결). 더 쪼갤 여지는 저이득 프레젠테이션(bake/graph-info 다이얼로그)뿐.
- [x] **인증·소유권** — 세션 인증 + Graph/Release 소유·가시성·객체 권한 구현(P05.1·.2, devlog 106·107).
- [~] **clamp 통합 → 재검토(축소 결론)** — graph clamp ↔ releases.Clamp *통합*이 목표였으나, 사용 현황(실 clamp
      거의 0, 대부분 demo)과 개념 재검토 결과 **clamp는 별도 개념으로 불필요**하다는 결론. 하던 일이 전부
      **authored 노드(GSSA leaf) + order 엣지 + joint-inference 노드 + 버전 나선**으로 접힘. → 통합 대신 **축소**
      (graph clamp 노드 deprecate · releases.Clamp/reconcile demo 격리). 근거·정리안: [cycles.md §12](docs/cycles.md#12-재검토-노트-2026-07--clamp는-별도-개념으로-필요한가). 구현은 후속.
- [ ] **PostGIS** — chrono.Locality lat/lon → PointField(공간 차원).
- [ ] **narrate(GTS)** — BoundaryRecord.narrative 충실화.
- [x] **retype diff 실데모** — Cryogenian base GSSA→GSSP. `diff_releases` 에 **shape 축**(exact→분포, ±0→±nonzero) 추가 +
      `seed_demo` 의 `Demo.Cryogenian.GSSA/GSSP` 릴리스 쌍(Vault→Diff 에서 topology·value·shape 세 축). (devlog 125)

## 0c. 배포 / 운영 — **구축됨** (devlog 021·022·025~028·031)

> Docker 이미지 + dev/test·prod 배포 + DB 분리·sync·백업까지 실동작. 아래는 후속.

- [x] **Docker 배포** — 이미지 `honestjung/cdgts`(numpy/scipy), `build.sh` pytest→bump→build→push.
- [x] **운영/개발 분리 배포** — 운영 `cdgts.paleobytes.info` @ 0.1.3(nginx+certbot), 개발/테스트 @ 0.1.1.
- [x] **DB 분리 + 백업** — 배포/DB 분리, 원자적 스냅샷 sync, NAS 오프사이트 + 04:00 cron.
- [x] **초기 데이터(seed) 통합 + 재시드 도구** — `seed/`(자연키·버전 `2026.07.0`) + `manage.py seed --mode=replace|add` (devlog P02).
      앱별 fixture 폐지, 자연키로 pk 충돌 없이 add 가능. 로컬 검증 완료(replace/add 멱등/원자/dry-run/bake).
- [x] **운영 재시드 실행 + 검증**(devlog 033) — 0.1.3 배포 후 `seed --mode=replace`(deleted 87/inserted 96/bake 2).
      드리프트 3건 해소(radiometric 스키마·age-depth linear/spline·releases 2/records 5). self-FK ProtectedError 수정 포함.
- [x] **v0.1.4 배포 + ICC 재시드**(devlog 038) — ICC 테이블 bake + ICS chart.ttl 확장 시드. 운영 `seed --mode=replace`
      (add 는 `example-icc-partial` 그래프를 slug 단위로 원자 skip → 추가 노드 반영 안 됨 → replace 필수). migration graph.0002 자동 적용.
- [x] **P08 — 배포·데이터 계약 retrofit** ([계획 P08](devlog/20260713_P08_deploy-data-contract-retrofit.md) · [140](devlog/20260713_140_seed-replace-lane-boundary.md)~[144](devlog/20260713_144_p08-close-deploy-validation.md), 0.1.56~0.1.60 실배포 검증) —
      cross-project 배포·데이터 계약(`../devdocs/wiki/deploy-data-contract.md`)의 cdGTS 파일럿. 세 수명주기 분리
      (코드·시스템 시드·운영 데이터)를 배포 파이프라인에 강제:
  - [x] **seed 레인 경계**(P08.1, devlog 140) — `seed --mode=replace` 가 delete-all → **운영 데이터(owner-set 그래프·
        릴리스·Proposal) 보존 upsert**(자연키 멱등 · 시스템 그래프만 재생성). P05 운영 데이터 silent 삭제 footgun 해소.
        `references.Reference` 재replace 중복 INSERT 잠복 버그 동봉 수정.
  - [x] **매니페스트 + 델타 노트**(P08.2·.3, devlog 141) — `deploy/deploy.toml`(선언층) + 루트 `DEPLOY.md`(릴리스별 append-only 운영 델타).
  - [x] **동사 + /healthz**(P08.4·.5, devlog 142) — `/healthz`(버전+DB+행 수→200/503) · `preflight.sh`·`smoke.sh`·`rollback.sh`.
  - [x] **git-free + self-heal 배포**(P08.6, devlog 143) — host 파일을 이미지에서 추출(`_extract_and_deploy.sh`) +
        부트스트랩 자기 치유 → **운영 서버 repo 불필요**. 배포 = `deploy-{prod,dev}.sh X.Y.Z [--reseed]` 한 줄.
  - [x] **실배포 검증 + 워커 핫픽스**(devlog 144) — 0.1.57 smoke SSL(`X-Forwarded-Proto`)·`--reseed`, 0.1.60 워커
        배포 버그(`up -d cdgts`→`up -d` 전 서비스). **양 서버 @ 0.1.60(웹+워커).** 계약·DEPLOY.md·README·HANDOFF 문서 정합.
  - [ ] **후속** — maintenance 점검 페이지 **자동 nginx 토글**(파일은 배포되나 앞단 fallback 은 수동).

## 0d. 구현 현황 리뷰 (R01, 2026-07-07)

> 초기 비전 대비 전반 리뷰 — 상세 [devlog R01](devlog/20260707_R01_vision-implementation-review.md).
> 요약: **뼈대·배관은 놓임**(그래프 엔진·티어×카테고리·bake/narrate·증분평가·ICC 차트·정합성 L1/L2 —
> 실동작·배포). **가장 야심찬 두 축은 미착수**. 현재 = 단일 사용자 그래프 에디터 + 결정론적 파이프라인.

- **✅ 견고**: 노드 그래프 엔진, 티어×카테고리, 게이트웨이 3티어, 증분(content-hash) 평가, ICC bake/차트,
  narrate, Science CI(verify), 경계·구간 이중성(nature·kind·unit·lower/upper·order edge).
- **⚠️ 구조는 있으나 얕음**: 경쟁 모델(데이터 구조만), clamp 거버넌스(releases.Clamp 미소비),
  topology diff(lineage 미소비), Distribution L4/L5, 정합성 L3, joint-inference(역분산 가중합 수준).
- **❌ 미착수(비전 핵심 아크 2개)**: 확률적·베이지안 결합 추정 엔진 / 멀티유저·샌드박스 플랫폼.

### 다음 전략 방향 — 둘 중 하나 선택 후 P 시리즈로

- [ ] **아크 A — 과학 엔진 심화**: 진짜 joint/베이지안 커널(PyMC+워커) · Distribution L4/L5(공분산) ·
      정합성 L1b/L2 warn/L3. 차별점의 원천, 도메인 난이도 높음. (→ §2.2·2.6·1, §0b 계산 커널)
- [~] **아크 C — 멀티유저 "CI for science" 플랫폼**: **구현 완료(미배포)**.
      **[P04](devlog/20260707_P04_editor-bake-vault-restructure.md) ✅** Editor→Bake→**Vault**(불변 Release 1급,
      devlog 102~104, 테스트 0.1.26). **[P05](devlog/20260707_P05_arc-c-multiuser-ci-platform.md) ✅** — .1 인증
      (세션·Membership)·.2 소유/가시성·.3 fork·.4 propose/review/ratify·.5 샌드박스 오버라이드(devlog 106~110).
      로그인→fork→편집→(bake→Vault)/propose→review→ratify · baseline sandbox→override 작동.
      **남음**: 인터벌 스코프 권한(훅 준비됨), 배포(관리자·ICS Authority·Membership 세팅), 브라우저 검증.
- [ ] **(병행 가능) 아크 B — 거버넌스 성숙**: clamp 통합 · 경쟁 모델 선택 로직 · lineage topology diff. (→ §2.3·2.4·2.5)

## 1. 추가 사례 검증

> 세 유형(GSSP 국소보간 / GSSA 결정 / GSSP 섹션간상관)은 완료. 모델을 더 조일 사례.

- [~] **Cryogenian base GSSA→GSSP 전환** — 진행 중인 실제 재배선. **토폴로지 diff·값 모양 변화(스칼라→분포)**
      는 릴리스 diff 데모로 실연(shape 축 + `seed_demo` GSSA/GSSP 쌍, devlog 125). 남음: **clamp 제거를 그래프
      노드로** 그리는 provenance 서브그래프(marker/stratotype) 실연. (topology-diff §6)
- [ ] **joint·공분산 워크드 예시** — 두 경계가 tracer/붕괴상수를 공유해 지속시간 오차가 상관되는 구체 사례
      (coherence-gate L2 / distribution C 를 실데이터로).
- [ ] **middle-type 변형** — correlation tier (b) 가 다봉(경쟁 상관가설)으로 나타나는 사례.

## 2. 설계 문서별 미해결 열린 질문

### 2.1 전역 vs 경계별 버전 ([versioning-global-vs-per-boundary](docs/versioning-global-vs-per-boundary.md) §5)

- [ ] 전역 릴리스 = **복사 스냅샷** vs **매니페스트/락파일** — 확정.
- [ ] 정합성 게이트를 **검증(validation)** 수준 vs **공동추정(joint inference)** 까지.
- [ ] **단조 순서 불변식** — hard constraint vs lint/경고 (대표 경계엔 드물지만 세밀 구간엔 필요).
- [ ] **공유 노드 재보정** 같은 전역 이벤트가 다수 경계 버전을 한꺼번에 bump 하는 것의 표기.
- [ ] **토폴로지/집합 변경**(경계 추가·삭제·개명) 버전의 위치 (경계 밖 전역 층?).
- [x] **샌드박스 오버라이드**(베이스라인 + 델타) 스키마 표현 — `Release.base` + 경계별 `Selection` 오버라이드로 구현(P05.5, devlog 110).
- [ ] **인용**이 (경계 버전 + 전역 릴리스)를 함께 가리키는 최소 형식.
- [ ] **상관된 불확실성**(공유 오차 구조)의 릴리스 보존.

### 2.2 정합성 게이트 ([coherence-gate](docs/coherence-gate.md) §6)

- [ ] **L3b 재조정값**("릴리스 보정값")을 레코드값과 나란히 인용·표기하는 법. (→ 잠정: authored clamp 로, cycles §6)
- [ ] **L1b 겹침 WARN** 을 릴리스가 차단 vs 통과시키는 정책 (대표 경계 vs 세밀 구간 차등).
- [ ] **공분산 추적 범위** — 전체 공분산 행렬 vs 공유성분 태그만.
- [ ] **게이트 버전**(`gate_version`) — 검사 규칙이 바뀌면 과거 인증서의 지위.

### 2.3 경쟁 모델 ([competing-models](docs/competing-models.md) §7)

- [ ] **후보 큐레이션 문지기** — 샌드박스 후보 중 ICC 가 고려하는 후보 집합에 무엇이 드나.
- [ ] **모델 정체성/버전** — 입력이 바뀐 재실행은 새 후보 vs 같은 후보의 새 버전.
- [ ] **포락 가중치** — 모델 평균 시 가중치를 누가/어떻게.
- [ ] **조합 폭발** — 경계 N × 후보 M × 정합 제약 관리.
- [ ] **전역 후보 부분 채택** 시 정합성 유지.

### 2.4 순환 / clamp ([cycles](docs/cycles.md) §10)

- [ ] **최소 clamp 집합** — 모든 사이클을 끊는 최소 clamp 자동 제안 + 사람 승인.
- [ ] **버전 나선 수렴 판정·감쇠(damping)** 기준.
- [ ] **동시추정 노드 스코프 분할** — 전부 결합 불가 → 분할이 들여오는 근사.
- [ ] **clamp 간 충돌** — 두 subcommission clamp 가 경계에서 모순 시 중재.

### 2.5 토폴로지 diff ([topology-diff](docs/topology-diff.md) §9)

- [ ] **식별자 영속성 & lineage 형식** — 안정 id 부여 주체·영속성, split/merge lineage 기록 형식.
- [ ] **토폴로지 입도** — 줌 레벨에 따라 값 변화이기도 토폴로지 변화이기도 → 어느 층에서 diff 정의.
- [ ] **대규모 재배선 정렬** — id 우선 + 휴리스틱 + 미정렬 플래그.
- [ ] **selection diff vs 구조 diff** — ModelCandidate A→B 교체 분류.

### 2.6 분포 표현 ([distribution-representation](docs/distribution-representation.md) §9)

- [ ] **모델 간 다봉** — 분포에 담을지 selection 층으로 뺄지 (내부오차=분포 / 모델간=포락, 분리가 깔끔).
- [ ] **사후 샘플 저장·버전** — 무거움 → 참조, 임베드 금지.
- [ ] **레거시 `± 2σ`뿐 데이터**의 우아한 저하(L1).
- [ ] **희소 공분산 재구성 정확도** — 공유성분 태그만으로 충분한가.
- [ ] **canonical rung 확정** — 경계 정본 L2/L3 + joint(L4) 릴리스 층 (잠정 방향, 미확정).

### 2.7 idea 원래 열린 질문 ([idea](docs/idea.md) §7 — 일부는 clamp/provenance 로 재프레이밍됨)

- [ ] **권위 vs 실험 경계** — sandbox 결과와 공식 ICC 구분, 개인 fork 시대표 허용 범위.
- [~] **기존 포맷 정합** — ICS 공식 chart.ttl(GeoSciML/timescale RDF) 파싱해 경계 시드에 사용(devlog 037).
      Macrostrat / 완전 GeoSciML·CGI 왕복은 후속. (§1 사례와 함께)
- [ ] **버전 전략 구체화** — git 태그 · 시맨틱 버저닝 · 자동 검증(CI) 매핑.

## 3. 유지 관리

- [ ] **한/영 쌍 동기화** — 새 문서·수정 시 KR/EN 함께 (memory `bilingual-docs-convention`).
- [ ] **devlog 시리즈** 단조증가 — `NNN`(완료, 현재 144)·`PNN`(Plan, 현재 P08)·`RNN`(Review, 현재 R04).
