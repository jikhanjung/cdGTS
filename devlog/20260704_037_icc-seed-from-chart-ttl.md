# 20260704_037 — ICS chart.ttl 로 ICC 경계 시드

> [036](20260704_036_icc-table-bake-from-graph.md) 의 bake-from-graph 위에 **실제 ICC 데이터**를 채운다.
> 출처: [i-c-stratigraphy/chart](https://github.com/i-c-stratigraphy/chart) `chart.ttl` (ICS 2024-12, RDF/Turtle).
> 값은 추측하지 않고 공식 파일에서 파싱 — 도메인 정확성 원칙.

## 스코프 (사용자 지시)

- **Period 이상(Eon/Era/Period) → 네트웍**: 데이터 노드 + 게이트웨이. 예제 3개만 편집 파이프라인.
- **Epoch/Age 이하 → registry 만**: `chrono.Boundary` 로 등록(값은 note), 네트웍엔 안 올림.

## chart.ttl 파싱

- 유닛: `gts:rank` (rank:Eon…Age) · `time:hasBeginning` → 경계 인스턴트.
- 연대: `ischart:inMYA` (base age) · `schema:marginOfError` (±). GSSP/GSSA: `gts:ratifiedGSSP/GSSA`.
- 계보: `skos:broader`. 이름: `skos:prefLabel@en`.
- Sub-Period(2)·Super-Eon(1) 은 5-rank 모델에 없어 제외.
- 검증: base-triassic 251.902±0.024, base-jurassic 201.4±0.2(GSSP), base-cretaceous 143.1(미정),
  base-hadean 4567(GSSA) 등 알려진 값과 일치.

## 한 일

### 새 NodeType `published-age` (category=data)
- 공표 연대 참조 leaf. `category=="data"` 커널이 `params["distribution"]` 를 그대로 출력 → 별도 커널 불필요.
- GSSA/moe 없음 → `exact`, GSSP+moe → `sym ±moe@2σ` (기존 데이터 노드 관례와 동일).

### 시드 확장 (자연키·기존 슬러그 보존)
- `01_chrono.json`: units **12→42** (period+ 30 신규), boundaries **3→175**
  (period+ 33 신규 + finer 139 registry-only). 예제 슬러그(early-triassic·induan·base-triassic…) 그대로.
- `02_nodes.json`: `published-age` 타입 + out 포트.
- `03_graphs.json`: `example-icc-partial` 에 period+ 데이터 노드 33 + 게이트웨이 33 추가.

### 결과
- `example-icc-partial` bake → **36경계 period-level ICC** (예제 파이프라인 3 + 공표값 33).
  base-hadean 4567 … base-quaternary 2.58, 예제(base-triassic 등)는 파이프라인 계산값 유지.
- finer 139 경계는 registry 에만 존재(게이트웨이 없음) — "자료 넣기만".

## 검증
- `pytest` **65 passed**: seed replace 카운트(42/175/13/4), bake 36경계, 예제/공표값,
  finer=registry-only 가드, replace 멱등(self-FK). 프론트 빌드 클린.

## 알려진 한계 / 다음
- 큰 그래프(36 게이트웨이)에서 `_certify` 는 게이트웨이 나열순 monotonicity 스텁 → **warn** 가능.
  층서순 정렬 후 판정 필요(이월).
- period+ 경계 below 는 대부분 null(above=유닛만). 인접 older 유닛 연결은 이월.
- finer 경계 **값**을 릴리스(candidate/selection)로 올려 완전한 공표 ICC 릴리스 만들기(선택).
- 배포: 이 확장은 마이그레이션 없음(데이터만). 운영 재시드는 `seed --mode=replace`(또는 add).
