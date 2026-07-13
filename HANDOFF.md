# HANDOFF — Current Work Status

**Last updated**: 2026-07-13. 운영 `cdgts.paleobytes.info`(dolfinid-2) @ **0.1.60** · 테스트 서버 **m710q**(tailscale serve → `127.0.0.1:8011`) @ **0.1.60**. 이미지 `honestjung/cdgts:0.1.35~0.1.60` dockerhub push 완료. 공개 `https://cdgts.paleobytes.info/healthz` = 0.1.60/node_types 17. **양 서버 cdgts + cdgts-worker 둘 다 가동**.
- **워커 배포 버그 수정(0.1.60)**([커밋]): `deploy.sh` 재기동이 `docker compose up -d cdgts`(웹만)라, prod 스냅샷 경로의 `down`(웹+워커 제거) 뒤 **워커(cdgts-worker, P06.4a 비동기 평가)가 계속 부재**했음(사용자가 예전에 "워커가 개발서버에만" 지적). `up -d`(전 서비스)로 수정 → rollback.sh 와 정합. prod 에 워커 즉시 기동 + 0.1.60 배포로 스냅샷 down/up 경로에서도 워커 유지 검증(cdgts+cdgts-worker 둘 다 0.1.60 Up, run_worker 폴링). dev 경로의 "워커 옛 이미지 잔존"도 함께 해소.
- **전체 릴리스 플로우 Claude 구동 검증(0.1.59)**: m710q 에서 `build.sh 0.1.59 --fast`(버전만) → `deploy-dev.sh 0.1.59`(테스트) → **`ssh dolfinid '/srv/cdGTS/deploy-prod.sh 0.1.59'`(prod 원격 배포)** → 공개 healthz 확인까지 한 세션에서 완주. prod 는 self-heal + repo-free 로 무개입. (prod 배포를 Claude 가 SSH 로 직접 수행한 첫 사례 — 사용자 지시.)
- **0.1.58 부트스트랩 self-heal — prod repo-free 확립**([커밋 14f1fd8]): `_extract_and_deploy.sh` 가 매 배포마다 부트스트랩 파일도 이미지에서 갱신(래퍼=exec 후 즉시 덮어쓰기 · 자기 자신=임시파일→원자 rename, 다음 배포부터). **prod·m710q 둘 다 self-heal 활성 확인**(`deploy-{prod,dev}.sh 0.1.58` 로그에 `self-heal *` 3줄). git-free 부트스트랩(repo 없이 `docker create`+`docker cp /app/deploy/host/{_extract_and_deploy,deploy-prod,deploy-dev}.sh`) 절차 DEPLOY.md 명시. **이제 prod 에 repo 불필요 — `~/projects/cdGTS` 삭제 가능.** 앞으로 릴리스 = (빌드호스트)`build.sh X.Y.Z` → (prod SSH)`deploy-prod.sh X.Y.Z [--reseed]`. SSH 별칭 `dolfinid`(키 인증, m710q→prod 붙음).
- **0.1.56 운영·테스트 배포 완료** — P08.1~P08.6(배포·데이터 계약 retrofit) 전량. m710q·dolfinid-2 모두 git-free `deploy-{dev,prod}.sh 0.1.56` + `seed --mode=replace`(운영 데이터 보존 upsert 실동작: prod `inserted 1053·updated 797`)·`seed_demo` 재시드. `/healthz` node_types 17 확인.
- **0.1.57 운영 배포 완료 — prod 실배포에서 나온 2 갭 수정**([커밋 9f6f620]): ⓐ **smoke SSL false-fail** — prod `SECURE_SSL_REDIRECT=True` 라 평문 HTTP `/healthz` 가 301 → curl(-L 없음) 빈 본문 → status!=ok 오판. `smoke.sh`·deploy 대기 루프에 `X-Forwarded-Proto: https`(SECURE_PROXY_SSL_HEADER) 헤더. ⓑ **deploy 에 seed 단계 부재** — 시드 변경/빈 DB 최초 배포 시 smoke 가 재시드 전 실패. `deploy-{prod,dev}.sh X.Y.Z --reseed` → migrate 후 smoke 전 `seed --mode=replace`+`seed_demo`. **dolfinid-2 @ 0.1.57 배포·재시드·smoke green 검증 완료**(`deploy-prod.sh 0.1.57 --reseed`: 스냅샷→스왑→[5b] reseed inserted 1053·updated 797→[6/6] smoke ok/17). P08 배포 파이프라인 전 구간 실증. **m710q 도 `deploy-dev.sh 0.1.57` 로 맞춤(smoke green)** — prod·test 0.1.57 일치.
- **P08.1 (배포·데이터 계약 retrofit — seed 레인 경계)**([계획 P08](devlog/20260713_P08_deploy-data-contract-retrofit.md) · [devlog 140](devlog/20260713_140_seed-replace-lane-boundary.md)): cross-project 배포·데이터 계약(`../devdocs/wiki/deploy-data-contract.md`)의 핵심 불변식 — *"`seed --mode=replace` 는 시스템 정의 데이터만 건드린다"* — 을 seed 명령에 세움. 기존 `_delete_all()` 이 owner 무시하고 `graph.Graph`·`releases.Release` 를 `all().delete()` → P05 운영 데이터(학자 fork·bake·Proposal) silent 삭제 또는 PROTECT 실패였던 **잠복 footgun** 해소. 전략: **레지스트리 자연키 upsert(pk 보존 → 운영 PROTECT/CASCADE 참조 안전) + 시스템 그래프(owner NULL)만 삭제·재생성 + 파생물 시스템 스코프 재-bake + 스코프 prune**. `references.Reference` 누락(재replace 중복 INSERT) 잠복 버그 동봉 수정. pytest **175**(운영 데이터 생존 회귀 신규) · 운영 미러 dry-run(inserted 1056·updated 794·removed 1893, 무예외). 마이그레이션 없음(관리 명령만). **미배포**(코드 변경, 다음 릴리스에 포함).
- **P08.2·P08.3 (매니페스트 + 운영 델타 노트)**([devlog 141](devlog/20260713_141_deploy-manifest-and-notes.md)): `deploy/deploy.toml`(선언층 — image·db_path·has_seed·services·[verbs]·[targets.prod=dolfinid-2/test=m710q]) + 루트 `DEPLOY.md`(릴리스별 append-only 운영 델타 노트 — 상시 불변식[재시드·DATABASE_PATH 바인딩·migrate·Crossref] + 0.1.3~P08.1 소급, 🔴/🟡/🟢). 문서·설정만(코드 무관).
- **P08.4·P08.5 (동사 + /healthz)**([devlog 142](devlog/20260713_142_deploy-verbs-and-healthz.md)): `config/health.py` **`/healthz`**(버전+DB+핵심 행 수 → 200/503; 시스템 시드 부재=503; 무인증) + 동사 스크립트 `deploy/preflight.sh`(위험 표면 diff + seed 냄새 lint + DEPLOY.md)·`deploy/host/smoke.sh`(healthz 200+버전 일치+행 수)·`deploy/host/rollback.sh`(이전 이미지+pre_deploy 스냅샷). `deploy.sh` [6/6] smoke 자동, `deploy.toml health_probe`→/healthz. pytest +3(healthz).
- **P08.6 (git-free 배포)**([devlog 143](devlog/20260713_143_git-free-deploy.md)): 운영 서버 git pull 의존 제거. host 운영 파일이 이미 `COPY . .` 로 이미지 `/app/deploy/host/*` 에 실려 있음 → `deploy-{prod,dev}.sh` 를 git-free 부트스트랩으로 재작성(공유 `_extract_and_deploy.sh` 가 `docker cp` 로 이미지에서 compose·deploy.sh·smoke·rollback·maintenance 추출 → deploy.sh 위임). 호스트 상시 파일=`.env`+래퍼2+`_extract_and_deploy.sh`. `sync_to_srv.sh`=부트스트랩 전용. **P08 전체 완료**(레인 경계·매니페스트·동사·헬스·git-free). ⚠️ **0.1.56 1회 부트스트랩**: 호스트 래퍼가 옛 2줄 버전이라 이번만 `sync_to_srv.sh` 1회 필요(DEPLOY.md 명시). **다음: 0.1.56 빌드·실배포 검증**(seed replace 운영 데이터 보존·[6/6] smoke·git-free 추출 최종 확인).
- **0.1.54~0.1.55** 공유 보정 노드 + 공분산 배선 L1 vertical slice([devlog 139](devlog/20260712_139_calibration-constant-covariance-slice.md) · 근거 [R04](devlog/20260711_R04_radiometric-provenance-depth.md)): R04("방사연대 provenance 를 어느 깊이까지"—결론 = 공유 보정 파라미터 한 프리미티브만 1급으로)를 노드·커널·데모로 착지. **`calibration-constant` NodeType**(data leaf; params distribution·kind·symbol; out `value`; 커널이 불확실성 전액을 자기 자신 ref=symbol 의 `shared_component` 로 자동 태깅=L4 joint 승격) + **소비자 배선**: `radiometric-uPb` 에 `calibration` 입력 포트, 커널이 보정 σ 를 (a) 자기 marginal budget 에 제곱합 + (b) shared_component 로 태깅. **값 불변 = 재계산 아닌 공분산 배선(L1)**. 캡스톤 데모(`seed_demo` demo-cov)를 매직 스트링 → **진짜 공유 노드**로 재구성: ²³⁸U 붕괴상수는 물리적으로 하나 → `decay-238U` **딱 한 노드**가 두 연대에 갈라짐(shared→Cov 1.96→L1b **pass**) vs 공유 의존을 모델에 기록 안 함(independent=노드 없음, 순진 독립→Cov 0→L1b **warn**). marginal 값·± 는 양쪽 동일, 차이는 provenance(노드+엣지)뿐. **pytest 174**(커널 단위 5케이스 신규). 프런트 변경·마이그레이션 없음(팔레트·포트·인스펙터 동적). **남은 것(L2)**: 상수 값 변경이 연대 **값**을 재계산하는 rescale(raw invariant/민감도 노드) — 유스케이스 대기.
- **0.1.48~0.1.53**(devlog 132~138) — readonly 그룹 드릴인 · 레퍼런스 후속(Crossref 자동 메타데이터) · Tier-1 CI 플로우 시나리오 테스트 + **gateway-wipe 버그 수정** · **clamp 축소**(`pin`/`range`/`freeze-version` NodeType 제거, GSSA=`published-age` leaf, `releases.Clamp` DEMO-ONLY) · Editor.jsx 분해 1·2차(1252→966줄). 전부 운영 반영·재시드 완료. 0.1.52 에서 compose 볼륨을 디렉터리 바인드로 바꾸며 `deploy.sh` DB 바인딩 게이트 추가.
- **P07 — Base of Cambrian realistic model**([devlog 131](devlog/20260710_131_p07-base-cambrian-realistic-model.md)): provenance vertical slice 를 실제 추론 구조로 — `section`/`horizon`/`reference` 노드, 3 dated 섹션(Oman·Namibia·Siberia)의 U-Pb ash bed 가 δ13C BACE horizon bracket → age-depth interpolate → cross-section-correlation → T. pedum FAD `calibration-transfer` → base of Cambrian 538.82 Ma. example③ 23노드·example④ 279노드. 운영 반영 완료.

