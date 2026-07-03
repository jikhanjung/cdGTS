# 20260703_P01 — 앱 구축 개발 계획 (Django)

> **P 시리즈 = 개발 계획(Plan)** 문서. 일반 devlog(NNN, 완료 기록)와 구분.
> 설계 청사진은 [docs/app-architecture.md](../docs/app-architecture.md). 본 문서는 **실행 순서·마일스톤**.
> 확정 결정: React Flow + DRF 에디터 / engine 은 pass-through 먼저.

## 목표

브레인스토밍 개념 코퍼스 → 작동하는 Django 앱 5개(+ React Flow 에디터). 사용자 4대 요구:
DB 관리 · 노드 정의 · 네트웍 설계 · 작동. 아래 페이즈가 이를 순서화한다.

## 원칙

- **아래에서 위로** 의존 순서대로(chrono → nodes → graph → engine → releases). 각 페이즈는 독립 검증 가능.
- **pass-through 우선** — 구조·인용·diff·게이트 골격 먼저, 무거운 계산(MC/베이지안)은 노드 타입별 점진.
- **각 페이즈 = 마이그레이션 + admin + 최소 검증(seed/fixture 또는 API 왕복)** 로 "작동" 확인 후 다음.
- 한/영 문서 쌍은 docs/ 에만(devlog·계획은 한글 단독).

---

## Phase 0 — 환경 뼈대 ✅ (완료, devlog 014)

Django 5.2.12 + SQLite + config/ 레이아웃 + runserver 200 확인.

## Phase 1 — `chrono` (DB registry) — "DB 관리"

정본 명명·경계 정체성. 값이 아니라 이름/계보.

- 모델: `Unit`(이중 명명·self-FK 위계) · `Boundary`(슬러그+separates) · `BoundaryLineage`(op+from) ·
  `Authority` · `Ratification` · `Locality`(lat/lon 스칼라).
- Django **admin** 등록 → 이게 "DB 관리" UI 1차.
- **Fixture**: 세 사례 경계 시드(base-triassic / base-proterozoic / base-cambrian) — 스키마 §3 예시에서.
- 검증: migrate + admin 에서 세 경계 CRUD + `separates` 위계 조회.
- **DoD**: 세 경계가 admin 에 존재, lineage/authority 연결.

## Phase 2 — `nodes` (타입 시스템) — "각종 노드 정의"

무슨 노드가 존재할 수 있는가(어휘).

- 모델: `NodeType`(category data|process|clamp, 포트 스펙, 파라미터 JSON schema) ·
  `Distribution`(값 객체, 충실도 L0–L5).
- **Fixture**: 데이터/프로세스/clamp 기본 타입 시드(radiometric-uPb, age-depth-model, pin …).
- 검증: admin 에서 NodeType 목록 + 포트 스펙 조회. `Distribution` 직렬화 왕복 테스트(pytest).
- **DoD**: 노드 타입 카탈로그가 데이터로 존재(하드코딩 아님).

## Phase 3 — `graph` (DAG) + DRF API — "네트웍 설계" (백엔드)

실제 네트워크 저장 + 에디터가 붙을 API.

- 모델: `Graph` · `NodeInstance`(type+좌표+params) · `Edge`(포트+엣지타입) · `NodeGroup` · `Gateway`.
- **불변식**: DAG 검증(사이클 금지, joint-inference/clamp 절단 예외).
- **스택 추가**: `djangorestframework`. `GET/PUT /api/graphs/{id}` → `{nodes[],edges[],viewport}`.
  `POST /api/graphs/{id}/evaluate`(스텁).
- 검증: API 로 그래프 생성→노드/엣지 추가→PUT 저장→GET 왕복. 사이클 거부 테스트.
- **DoD**: React Flow JSON 모양으로 그래프를 저장/복원할 수 있다(프론트 없이 curl/pytest 로).

## Phase 4 — 프론트엔드 에디터 (React Flow + Vite) — "drag & drop"

Figma/Blender-nodes 느낌 캔버스.

- **스택 추가**: `frontend/` (React + React Flow + Vite, 독립 빌드). Django 는 정적 번들 서빙 또는 개발 프록시.
- `nodes.NodeType` → 커스텀 노드 팔레트(데이터 구동). 드래그 배치·엣지 연결·팬/줌/미니맵.
- 저장: 디바운스 PUT → Phase 3 API. 로드: GET.
- 검증: 브라우저에서 노드 드래그 배치 → 엣지 연결 → 새로고침 후 복원.
- **DoD**: 웹페이지 위에서 노드 그래프를 손으로 그리고 저장/복원.

## Phase 5 — `engine` (평가, pass-through) — "작동하게 만들기"

값+출처 전파 골격.

- 모델: `EvalRun` · `NodeResult`(분포+콘텐츠 해시) · `CoherenceCertificate`(L0–L3 스텁).
- **pass-through**: 노드 출력 = 입력 분포 그대로. 증분(해시 캐시). 계산 커널은 후속.
- `/evaluate` 실동작 → NodeResult 반환, 에디터에 결과 뱃지.
- 검증: 시드 그래프 평가 → leaf 분포가 gateway 까지 전파, 재평가 시 캐시 히트.
- **DoD**: 그래프가 "돈다" — 입력을 바꾸면 하류 결과가 갱신되고 provenance 역추적 가능.

## Phase 6 — `releases` (버전·배포·diff)

- 모델: `ModelCandidate` · `Release`(selection+clamps) · `BoundaryRecord`(bake 스냅샷) · `Diff`.
- 값 diff + 토폴로지 diff(lineage 정렬). bake(→Record) / narrate(스텁).
- 검증: 두 릴리스 생성 → 값 diff + 경계 재배선(retype) 토폴로지 diff 표기.
- **DoD**: 릴리스를 얼리고 두 릴리스를 diff.

---

## 스택 추가 요약 (페이즈별)

| 페이즈 | 추가 |
|---|---|
| 3 | `djangorestframework` |
| 4 | React + React Flow + Vite (`frontend/`) |
| 후속(5+) | Celery/RQ + numpy/scipy/PyMC (engine 이 pass-through 초과 시) |
| 공간 기능 착수 시 | PostGIS (chrono.Locality → PointField) |

## 지연된 결정 (착수 중 확정)

- definition 소속(Boundary vs BoundaryRecord) · NodeType↔커널 바인딩 · Gateway↔Record 관계 ·
  Graph 브랜치/샌드박스(fork+델타). → [app-architecture §5](../docs/app-architecture.md) · [TODOs §2](../TODOs.md).

## 다음 액션

- Phase 1 `chrono` 앱 생성(`startapp chrono`) + 모델 + admin + 세 경계 fixture.
