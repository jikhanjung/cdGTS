# 20260706_081 — period 그룹 안 boundary+unit 교호 (age unit 재귀 세분)

top-level 컬럼(경계+time-period 교호)과 동일한 구조를 period 그룹 **안**에도 내려, 각 age 경계 사이에
age unit 노드를 끼웠다. unit→group 재귀 모델의 다음 층. (설계 P03, 앞선 devlog 079·080)

## 변경 (seed/03_graphs.json)
- **101개 age unit 노드** — 12 period 그룹 각각에 그 period 의 age 들(Cambrian 10 … Cretaceous 12 …). ICS age 수와 일치. unit 총 116(= age 101 + Precambrian 15).
- **order 체인 재배선** — 직접 boundary↔boundary order 엣지 101개 제거, `older.younger→unit.older` + `unit.younger→younger.older` 로 매개(Precambrian·top-level 과 동일 규약). order 엣지 132→233.
- **각 unit `out` → 그룹 내부 merge** — age 밴드가 그룹 output(→컬럼 merge→최종)에 합류.

## age 매핑 (정확성)
- `above`/`below` 는 일부만 채워져 불신뢰 → **경계 노드의 r6(Age) 게이트웨이**로 age 를 얻음(`base-<age>` ↔ unit `<age>`, rank 6).
- gap(older,younger)의 age = older 의 r6 게이트웨이 단위. coincident period-base(예: base-cambrian≡base-fortunian)도 r6 게이트웨이로 fortunian/induan 등 정확히 산출.
- plain unit 노드엔 unit/lower/upper FK 없음(그건 NodeGroup 필드; NodeInstance 확장은 migration 필요 → 보류) → Precambrian unit 과 동일하게 **label-only**. chrono 정체성은 경계 게이트웨이가 담당.

## 무결성
- Neogene 만 pub-neogene↔pub-aquitanian zero-width(coincident 23.03) gap 정상 스킵 — aquitanian 은 pub-aquitanian gap 에서 생성(무손실).
- cert L0~L2 pass(unit 매개 order 체인 정상) · bake 177 · 차트 rank 전부 불변(타일링은 게이트웨이 기반). pytest 91 passed.

## 다음 (선택)
- age unit 배치 정돈(현재 멤버 경계 열 오른쪽 x+190 근사).
- unit→group 재귀 다음 층(Precambrian unit 세분, epoch 층 명시).
- NodeInstance 에 unit/lower/upper FK(정본 바인딩) — migration 동반.