**배경(0.1.35~0.1.46)**: **레퍼런스 노드 + bake→bibliography**(devlog 127·128) 위에 P07 을 쌓음. 이전 P04(불변 Bake·Vault) · P05(멀티유저 CI) · P06(Science Engine: 공분산 백본·정합성 게이트 L1/L2·clamp reconcile) · P06.4a(비동기 워커) 는 그대로. **다음: R04 L2(상수 변경→연대 값 rescale 커널) · P06.4b(PyMC joint) · 아크 A(L2/L3).** (P07 운영 반영·devlog·clamp 통합→축소·Editor 분해 1·2차·Tier1/2 테스트·R04 L1 공분산 배선은 완료.)

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
- **배포/운영** (배포·데이터 계약 P08 — [DEPLOY.md](DEPLOY.md)·[deploy/README.md](deploy/README.md)·[deploy/deploy.toml](deploy/deploy.toml)):
  - Docker 이미지 `honestjung/cdgts`, `deploy/build.sh <ver>` 로 pytest→bump→build→push. 버전 `config/version.py`.
  - **운영서버** `cdgts.paleobytes.info`(GCP dolfinid-2) @ **0.1.60**(nginx + certbot). 테스트 `127.0.0.1:8011`(m710q) @ **0.1.60**.
    **양 서버 cdgts(웹) + cdgts-worker(비동기 평가) 둘 다 가동**. 테스트 DB(prod 미러)에 P05 검증용 계정: `admin`(staff·ICS chair)·`demo`(비-staff·ICS chair·개인 fork).
  - **git-free + self-heal 배포(0.1.58~)**: 운영 서버에 repo 불필요. 모든 host 파일이 이미지 `/app/deploy/host/*`(`COPY . .`)에
    실려, 진입점 `deploy-{prod,dev}.sh X.Y.Z [--reseed]` 가 `_extract_and_deploy.sh` 로 이미지에서 추출 + 부트스트랩 파일까지
    자기 치유. **배포 = 한 줄**(git pull/sync 불요). prod=스냅샷(pre_deploy) 후 스왑, dev=스냅샷 없이(DB=운영 복사본).
    `deploy.sh` 재기동은 `docker compose up -d`(웹+워커 전 서비스). m710q→prod SSH 별칭 `dolfinid`(키 인증)로 원격 배포 가능.
  - **동사·게이트**: `/healthz`(버전+DB+핵심 행 수 → 200/503) · `smoke.sh`(배포 후 healthz+버전+행 수, prod SSL `X-Forwarded-Proto`
    대응) · `rollback.sh`(이전 이미지+pre_deploy 스냅샷) · DB 바인딩 게이트([5/6], 이미지 내부 빈 DB 폴백 차단) · `preflight.sh`(위험 표면 diff).
  - **백업**: 원자적 스냅샷(WAL torn-copy 방지) + NAS 오프사이트 + 04:00 cron.
  - ⚠️ **시드/레이아웃 변경 릴리스는 재시드 필요** — 0.1.57~ 는 **`--reseed` 플래그**로 자동(migrate 후 smoke 전 `seed --mode=replace`
    + `seed_demo`). replace 는 P08.1 이후 **운영 데이터(owner-set) 보존 upsert**(자연키 멱등). add 는 그래프 원자 skip → 변경 반영 안 됨.
