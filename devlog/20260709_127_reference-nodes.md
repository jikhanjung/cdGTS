# 20260709_127 — 레퍼런스 노드 (provenance as a graph citizen)

데이터/모델 노드의 **source(출처)를 그래프에 명시적으로** 넣는다. 사용자 선택 = "그래프 reference 노드
타입 + cite 엣지"(vs 노드 메타데이터 M2M). 이유: 가시성 + 데이터/모델이 레퍼런스를 끌고 들어가는 게
패러다임("모든 것은 노드")에 맞고, **나중에 bake 시 cite 엣지를 역추적해 참고문헌을 자동 수집**할 수 있음.

## 설계

- **`reference` = 데이터 흐름이 아니라 provenance 주석.** cite 엣지는 order 엣지처럼 **비-데이터**:
  평가 위상·순환 판정·포트 검증에서 전부 제외(`Edge.NON_DATA_KINDS = {order, cite}`).
- reference 노드(`citation` out) → 피인용 노드(`cited` in). 대상에 선언 포트 불요(order 와 대칭).

## 백엔드

- **새 `references` 앱** — `Reference` 모델(DOI 레지스트리): slug(자연키)·doi·title·authors·year·
  container·url·kind. `link`(doi.org 우선). 부분 유니크(doi 비어있지 않을 때). `ReferenceViewSet`
  CRUD(`/api/references/`, 읽기 공개·쓰기 로그인). INSTALLED_APPS·urls 등록. migration 0001.
- **`cite` 엣지 종류**(`graph.Edge.Kind`) + `NON_DATA_KINDS` 상수. serializer 포트검증·사이클판정,
  `engine.evaluate`(needs_async·evaluate_graph·_certify) 세 곳을 `not in NON_DATA_KINDS` 로 갱신.
- **`reference` NodeType**(새 카테고리 `reference`, `citation` out 포트) — seed/02_nodes.json.
- **그래프 참고문헌 API** `GET /api/graphs/{id}/references/` → `{bibliography[], citations[]}`
  (reference 노드가 가리키는 Reference + cite 대상 노드). bake→bibliography 의 seam.

## 프론트

- 팔레트에 `reference` 카테고리 노드 자동 노출. 노드 얼굴에 저자·연도·DOI(레지스트리에서 해석).
- **cite 엣지 배선**: reference 의 citation(우측 out) → 노드의 `cited`(상단 amber) 핸들 드래그 →
  kind=cite(amber 점선). apiToRF/onConnect 에 cite 스타일·감지(`edgeStyleFor`).
- **인스펙터 reference 필드**: 레지스트리 select + 선택 시 제목·DOI 링크(↗) + **인라인 새 레퍼런스 추가**
  (slug·doi·title·authors·year → `POST /api/references/`). 등록 후 노드 얼굴에 즉시 반영.

## 검증

- pytest **154 passed**(신규 7): Reference link/유니크/권한, cite 엣지 왕복·평가 제외, 그래프 참고문헌 API.
- 임시 DB 수동 확인: cite 엣지가 평가 provenance·needs_async 에 영향 없음(obs 값 그대로, ref 노드 값 None).
- 프론트 `npm run build` 정상.

## 배포 주의

- 마이그레이션: `references.0001`·`nodes.0003`(category)·`graph.0010`(edge kind) — entrypoint migrate 자동.
- **seed 변경**(reference NodeType 추가) → 배포 후 `manage.py seed --mode=add` 1회면 노드타입 반영
  (add 는 기존 그래프 원자 skip, 신규 NodeType 은 자연키로 추가). 그래프 시드까지 갱신하려면 replace.

## 다음(후속)

- **bake→bibliography**: 릴리스 bake 시 게이트웨이에서 cite 엣지를 역추적해 결과별 참고문헌 목록 산출·표기.
- reference 노드 얼굴에서 DOI 직접 클릭(현재는 인스펙터에서). 레지스트리 관리 뷰(Vault 탭?).
- Crossref DOI 자동 메타데이터 해석(수동 입력 → 자동 채움).
