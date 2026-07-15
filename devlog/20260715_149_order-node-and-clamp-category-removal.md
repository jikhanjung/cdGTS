# 20260715_149 — `order` 노드 제거 → `clamp` 카테고리 소멸

> 성격: **정리(scope-down).** [devlog 135](20260711_135_clamp-scopedown.md)(clamp 축소)의 **미완 잔재 회수**.
> 계기: [노드 매뉴얼 자동 생성](20260715_R05_correlation-provenance-depth.md)(0.1.66)이 *"어떤 그래프도 쓰지 않는 타입 4개"*
> 를 표면화 — 사용자 판단: **`order` 는 정리, 나머지 3개는 존치.**

## 1. 왜 지금

devlog 135 는 "**order 제약 = order 엣지**"로 결정하고 `graph/models.py` 에 그렇게 적어두기까지 했다:

```python
ORDER = "order", "order"  # boundary vertical-port connection = order constraint (replaces the order node).
```

*"replaces the order node"* — 그런데 **그 order 노드를 실제로 지우지 않았다.** NodeType·Port·커널·L1 폴백 가지가
그대로 남아, 시드된 어느 그래프도 쓰지 않는 채 1개월 가까이 방치됐다. 매뉴얼이 없었으면 계속 못 봤을 것이다.

> **매뉴얼의 첫 수확**: 만든 목적("무엇이 정말 필요한가")이 만든 당일에 회수됐다.

## 2. 무엇을 지웠나

| 층 | 제거 |
|---|---|
| 시드 | `order` NodeType + Port 2개(`younger`·`older`) — `02_nodes.json` 57 → 54 객체 |
| 커널 | `order_check()` + `KERNELS["order"]` 레지스트리 항목 |
| 게이트 | `_certify` 의 **L1 중간 폴백 가지**(`elif order_nodes:` — mode=hard/warn 판정) |
| 모델 | `NodeType.Category.CLAMP` enum (→ 마이그레이션 `nodes/0004_alter_nodetype_category.py`) |
| 프론트 | 팔레트 그룹 `clamp` · `CdgtsNode` 의 clamp 색(`#a24bd8`) |
| 테스트 | order 커널 5종(`test_kernels.py`) + order 제약 L1 4종(`tests.py`) + 죽은 `_agein` 헬퍼 |

**`order` 가 clamp 카테고리의 마지막 멤버**였으므로 카테고리가 비었고, enum 에서도 뺐다(사용자 결정).
→ 남은 카테고리 = **data · process · reference** 3종.

## 3. L1 게이트가 어떻게 바뀌었나

**전**: order 엣지 > **order 노드** > 게이트웨이 단조 휴리스틱 (3단)
**후**: order 엣지 > 게이트웨이 단조 휴리스틱 (2단)

중간 단은 order 노드 인스턴스가 0개라 **한 번도 안 타던 죽은 가지**다. 판정 결과 변화 없음(실측: 재시드 후
행 수·경계 연대 동일).

## 4. 헷갈리기 쉬운 것 — `clamp` 이 가리키던 세 가지

이 정리에서 **하나만** 없앴다. 나머지 둘은 그대로다:

| 이름 | 무엇 | 이번에? |
|---|---|---|
| `nodes.NodeType.Category.CLAMP` | 그래프 노드 카테고리 | **제거** ← 이번 대상 |
| `releases.Clamp` | 릴리스 층 governance clamp (pin/range/order/freeze) | **존치** — DEMO-ONLY, `seed_demo` 시연용(cycles §12) |
| `engine.kernels.range_clamp` | 절단정규 커널 | **존치** — `releases/services.py` 의 L3b reconcile 이 사용 |

프론트의 `clampZoom`·CSS `line-clamp` 도 무관(수학 clamp).

## 5. 순환 breaker 는 무관함을 확인

`clamp` 카테고리가 cycle-breaker 였다면 제거가 순환 의미를 바꿨을 것이다. 실측: breaker 판정은
**`slug == "joint-inference"` 하나뿐**(`graph/serializers.py:175` · `engine/evaluate.py:201` ·
`graph/models.py:is_cycle_breaker`). docstring 이 "clamp/joint" 라 쓴 건 devlog 135 이전의 낡은 주석 → 함께 정정.

> 그래서 **`joint-inference` 는 인스턴스 0개여도 존치가 맞다** — 유일한 순환 breaker이고, 없으면 DAG 불변식상
> 순환을 끊을 수단 자체가 사라진다. "미사용 = 불필요"가 아닌 사례.

## 6. 남긴 것 (사용자 결정)

