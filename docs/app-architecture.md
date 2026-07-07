# 앱 아키텍처 (App Architecture)

*[English](app-architecture_en.md) · 한국어*

> 상태: **설계 v0.** 브레인스토밍 개념 코퍼스를 Django 앱 구조로 처음 옮긴 것. 코드 착수 전 청사진.
> 어휘·구조는 [concept-map](concept-map.md) · [node-graph-paradigm](node-graph-paradigm.md) ·
> [boundary-gateway-schema](boundary-gateway-schema.md)에 종속. 확정 아님.

## 0. 설계 원칙

개념 문서의 두 축을 앱 경계로 삼는다:

1. **게이트웨이/네트워크 2계층** (node-graph §게이트웨이) — *비준·인용 대상인 고정 계약*과 *자유롭게
   churn 하는 네트워크*를 분리. → `graph`가 둘 다 담되 `Gateway`를 1급 모델로.
2. **registry(정본 명명) vs release(얼린 산출물)** 분리 — 이름/계보는 안정, 값/정의 스냅샷은 버전별.
   → `chrono`(정본) ↔ `releases`(스냅샷) 양극.
3. **노드 *타입 정의* vs *인스턴스*** 분리 — 무슨 노드가 존재할 수 있는가(어휘)와 실제로 배선된
   네트워크는 다른 관심사. → `nodes`(타입) ↔ `graph`(인스턴스).

## 1. 앱 지도

| 앱 | 책임 | 대응 개념 |
|---|---|---|
| **`chrono`** | 정본 명명·위계·경계 정체성·권위 (DB registry) | Layer 0, `identity.lineage` |
| **`nodes`** | 노드 *타입 시스템* — 데이터/프로세스/clamp 종류, 포트, 분포 페이로드 | node-graph 노드 종류, 충실도 사다리 |
| **`graph`** | 실제 DAG — 노드 인스턴스·엣지·노드그룹·게이트웨이·캔버스 레이아웃 | 네트워크, 게이트웨이 2계층 |
| **`engine`** | 평가(확률 전파)·증분 재계산·정합성 게이트·bake/narrate | Layer 5, coherence-gate |
| **`releases`** | Release 매니페스트(selection+clamps)·ICC/GTS·값/토폴로지 diff · **Bake 아티팩트·Proposal(CI)** | versioning, competing-models, topology-diff |
| **`accounts`** | User↔Authority Membership · 세션 인증 · 중앙 `can_ratify` | 멀티유저 CI(P05) |
| **(프론트엔드)** | React Flow drag&drop 캔버스 ↔ `graph` REST API · Vault · Proposals | Figma/Blender-nodes 느낌 |

> **구현 현황**: 위 설계는 6개 앱으로 구현됨(+`accounts`, P05). 아티팩트=불변 Release(Vault)·멀티유저 CI(fork·propose·ratify)는 devlog 102~109 참조. 배포/현재 상태는 [HANDOFF.md](../HANDOFF.md).

의존 방향 (하위는 상위를 모름):

```
chrono ◁─ nodes ◁─ graph ◁─ engine ◁─ releases
(registry)  (타입)   (DAG)   (평가)    (배포·diff)
   ▲                                      │
   └────── releases.BoundaryRecord ────────┘
           → chrono.Boundary 참조
```

## 2. 앱별 상세

### 2.1 `chrono` — 정본 registry ("DB 관리")

*값이 아니라 이름과 계보.* 모든 앱이 여기를 가리킨다.

- `Unit` — 이중 명명(연대층서 Eonothem/System/Stage ↔ 지질연대 Eon/Period/Age)을 한 엔티티 양면으로.
  위계는 self-FK.
- `Boundary` — **안정 슬러그**(`base-triassic`) + `separates(below/above → Unit)`. 값·정의 없음.
- `BoundaryLineage` — `op: created|renamed|split|merged|retyped|deprecated` + `from:[Boundary]`.
  토폴로지 diff의 전제.
- `Authority` — ICS, subcommission, `sandbox-branch:*`, `fork:*`.
- `Ratification` — 연도·주체.
- `Locality` — GSSP 노두. 지금은 `lat/lon` 스칼라 → **PostGIS 착수 시 PointField 승격**
  (이게 SQLite→PostGIS 전환의 실질 트리거).

### 2.2 `nodes` — 노드 타입 시스템 ("각종 노드 정의")

*무슨 종류의 노드가 존재할 수 있는가* = 어휘. 인스턴스 아님.

- `NodeType` — `category: data | process | clamp`, 포트 스펙(입출력 타입), 파라미터 스키마(JSON).
  - 데이터: `radiometric-uPb`, `astronomical`, `magnetostratigraphic`, `biostratigraphic` (불변·인용·leaf)
  - 프로세스: `age-depth-model`, `cross-section-correlation`, `calibration-transfer`, `joint-inference`
  - clamp: `pin | range | order | freeze-version` (GSSA = `pin`의 특수사례)
- `Distribution`(값 객체) — 스키마 `uncertainty` 충실도 사다리 **L0–L5**:
  `fidelity: exact|sym|decomposed|shape|joint|full`, `budget{analytical,systematic,model}`,
  `shared_components`, `posterior_ref`. 엣지가 흘리는 것 = 이 분포(스칼라 아님).

> `NodeType`을 데이터로 두면 학자가 새 모델 종류를 플러그인처럼 등록 가능. `process` 노드의 실제
> 계산 커널은 `engine`에 코드로 있고 `NodeType.kind`로 바인딩.

### 2.3 `graph` — 실제 DAG ("네트웍 설계")

학자가 캔버스에서 만든 한 개의 네트워크. drag&drop 에디터의 백엔드 상태.

