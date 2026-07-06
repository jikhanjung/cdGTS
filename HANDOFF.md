# HANDOFF — Current Work Status

**Last updated**: 2026-07-06 (**v0.1.18 운영서버 배포 완료**. v0.1.4 이후 하루(07-04~05) 동안 라운드 039~074:
**노드그룹 실기능화(중첩·병합) → order 제약 노드(L1 authored) → L2 duration 게이트 → ICC 차트(5컬럼+±)
→ 공표 ICC 릴리스(ICS-2024/12) → narrate → 전 ICC 계층 재구성(175경계·Subperiod 포함) → 모바일 대응
→ Science CI 원클릭 검증 → 선택 버그픽스 시리즈**. 백엔드 **pytest 85 passed**.
운영 **cdgts.paleobytes.info @ 0.1.18**. devlog 001~074 push.)

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
    **노드그룹 = 컨테이너+접기+드릴인, N단 중첩**(parent self-FK, 엔진은 평탄). **order 제약 노드**(두 경계
    선후 검사, 세로 핸들 위=younger/아래=older).
  - `engine` — 평가(EvalRun·NodeResult 콘텐츠해시 증분·CoherenceCertificate) + 계산 커널(numpy/scipy,
    age-depth 선형보간+spline MC). **정합성 게이트: L1 = authored order 체인(sparse) · L2 = 게이트웨이가
    덮는 전 유닛 duration>0 자동검사**(영-길이 유닛 검출, rank 별 타일링).
  - `releases` — ModelCandidate·Release·BoundaryRecord·Clamp + bake/diff/`bake_graph` API.
    **공표 ICC 릴리스 `ICS-2024/12`**(Epoch/Age 까지 값 정식화) + `GET /api/releases/{id}/icc-chart/`.
    **narrate**: `BoundaryRecord.narrative` 를 구조화 필드에서 결정적 템플릿 렌더(LLM 창작 없음).
- **프론트**: 팔레트/캔버스/인스펙터 에디터 + ICC 테이블 + **ICC 차트**(Eon~Age 5 컬럼 중첩, 경계 불확실성
  ± 밴드·툴팁) + 릴리스 Diff 뷰. **다중선택**(좌-드래그 선택/중앙 팬, Full 모드), 그룹 선택·병합, 세로
  order 포트(데이터 노드 위=older/아래=younger), 컴팩트 order 노드(세로 부등호). **모바일 대응**: 반응형
  드로어 + 터치 팬 + 탭-투-추가/롱프레스 메뉴. **Science CI 버튼**: 그래프 편집 → 재bake → 공표 baseline
  과 원클릭 diff(이동 경계·배선 변화 요약).
- **예제 그래프**: 3종 파이프라인 + **`example-icc-partial`(예제④, 270 노드)** — 전 ICC 재구성:
  Eon 4·Era 10·Period 22·Epoch 37·Age 102, 175 경계 전부. period=노드그룹(span)·내부 age order 체인,
  order 노드 137개는 위/아래 경계의 세로 중점 정렬(074).
- **배포/운영**:
  - Docker 이미지 `honestjung/cdgts`, `deploy/build.sh <ver>` 로 pytest→bump→build→push. 버전 `config/version.py`.
  - **운영서버** `cdgts.paleobytes.info` @ **0.1.18**(nginx + certbot). 개발/테스트 `127.0.0.1:8011`.
  - deploy-prod.sh / deploy-dev.sh 분리, 스왑 중 nginx maintenance. DB 분리 + prod→test sync.
  - **백업**: 원자적 스냅샷(WAL torn-copy 방지) + NAS 오프사이트 + 04:00 cron.
  - ⚠️ **시드 데이터(레이아웃 포함) 변경 릴리스는 `seed --mode=replace` 재시드 필요**(add 는 그래프 원자 skip).
- **초기 데이터(seed)**: 통합 `seed/`(manifest `2026.07.0`, 자연키) — `01_chrono`~`04_releases` + **`05_icc_release`**.
  `manage.py seed --mode=replace|add`. `FIXTURE_DIRS=seed/`.
- **테스트**: 백엔드 `pytest` **85 passed**(L2 게이트·seed 회귀 포함). 테스트 fixture 는 seed 파일 loaddata.
- **문서 코퍼스**: `docs/` 14주제 × 한/영 + README + app-architecture + naming(태그라인·표기 규칙) +
  evaluation-order(의존 vs 연대순, order=사후 검사). 진입점 `docs/concept-map.md`.
- **원격**: `git@github.com:jikhanjung/cdGTS.git`, main 직접 커밋·push.

## 개념/구현 진척 한 줄 정리

> **개념 → 스키마 v0 → 앱 설계 → Phase 0~6 → 계산 커널 → 배포 인프라 → ICC 전 계층 재구성(175경계) →
> 공표 릴리스 대비 Science CI 검증** 완주. 미션 "사람이 clamp, 기계가 전파·정합·diff" 가 실배포 환경에서
> **authored order(L1) + 자동 duration(L2) + 원클릭 공표 diff** 로 돎.

## 최근 작업 (2026-07-04 ~ 07-05, devlog 039~074)

- **노드그룹**(039·057·062) — 컨테이너+접기+드릴인 실기능화 → 그룹 선택·병합·order 포트 → N단 중첩(parent self-FK).
- **order 제약**(040·041) — order clamp 를 두 경계 선후 검사로 활성화, 예제4 를 order 체인으로 시간순 세로 정렬
  (기존 `_certify` 나열순 warn 스텁을 **명시적 authored 제약 체인**으로 대체).
