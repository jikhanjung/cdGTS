# 20260703_016 — Phase 2: nodes 앱 (노드 타입 시스템)

> 계획 [P01](20260703_P01_app-build-plan.md) Phase 2 완료 기록. 설계 [app-architecture §2.2](../docs/app-architecture.md).

## 한 일

두 번째 앱 `nodes` — *무슨 노드가 존재할 수 있는가*(어휘). 인스턴스 아님(→ graph), 계산 커널 아님(→ engine).

### 모델 (`nodes/models.py`)
- `NodeType` — `category(data|process|clamp)` + `slug`(=engine 커널 바인딩 키) + `params_schema`(JSON).
  `input_ports`/`output_ports` 프로퍼티. NodeType 을 **데이터로** 둠 → 새 모델 종류 플러그인 등록.
- `Port` — 타입의 입출력 포트 스펙. `direction(in|out)` + `datatype(distribution|scalar|series|signal|any)`
  + `multiple`(번들 입력). 대부분 distribution(엣지가 분포를 흘린다).

### 값 객체 (`nodes/distribution.py`)
- `Distribution` — 충실도 사다리 **L0–L5**(exact→sym→decomposed→shape→joint→full). DB 테이블이 아니라
  JSON 임베드 값 객체(NodeResult·BoundaryRecord 가 나를 예정). `to_dict`/`from_dict`(빈 값 생략, 왕복 안전),
  `level` 프로퍼티, `exact()`(GSSA 점질량)·`symmetric()` 생성자. 검증: exact 은 value 필수·budget 금지.

### admin (`nodes/admin.py`)
- NodeType(Port 인라인 + in→out 요약) · Port 등록.

### fixture (`nodes/fixtures/initial_node_types.json`)
- **12 타입 + 22 포트 = 34객체**. data 4(radiometric-uPb·astronomical·magneto·biostrat) /
  process 4(age-depth-model·cross-section-correlation·calibration-transfer·joint-inference) /
  clamp 4(pin·range·order·freeze-version). 포트 datatype 로 "엣지=분포" 구현.

### 테스트 (`nodes/tests.py`)
- Distribution: 사다리 순서·점질량·budget 검증·**JSON 직렬화 왕복(parametrize 5)**·빈값 생략.
- 카탈로그: 12타입 로드·포트 배선·pin params·엣지 datatype. **전체 19 passed**(chrono 5 + nodes 14).

## 검증
- check 0 · migrate OK · loaddata 34 · shell 카탈로그 조회(data/process/clamp 포트) · pytest 19 passed.
- **DoD 충족**: 노드 타입 카탈로그가 데이터로 존재(하드코딩 아님), 포트 스펙 조회 가능, Distribution 왕복.

## 스택
- 추가 없음. `nodes.apps.NodesConfig` → INSTALLED_APPS.

## 다음
- **Phase 3 `graph`** — Graph/NodeInstance/Edge/NodeGroup/Gateway + DAG 불변식 + **DRF API**
  (`GET/PUT /api/graphs/{id}`, `POST .../evaluate` 스텁). 스택에 djangorestframework 추가.