- **초기 데이터(seed)**: 통합 `seed/`(manifest `2026.07.0`, 자연키) — `01_chrono`~`04_releases` + **`05_icc_release`**.
  `manage.py seed --mode=replace|add`. 순환 자연키 FK(그룹↔노드)는 forward-ref 2패스로 로드. `FIXTURE_DIRS=seed/`.
- **테스트**: 백엔드 `pytest` **178 passed**(L2 게이트·seed 회귀 + P04/P05 소유·CI·가시성 + calibration 커널 공분산 상속/비상속 + seed replace 운영 데이터 생존 + /healthz 포함). 테스트 fixture 는 seed 파일 loaddata.
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

## 진행 중 (WIP)

- **인터페이스(Group I/O) 노드 위치 영속** — 현재 드릴인별 프론트 세션 메모리(리로드/저장 시 초기화).
  영속 필요 시 NodeGroup 에 io 좌표 필드 추가(후속).

### 완료된 큰 아크 (배포됨)

- **[P04](devlog/20260707_P04_editor-bake-vault-restructure.md)** — Editor→Bake→**Vault** 재구성(불변 Release 아티팩트·Bake 액션·Chart/Table/Narrative/Diff 허브). devlog 102~104.
- **[P05](devlog/20260707_P05_arc-c-multiuser-ci-platform.md)** — 아크 C 멀티유저 CI: 세션 인증·Graph/Release 소유·가시성·fork·propose/review/ratify·샌드박스 오버라이드. devlog 106~110. 흐름 = 로그인→fork→편집→(bake→Vault)/propose→review→ratify · sandbox→override.
- **P06** — Science Engine(공분산 백본·정합성 게이트 L1/L2·clamp reconcile) · P06.4a 비동기 워커.
- **[P08](devlog/20260713_P08_deploy-data-contract-retrofit.md)** — 배포·데이터 계약(seed 레인 경계·매니페스트·/healthz·git-free·self-heal). devlog 140~144.

### 후속 (열린 항목, 우선순위 대략순)

- [ ] **R04 L2** — 상수 값 변경이 연대 **값**을 재계산하는 rescale 커널(raw invariant/민감도 노드). L1 공분산 배선(0.1.54~55)의 다음 단계.
- [ ] **L2/L3 확장** — L2 warn 임계(과소/과대 duration 의심) · L3 joint reconcile · 프론트 cert 뷰 L2 상세.
- [ ] **계산 커널 확장 / P06.4b** — age-depth 외 joint/베이지안(PyMC) 노드타입별 실제 커널(별도 워커).
- [ ] **PostGIS** — chrono.Locality lat/lon → PointField(공간 차원 착수 시).
- [ ] **retype diff 실데모** — Ediacaran/Cryogenian 경계 추가로 GSSA→GSSP retype 시나리오.
- [ ] **미해결 열린 질문** — 각 설계 문서 말미. → `TODOs.md` §2.