- **`joint-inference`** — 위 §5. 유일한 breaker. (⚠️ [R05](20260715_R05_correlation-provenance-depth.md) 는
  "`cross-section-correlation` 소멸 / `joint-inference` 생존"이라 봤는데, 정작 **미사용인 쪽이 `joint-inference`** 이고
  둘은 같은 커널이다 — R05 아크에서 재검토.)
- **`astronomical` · `magnetostratigraphic`** — 아직 안 쓴 여지. data leaf 라 유지 비용이 사실상 0.

## 7. 검증

- pytest **183 → 174** (order 테스트 9종 제거 = 183−9). 회귀 없음.
- 재시드 후 매뉴얼 재생성: **NodeType 16 · 미사용 3** · 카테고리 3종. 경계 연대·행 수 불변.
- ⚠️ **시드 + 마이그레이션 변경** → 배포 시 `--reseed` 필요. `nodes/0004` 는 enum choices 변경만(데이터 무손실).

## 관련

- [devlog 135](20260711_135_clamp-scopedown.md) — clamp 축소(본 정리의 원류) · [cycles §12](../docs/cycles.md#12-재검토-노트-2026-07--clamp는-별도-개념으로-필요한가) 후일담 추가
- [tier-category-model](../docs/tier-category-model.md) §2·§3 — 카테고리 표 갱신(KR/EN)
- [docs/node-manual.md](../docs/node-manual.md) — 이 정리를 촉발한 자동 생성 매뉴얼

---

## Addendum (2026-07-15) — 배포 중 발견: `sync-cdgts-db.sh` 가 테스트 DB 를 깨뜨리고 있었다

0.1.67 배포 중 테스트 DB 가 `database disk image is malformed` 로 두 번 깨졌다. 조사 결과 **`scripts/sync-cdgts-db.sh`
의 버그**였고, 이건 **0.1.60(devlog 144) 버그의 놓친 형제**다.

```bash
CONTAINER="cdgts"                       # ← 웹만
docker compose stop "$CONTAINER"        # 워커는 계속 돌아간다
cp -f "$SNAP" "$DEV_DB"                 # 워커가 쥔 DB 를 통째로 덮어씀
rm -f "${DEV_DB}-wal" "${DEV_DB}-shm"   # 워커 발밑에서 WAL 을 삭제
docker compose up -d "$CONTAINER"
```

compose 에는 `cdgts`(웹)와 `cdgts-worker`(`run_worker` 폴링 루프)가 있고 **둘 다 같은 sqlite 를 WAL 로 연다.**
웹만 정지하면 워커가 DB 를 연 채 남고, 그 상태에서 메인 파일을 교체하고 WAL 을 지우면 워커의 캐시 페이지 상태와
어긋나 btree 가 깨진다. 손상이 `graph_nodeinstance`(워커가 평가하며 읽는 테이블)에 난 것도 정합적.

**두 번의 손상을 모두 설명한다** — 04:00 cron sync(1차)와 그걸 고치려고 돌린 수동 sync(2차). *복구 도구가 재손상의
원인이었다.* prod 는 sync 의 **소스**이지 대상이 아니라 무사(`integrity_check` = ok, 전 구간 확인).

**수정**: `stop`/`up -d` 를 **서비스명 없이**(= 전 서비스). devlog 144 가 `deploy.sh` 의 `up -d cdgts` → `up -d` 를
고칠 때 이 파일의 같은 가정을 놓쳤다.

**대조 — `deploy.sh` 의 pre_deploy 스냅샷은 처음부터 옳았다**: `docker compose down`(전 서비스)으로 writer 를 모두
내린 뒤 `cp` 하고 `-wal`/`-shm` 도 함께 복사한다. 정지 사본이라 안전.

### 교훈

- **"컨테이너 정지 후 파일 교체"는 서비스가 하나일 때만 성립한다.** 워커가 생긴 순간 모든 단일-서비스 가정이 버그가 됐고,
  0.1.60 은 그중 하나만 고쳤다. → 같은 가정을 쓰는 파일을 전수 점검할 것.
- **성급한 자기귀인 주의**: 1차 손상 때 "호스트에서 라이브 DB 를 건드린 내가 유력한 원인"이라 적었으나, 증거는
  시간적 인접성뿐이었고 **틀렸다**. 2차 손상(라이브 DB 를 읽기 전용으로만 건드린 창)이 그 가설을 반증했다.
  다만 그때 세운 규칙(라이브 DB 는 `mode=ro`·`cp` 금지·쓰기는 fresh DB)은 독립적으로 옳으므로 유지.