- `Graph` — 컨테이너(브랜치/샌드박스 단위), 소유자, 상태.
- `NodeInstance` — `graph`, `type→NodeType`, 파라미터, **캔버스 좌표(x,y)**, 그룹.
- `Edge` — `from_port→to_port`, **엣지 타입(`co-location | calibration-transfer`)** —
  게이트가 이걸로 사이클 탐지.
- `NodeGroup` — 지역/경계별 서브그래프. 접으면 게이트웨이처럼.
- `Gateway` — **비준·인용·버전의 단위(계약)**. 노드그룹 출력을 고정 타입으로 노출.
  스키마 `BoundaryGateway`가 참조하는 대상.

> 불변식: DAG 유지(사이클 금지) — 단 `joint-inference`/clamp 노드로 절단 허용(cycles §).

### 2.4 `engine` — 평가 ("작동하게 만들기")

**착수 스코프: pass-through 먼저.** 노드 출력 = 입력 분포 그대로 전파(계산 없음) — idea §7의
"발표값+출처" 층. 그래프·인용·diff·게이트 골격을 먼저 세우고, MC/베이지안 계산 커널은
노드 타입별로 점진 투입. 문서 미션 재정의("사람이 clamp, 기계가 전파·정합·diff")와 정합.

- `EvalRun` — 한 `Graph`(서브그래프)의 평가 작업. 상태·트리거·입력 해시.
- `NodeResult` — 노드별 산출 분포 + **콘텐츠 해시**(입력 불변 시 캐시 재사용 = 증분 재평가).
- `CoherenceCertificate` — Layer 5 게이트 검사(L0–L3: 단조순서·구간겹침·joint 정합).
- **분리 원칙**: Django는 오케스트레이션만. 확률 전파·joint 추정은 별도 과학 스택
  (numpy/scipy/PyMC) 워커. 초기 동기/관리명령 → 이후 Celery/RQ.
- **bake/narrate**: bake=분포 요약·고정→`releases`, narrate=추론·caveat 직렬화(GTS).

### 2.5 `releases` — 버전·배포·diff

- `ModelCandidate` — 네트워크 공존 경쟁 후보(독립 주소), `scope: boundary|global`,
  `output{boundary:{value,dist}}`.
- `Release` — 매니페스트: `selection{boundary→ModelCandidate}`, `clamps[]`.
  **릴리스가 selection 소유**(경계 레코드가 아니라).
- `BoundaryRecord` — 한 Release에서 얼린 `BoundaryGateway` 스냅샷(definition+age+model_ref+
  provenance_ref) = ICC bake. `chrono.Boundary` 참조.
- `Diff` — 두 Release 간 **값 diff** + **토폴로지 diff(직교 축)**. lineage 정렬, edit-script/
  2색 합집합 표기.

## 3. drag & drop 에디터 — 프론트엔드 (React Flow + DRF)

Figma/Blender-nodes 느낌의 캔버스는 서버렌더링(django-bootstrap5)로 불가 → 클라이언트 그래프
라이브러리 필요. **선택: React Flow.** (노드 에디터 사실상 표준; 팬/줌/스냅/미니맵/커스텀 노드.)

아키텍처:

```
[React Flow SPA (Vite 빌드)]
      │  GET/PUT /api/graphs/{id}   {nodes[], edges[], viewport}
      ▼
[graph app + DRF]  ── NodeInstance/Edge/좌표 ↔ React Flow JSON 1:1
      │  POST /api/graphs/{id}/evaluate
      ▼
[engine]  → NodeResult(분포) 스트리밍
```

- 그래프 저장: 디바운스 PUT.
- React Flow 노드 JSON ↔ `graph.NodeInstance`(좌표 포함) 1:1 → 그래서 캔버스 좌표를 모델에 둠.
- `nodes.NodeType`이 React Flow 커스텀 노드 팔레트를 데이터로 구동.

**스택 확장(명시)**: `djangorestframework` 추가 + **Node/React 툴체인**(별도 빌드 스텝,
`package.json`, Vite). fsis2026 순수 서버렌더 패턴에서 벗어나는 첫 지점.

## 4. 스택에 추가되는 것

- `djangorestframework` (graph/engine API)
- 프론트엔드 툴체인: React + React Flow + Vite (별도 `frontend/` 디렉토리, 독립 빌드)
- (나중) Celery/RQ + numpy/scipy/PyMC 워커 — engine이 pass-through를 넘어설 때

## 5. 열린 모델링 질문 (다음 결정)

- **definition 소속** — GSSP 마커/노두를 `chrono.Boundary`(안정) vs `releases.BoundaryRecord`
  (버전별, retype 허용) 어디에. 잠정: 현재값은 Boundary, 스냅샷은 Record.
- **NodeType 코드 바인딩** — 계산 커널을 `NodeType.kind` 문자열 ↔ engine 레지스트리로 어떻게 연결.
- **Gateway ↔ BoundaryRecord 관계** — Gateway(그래프 내 계약)와 Record(릴리스 스냅샷)의 중복/참조.
- **Graph 브랜치/샌드박스 모델** — fork·override(베이스라인+델타) 표현 (versioning §).
- 나머지 스키마 열린 질문은 [TODOs](../TODOs.md) §2 참조.

## 6. 링크

- [concept-map](concept-map.md) — 상위 개념 지도
- [node-graph-paradigm](node-graph-paradigm.md) — 게이트웨이/네트워크 2계층
- [boundary-gateway-schema](boundary-gateway-schema.md) — 스키마 v0 (모델의 출처)
- [TODOs](../TODOs.md) §0 — 착수 결정
