# 20260703_017 — Phase 3: graph 앱 (DAG + DRF API)

> 계획 [P01](20260703_P01_app-build-plan.md) Phase 3 완료 기록. 설계 [app-architecture §2.3](../docs/app-architecture.md).

## 한 일

세 번째 앱 `graph` — 실제 DAG(네트워크) + React Flow 왕복 API. 스택에 **DRF 첫 도입**.

### 모델 (`graph/models.py`)
- `Graph` — 컨테이너(브랜치/샌드박스), status, `viewport`(React Flow 팬/줌), owner, 타임스탬프.
- `NodeInstance` — 캔버스 노드. `key`(=React Flow 노드 id, 그래프 내 유일) + `node_type`(→nodes) + params + x/y + group.
  `is_cycle_breaker` 프로퍼티(clamp / joint-inference).
- `Edge` — `source/target`(NodeInstance) + 포트 이름 + `kind`(data|co-location|calibration-transfer).
- `NodeGroup` — 지역/경계별 서브그래프. `Gateway` — 비준·인용 단위, 노드 출력 노출 + chrono.Boundary 링크.

### DAG 불변식 (`graph/dag.py`)
- `find_unbroken_cycles` — **cycle-breaker(clamp/joint-inference)를 잘라낸 부분그래프가 acyclic 이어야**.
  Kahn 위상정렬로 남는 노드 = 끊기지 않은 순환. 순수 함수(저장 전 검증).

### DRF API (`serializers.py`·`views.py`·`urls.py`)
- `GET/PUT /api/graphs/{id}/` — `{nodes[], edges[], viewport}` 왕복. PUT 은 **통째 교체**(wholesale replace),
  저장 전 검증: 포트 방향 정합 + 끊기지 않은 순환 금지. slug/name 은 생성 시 고정(토폴로지 PUT 이 개명 안 함).
- `POST /api/graphs/{id}/evaluate/` — Phase 5 engine 스텁(node/edge count 반환).
- 엣지 끝점은 노드 **key** 로 직렬화(FK __str__ 아님) — React Flow 노드 id 매칭.
- 권한 dev AllowAny(착수 검증용, 인증·소유권 후속). `config/urls.py` 에 `/api/` 마운트.

### admin
- Graph(노드/엣지/게이트웨이 인라인) + NodeInstance/NodeGroup/Gateway.

### 테스트 (`graph/tests.py`)
- DAG 순수함수(acyclic/순환탐지/breaker 절단) + API 왕복 + wholesale replace + **순환 거부(400)** +
  joint-inference 통과 순환 허용 + 잘못된 포트 거부 + evaluate 스텁. **전체 28 passed**.

## 검증
- check 0 · migrate OK · pytest 28 passed · **live curl 왕복**(POST 생성→GET 왕복→evaluate node_count 2→순환 PUT 400).
- **버그 잡음**: 엣지 GET 이 노드 __str__ 를 내보내 key 왕복이 깨지던 것 → plain Serializer + to_representation 으로 수정, 테스트 강화(curl 이 먼저 노출).
- **DoD 충족**: React Flow JSON 모양으로 그래프 저장/복원(프론트 없이 curl/pytest), 사이클 거부.

## 스택
- **djangorestframework==3.17.1** 추가(requirements.txt). `rest_framework` + `graph.apps.GraphConfig` → INSTALLED_APPS.

## 다음
- **Phase 4** 프론트엔드 — React Flow + Vite `frontend/`, nodes.NodeType → 노드 팔레트, 이 API 왕복.
