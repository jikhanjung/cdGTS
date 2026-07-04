# 20260704_P02 — 초기 데이터(seed) 통합 + 버전드 재시드 계획

> 계획(Plan) 문서. 배경 devlog [031](20260704_031_release-0.1.2-prod.md)(0.1.2 배포) 후속 점검에서
> **운영 DB 가 리포 fixture 와 어긋남**을 발견한 데서 출발. 구현 전 방식 확정용.

## 문제 (관찰된 사실)

운영서버(cdgts.paleobytes.info) DB 를 직접 열어 보니 리포 fixture 와 양방향으로 드리프트:

| 항목 | 리포 fixture | 운영 DB |
|---|---|---|
| `radiometric-uPb.params_schema` | distribution+depth 채워짐 | `{}` (비어 있음) |
| `age-depth-model.params_schema` | `linear/spline` + target_depth | `spline/bayesian` (target_depth 없음) |
| releases | example_releases 2건 | **0건** (diff UI 빈 화면) |

**근본 원인**: `deploy/entrypoint.sh` 는 `migrate` 만 실행하고 `loaddata` 를 하지 않는다.
운영 DB 는 최초 배포(0.1.0/0.1.1) 때 한 번 수동 시드된 뒤, 이후 리포의 fixture 변경이 전혀 반영되지 않음.
DB 를 배포에서 분리한(devlog 026) 설계의 의도된 부작용 — **시드는 수동**이어야 하는데 그 절차가 없었다.

또한 초기 데이터가 앱별 fixture 로 흩어져 있어(`chrono/…`, `nodes/…`, `graph/…`, `releases/…`)
"현재 공식 초기 데이터 세트"가 무엇인지 단일하게 가리킬 수 없다.

## 전제 (사용자 확인)

- **아직 정식 사용 전** → 운영 DB 를 갈아엎어도 무방. 지금은 *어떤 seed data 를 넣을지 알아가는 과정*.
- 그래서: 초기 데이터를 **하나로 통합 + 버전 부여**하고, 버전 업 시 두 모드 중 선택:
  1. **replace** — 초기 데이터를 완전히 새로 넣기(기존 seed 제거 후 로드).
  2. **add** — 운영에 이미 데이터가 있을 때, **추가된 초기 데이터만** 넣기(기존 행 보존).
- **add 모드의 pk 충돌 대비**: fixture 에 pk 를 박지 말고 **natural key** 로 넣어 기존 데이터에 안전하게 append.

## 설계 결정

### 1. 통합 버전드 seed 세트

`seed/` 디렉토리에 "공식 초기 데이터" 를 단일 소스로 통합(앱별 fixture 는 폐지 또는 이걸 가리키게):

```
seed/
  manifest.json      # { "version": "2026.07.0", "fixtures": [순서대로] }
  01_chrono.json     # Unit · Authority · Boundary  (+ Ratification/Lineage 있으면)
  02_nodes.json      # NodeType · Port
  03_graphs.json     # 예제 그래프 3종 (Graph+NodeInstance+Edge+Gateway)
  04_releases.json   # ModelCandidate · CandidateOutput · Clamp · Release · Selection
```

- **버전**은 manifest 의 문자열 라벨(예 `2026.07.0`). 로그·표기용. (아래 add 로직은 버전 상태 테이블 불필요 — 자연키 존재 여부로 판정하므로 stateless.)
- **seed = 입력만**. 파생물(`engine.EvalRun/NodeResult/Certificate`, `releases.BoundaryRecord`)은 넣지 않음 — 평가/ bake 가 생성.

### 2. natural key (pk 제거)

`dumpdata --natural-primary --natural-foreign` 로 재덤프하려면 모델에 natural key 지원을 추가.
대부분 이미 유니크 업무키가 있어 간단:

| 모델 | natural key | 상태 |
|---|---|---|
| chrono.Unit / Authority / Boundary | `(slug,)` | 유니크 slug ✓ |
| nodes.NodeType | `(slug,)` | ✓ |
| nodes.Port | `(nodetype_slug, direction, name)` | 유니크복합 ✓ |
| graph.Graph | `(slug,)` | ✓ |
| graph.NodeInstance / NodeGroup | `(graph_slug, key)` | 유니크복합 ✓ |
| graph.Gateway | `(graph_slug, slug)` | 유니크복합 ✓ |
| graph.Edge | `(graph_slug, source_key, source_port, target_key, target_port)` | **유니크 제약 없음** → 아래 3 참고 |
| releases.ModelCandidate / Clamp | `(slug,)` | ✓ |
| releases.Release | `(version,)` | 유니크 ✓ |
| releases.CandidateOutput | `(candidate_slug, boundary_slug)` | 유니크복합 ✓ |
| releases.Selection | `(release_version, boundary_slug)` | 유니크복합 ✓ |

