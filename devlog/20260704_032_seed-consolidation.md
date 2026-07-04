# 20260704_032 — 초기 데이터(seed) 통합 + 자연키 재시드 구현

> 계획 [P02](20260704_P02_seed-consolidation-reseed.md) 실행. 흩어진 앱별 fixture → 단일 `seed/` + `manage.py seed`.

## 한 일

### 자연키 (pk 제거)
- seed 대상 모델 전부에 `natural_key()` + manager `get_by_natural_key()` 추가:
  - chrono: Unit·Authority·Boundary(slug) · BoundaryLineage(boundary,op) · Ratification(boundary,authority,year) · Locality(boundary)
  - nodes: NodeType(slug) · Port(nodetype,direction,name)
  - graph: Graph(slug) · NodeInstance(graph,key) · Gateway(graph,slug) · **Edge(graph,src,src_port,tgt,tgt_port)**
  - releases: ModelCandidate·Clamp(slug) · CandidateOutput(candidate,boundary) · Release(version) · Selection(release,boundary)
- `natural_key.dependencies` 로 덤프/로드 순서 보장. 마이그레이션 불필요(메서드만).

### 통합 seed 세트 (`seed/`)
- `manifest.json`(version **2026.07.0**) + 의존순 4파일: `01_chrono` · `02_nodes` · `03_graphs` · `04_releases`.
- `dumpdata --natural-primary --natural-foreign` 로 재생성 → **pk 0회**(전부 자연키). 정본값 확정:
  - age-depth-model `linear/spline`(bayesian 미구현 → 제외, 나중에 커널과 함께 추가), radiometric-uPb 스키마 채움, example_releases 포함.
- **BoundaryRecord(=bake 산출)는 seed 에서 제외** — 로드 후 릴리스별 bake 로 생성.

### `manage.py seed` 명령 (releases/management/commands)
- `--mode=replace` — seed 범위(+파생물 EvalRun/NodeResult/Cert/BoundaryRecord) flush 후 전체 로드 + bake.
- `--mode=add` — 자연키로 **없는 것만** insert(기존 보존). **그래프/릴리스는 원자 단위**(slug/version 있으면 자식까지 통째 skip),
  레지스트리/후보는 행 단위. `loaddata` 대신 `deserialize` 루프인 이유 = loaddata 는 기존 행을 덮어쓰기 때문.
- `--dry-run` — 트랜잭션 안에서 실제 경로 실행 후 롤백(정확한 미리보기). `--no-bake` 옵션.

### 정리
- 앱별 fixture 4개 폐지(chrono/nodes/graph/releases fixtures/). `FIXTURE_DIRS=[seed/]` 추가.
- 테스트 5개 loaddata 를 seed 파일명(`01_chrono`/`02_nodes`)으로 전환.
- deploy/README 시드 절차를 `manage.py seed` 로 갱신. HANDOFF/TODOs 반영.

## 검증 (로컬 임시 DB)
- **replace**(빈 DB): inserted 96 · bake 2 releases.
- **add 재실행**: inserted 0 · skipped 96 (**멱등**).
- **부분 삭제 후 add**(그래프1+릴리스1 제거): dry-run inserted 15(롤백, 변경 0) → 실제 add inserted 15 · bake 1(**원자 재삽입**).
- **diff**: value_diff 2 · topology_diff 1 (릴리스 Diff UI 데모 정상).
- `manage.py check` 무결 · `pytest` **59 passed**(앱 fixture 삭제 후에도).

## 남은 것 (운영)
- **운영 재시드**: 이 도구를 담은 이미지 배포 후 운영서버에서 `seed --mode=replace` 1회 → 드리프트(빈 스키마·releases 0) 해소.
- 이후 done-log 로 운영 검증 기록. bayesian 은 커널 구현 시 seed 버전 올려 add.