- **ICC 차트**(042·044·066) — Eon/Era/Period 중첩 컬럼 → Epoch/Age 5 컬럼 + **공표 릴리스 ICS-2024/12** →
  경계 불확실성 ± 밴드.
- **narrate**(045) — `BoundaryRecord.narrative` 결정적 템플릿 렌더(bake 의 짝).
- **L2 게이트**(047) — 전 유닛 duration>0 자동검사, L1 이 못 잡는 영-길이 유닛 검출.
- **계층 재구성**(046·056·059·060) — Triassic 프로토 → 전 period age 그룹 → Epoch 층 + 전 175 경계 재구성 →
  Subperiod rank. 조립 그래프가 공표 릴리스와 완전 대칭.
- **에디터 UX**(049·050·051) — data↔order 세로 포트 · 다중선택(좌-드래그) · 컴팩트 order 노드.
- **모바일**(054·064) — 반응형(드로어+터치 팬) + 노드 생성(탭-투-추가·롱프레스 메뉴).
- **Science CI**(065) — 에디터 원클릭: 편집 → 재bake → 공표 baseline diff.
- **선택 버그픽스**(068·070·072·073) — auto-pan x 튐 → 재렌더 폭풍 프리즈 → Full 모드 → order 노드
  유령 폭(선택 판정) 근본 수정.
- **릴리스** — 0.1.5~0.1.18 순차 배포(빌드/푸시 Claude, 서버 배포 사용자). 시드 레이아웃 변경분은 재시드로 반영.

## 진행 중 (WIP · 미커밋 · 미배포)

- **경계·구간 이중성 모델**([boundary-span-duality](docs/boundary-span-duality.md), KR/EN) — 그래프 계층에
  셀 복합체 모델 도입. **백엔드+시드+프론트 코드 완료**(커밋 전, **육안 QA만 남음**):
  - **모델**: `NodeInstance.nature`(generic|boundary) · `NodeGroup.kind`(container|unit)·`unit`(chrono.Unit FK)·
    `lower`/`upper`(경계 노드 FK, SET_NULL) · `Edge.kind=order`. migration **graph.0005**.
  - **시리얼라이저**: 왕복(3패스: 그룹→parent→노드→lower/upper), order edge 포트검증·데이터 DAG 제외.
    `engine._certify` L1 = **order edge 체인 우선**(order 노드/게이트웨이 폴백 유지), `evaluate_graph` 도 order edge 위상 제외.
  - **시드 변환**(예제4): order 노드 137개 제거→**order edge 137개**, published-age 124개 `nature=boundary`,
    단위 그룹 14개 `kind=unit`+unit+lower/upper(공유 경계 예: mississippian.lower=carboniferous.base).
    노드 270→133. seed 명령에 **forward-ref 2패스**(handle_forward_references) 추가 — 순환 자연키 FK(그룹↔노드) 로드.
  - **프론트**: `apiToRF`/`rfToApi` 에 nature·kind·unit·lower·upper·order-edge 스레드(저장 유실 방지),
    order edge 점선(보라) 스타일. **블렌더식 그룹 I/O 인터페이스 노드**(`GroupIoNode.jsx`): 드릴인 시 외부
    연결을 입력 1개·출력 1개 노드로 집약(포트 다중, 선택·이동, 위치 드릴인별 기억) — 기존 per-edge stub 대체.
  - **검증**: pytest **90 passed**, seed replace(bake 3) OK, API 계약(nature 124/9·order 137·공유 경계) 확인, `npm run build` OK.
  - **남은 것**: 브라우저 육안 QA(인터페이스 노드 렌더·order 사다리 모양·이동) — 헤드리스 미검증. 인터페이스
    노드 위치는 현재 프론트 세션 메모리(리로드/저장 시 초기화) — 영속 필요하면 NodeGroup에 io 좌표 필드 추가(후속).

### 후속 (선택, 우선순위 대략순)

- [x] **`engine._certify` 층서순 정합** — order 제약 체인(040·041) + L2 duration 게이트(047)로 해소.
- [x] **finer 경계 값 릴리스화** — 공표 ICC 릴리스 `ICS-2024/12`(044)로 Epoch/Age 까지 정식화.
- [x] **narrate(GTS)** — BoundaryRecord.narrative 결정적 템플릿 렌더(045).
- [ ] **L2/L3 확장** — L2 warn 임계(과소/과대 duration 의심) · L3 joint reconcile · 프론트 cert 뷰 L2 상세(047 이월).
- [ ] **브라우저 육안 검증** — 선택/모바일 계열은 실사용 검증됐으나 인스펙터·diff 뷰 등 잔여 항목.
- [ ] **계산 커널 확장** — age-depth 외 joint/베이지안 등 노드타입별 실제 커널(별도 워커·PyMC).
- [ ] **인증·소유권** — 현재 API AllowAny(dev). 로그인·그래프 소유·샌드박스 권한.
- [ ] **clamp 통합** — order 노드는 활성화됨(040); 나머지 graph clamp ↔ releases.Clamp(authored 거버넌스) 관계 정리.
- [ ] **PostGIS** — chrono.Locality lat/lon → PointField(공간 차원 착수 시).
- [ ] **retype diff 실데모** — Ediacaran/Cryogenian 경계 추가로 GSSA→GSSP retype 시나리오(030 메모).
- [ ] **미해결 열린 질문** — 각 설계 문서 말미. → `TODOs.md` §2.
- [ ] **리뷰(R01)** — 구현 코드 리뷰 회차(devlog R 시리즈).
