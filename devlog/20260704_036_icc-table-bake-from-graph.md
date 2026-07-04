# 20260704_036 — ICC 테이블 (그래프 bake)

> "ICC 테이블 만드는 기능 = bake". 그래프의 게이트웨이 출력을 경계 스냅샷으로 얼려 ICC 테이블로.
> 조립 예제([035](20260704_035_combined-icc-example.md)) 위에서 실제 산출물(ICC)을 뽑는 단계.

## 배경

기존 bake(`bake_release`)는 릴리스의 selection→candidate 출력 기반이라 **라이브 그래프와 분리**돼 있었다.
사용자가 만든 조립 그래프(데이터 노드 + 게이트웨이)를 그대로 ICC 테이블로 굽고 싶다 → **bake-from-graph**.

## 한 일

### 백엔드
- `releases.services.bake_graph(graph)` — 그래프 평가 → 각 **게이트웨이(경계 지정)의 노드 결과 분포**를
  `BoundaryRecord` 로 얼림. 그래프당 릴리스 `graph:<slug>` 하나에 스냅샷(재-bake 는 레코드 갱신, 멱등).
  기존 BoundaryRecord/Release/diff 인프라를 그대로 재사용 → bake 결과가 **릴리스 Diff 에서도 비교됨**.
- `POST /api/graphs/{id}/bake/` (`GraphBakeView`) → `{baked, release(records 포함)}`.

### 프론트 — "ICC 테이블" 뷰 (신규 nav 탭)
- 그래프 선택 → bake → 표: **경계 · 정의(GSSP/GSSA) · 연대(Ma) · 불확실성 · 출처**, 오래된→젊은 정렬.
- 불확실성은 fidelity 별 표기(exact=오차 없음 / ±budget(σ) / 95% HPD). `example-icc-partial` bake 시
  base-proterozoic 2500(GSSA) · base-cambrian 538.8 · base-triassic 251.9 의 미니 ICC.

## 검증
- `bake_graph` 서비스 + HTTP 엔드포인트 테스트(`test_bake_graph_produces_icc_table`) — 3경계 스냅샷, 재-bake 멱등.
- `pytest` **64 passed** · 프론트 빌드 클린.

## 다음
- **ICC 나머지 경계 채우기**: ICS 공식 chart(i-c-stratigraphy/chart `chart.ttl`)를 참조해 나머지 경계를
  고정값 **데이터 노드**로 시드(→ 037). "기존 데이터=데이터 노드, 예제 3개=편집 파이프라인" 구조 확장.
- `_certify` 층서순 정합(현재 게이트웨이 나열 순서 스텁).