각 모델에 `natural_key(self)` + manager `get_by_natural_key(...)` 추가. FK 는 `--natural-foreign` 로
슬러그 참조가 되어 pk 하드코딩이 사라짐 → **add 시 기존 행에 새 pk 로 안전 insert / 기존은 자연키로 매칭.**

### 3. 그래프는 원자 단위 (Edge 문제 해소)

`Edge` 만 유니크 제약이 없어 자연키가 어색하다. 하지만 **그래프는 통째로 다루는 단위**다
(API 도 PUT 시 topology 를 wholesale replace). 따라서:

- **add 모드에서 그래프/릴리스는 "원자적"**: slug/version 이 없으면 그래프(노드+엣지+게이트웨이) *통째로* insert,
  이미 있으면 *통째로 skip*. 내부 노드/엣지를 부분 병합하지 않는다 → Edge 자연키 불필요.
- Edge 는 그래프 insert 시 부모 그래프 pk 로 함께 들어가므로 자연키 자체가 필요 없음.

즉 seed 는 두 성격으로 갈린다:
- **레지스트리 데이터**(chrono·nodes) — 행 단위 자연키 병합.
- **예제 콘텐츠**(graphs·releases) — slug/version 단위 원자 insert/skip.

### 4. `seed` 관리 명령

```
python manage.py seed --mode=replace     # seed 범위 flush 후 전체 로드
python manage.py seed --mode=add         # 없는 것만 insert (기존 보존)
python manage.py seed --dry-run          # 무엇이 insert/skip/update 되는지 출력만
```

- **replace**: 트랜잭션 안에서 seed 범위 행을 역-의존 순서로 삭제(또는 cascade 활용) → manifest 순서로 로드.
  파생물(EvalRun·BoundaryRecord)은 cascade 로 함께 정리.
- **add**: `serializers.deserialize(use_natural_keys)` 로 객체를 돌며 **자연키 존재 시 skip, 없으면 save**.
  그래프/릴리스는 slug/version 존재 여부로 원자 판정. `loaddata` 를 직접 안 쓰는 이유 = loaddata 는
  기존 행을 *덮어쓰기* 때문(사용자 요구는 "추가된 것만").
- 실행 후 요약 로그: `version 2026.07.0 · inserted N · skipped M · (replace 시 deleted K)`.

### 5. 배포 통합

- `entrypoint.sh` 는 **그대로 migrate 만** (자동 시드는 위험 — 매 배포 덮어쓰기 사고 방지).
- 시드는 **명시적 단계**로 분리. deploy/README 에 문서화:
  - 최초/재구축: `docker compose exec cdgts python manage.py seed --mode=replace`
  - 증분: `… seed --mode=add`
- (선택) `SEED_MODE` env 로 원샷 시드 컨테이너를 두는 방식은 후속.

## 데이터 정합성 결정 (통합 시 확정 필요)

통합 seed 의 정본값을 하나 골라야 함. 드리프트 3건 처리안:

- **radiometric-uPb / target_depth** → 리포 fixture(채워진 쪽)를 정본으로. (운영의 빈 값은 옛 시드 잔재)
- **age-depth-model 스키마** → **`linear/spline` 채택 권장**. 이유: 현재 engine 커널이 linear 보간 + spline MC 만
  구현(`bayesian` 미구현). 운영의 `bayesian` 은 실험적 수기 수정으로 보이며, 미구현 옵션을 UI 에 노출하지 않는 게 안전.
  → **열린 결정**: bayesian 을 로드맵상 유지하고 싶으면 fixture 에 남기되 disabled 표기.
- **releases** → example_releases(ICC-2012→2024 diff 데모)를 통합 seed 에 포함.

## 구현 단계 (승인 후)

1. seed 대상 모델에 `natural_key` + manager 추가 (마이그레이션 불필요 — 메서드만).
2. `dumpdata --natural-primary --natural-foreign` 로 앱별 fixture → `seed/*.json` 재생성(정본값 반영).
3. `seed` 관리 명령 구현(replace/add/dry-run) + 요약 로그.
4. 기존 앱별 fixture 정리(폐지 또는 seed 로 이동), README/HANDOFF/TODOs 갱신.
5. **운영 재시드**: 지금은 전제상 `--mode=replace` 로 깨끗이 재구축. 이후 버전업부터 add 병행.
6. 검증: replace 후 node_types 스키마·예제 그래프·releases 존재 확인 / add 재실행 시 inserted 0 (멱등).
7. done-log(NNN) 로 결과 기록.

## 열린 질문

- age-depth-model `bayesian` 정본 여부(위 참고).
- seed 버전 상태를 DB 에 기록할지(현 설계는 불필요하나, "이 DB 는 seed vX 로 시드됨" 표기가 필요해지면 소형 `SeedState` 1행).
- `chrono.Ratification/BoundaryLineage/Locality` 를 seed 에 포함할지(현재 예제 범위엔 최소 경계만).
