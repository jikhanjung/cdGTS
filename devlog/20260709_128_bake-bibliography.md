# 20260709_128 — bake → bibliography (cite 역추적 참고문헌 수집)

레퍼런스 노드([127](20260709_127_reference-nodes.md))의 후속. 사용자 구상: "최종 결과물 bake 하면서
그래프 거슬러올라가서 레퍼런스들 모두 모아서 쉽게 보여주기." 게이트웨이에서 **데이터 흐름을 역추적**해
각 경계에 기여한 레퍼런스를 수집·스냅샷·표기한다.

## 귀속 규칙

reference 노드가 cite 엣지로 노드 M 을 인용할 때, M 이 어떤 게이트웨이 노드의 **상류 데이터-흐름 cone**
(데이터 엣지 역방향 도달집합)에 있으면 그 경계에 **기여**한다. order/cite 는 데이터 흐름이 아니라 cone 을
전파하지 않는다 → 관련 없는 곳에 붙은 레퍼런스는 그 경계에 안 딸려온다.

## 백엔드

- **`graph.services.graph_bibliography(graph)`** — `{by_boundary: {slug: [ref_slug]}, all: [ref_slug]}`.
  게이트웨이 노드별 상류 cone(BFS, 데이터 엣지만) → cone 안에서 cite 된 reference 슬러그 수집.
- **bake 스냅샷** — `BoundaryRecord.references`(JSONField) 신설(migration releases.0009).
  `_write_graph_records` 가 bake 시 경계별 기여 레퍼런스를 레코드에 복사(불변 스냅샷).
- **API**
  - `GET /api/graphs/{id}/references/` 에 `by_boundary` 추가(편집 중 경계별 귀속 미리보기).
  - `GET /api/releases/{id}/references/` 신설 — 릴리스 bibliography(레코드 스냅샷 union) + `by_boundary`.

## 프론트

- **Vault "References" 탭** — `Bibliography.jsx`. 릴리스의 참고문헌 목록(저자·연도·제목·DOI 링크 ↗),
  각 레퍼런스가 어느 경계를 먹이는지(`feeds: …`) 역표기. MODES 에 `references` 추가.

## 검증

- pytest **156 passed**(신규 2 + 그래프 endpoint by_boundary 단언): bake 시 레코드 references 스냅샷,
  릴리스 references 엔드포인트, **상류만 귀속**(관련 없는 곳에 인용된 레퍼런스는 경계에 안 딸려옴).
- 프론트 `npm run build` 정상.

## 메모 / 다음

- 현재 cone = **데이터 엣지 역방향 전체**. clamp/joint 로 끊긴 순환 경계는 breaker 상류까지만(evaluate 와 동일 관점).
- 후속: reference 노드 얼굴에서 DOI 직접 클릭 · 레지스트리 관리 뷰 · Crossref DOI 자동 메타데이터 ·
  narrate(GTS)에 참고문헌 자동 삽입.
