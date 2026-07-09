# 20260709_125 — retype diff 실데모 (shape 축 + Cryogenian GSSA→GSSP)

TODO 오래된 항목 **retype diff 실데모**(devlog 030 메모 이월). Cryogenian base GSSA→GSSP 전환을
릴리스 diff 로 실연 — 그 과정에서 diff 엔진에 **제3의 축(shape)**을 추가해 topology-diff.md §6 이
지적한 "순진한 값 diff 가 못 잡는 변화"(±0→±nonzero)를 실제로 표면화.

## 왜

topology-diff.md §6 핵심: GSSA→GSSP retype 은 **값을 거의 안 바꾸면서 값의 *모양*을 바꾼다** —
스칼라(오차 0) → 분포(오차 있음). 종전 `diff_releases` 는 `value_ma`(값) 와 `definition_type`(retype)
만 비교해 이 shape 변화를 표현조차 못 했다. `BoundaryRecord.uncertainty`(Distribution) 필드는 이미
있었으나 diff 가 안 읽었음.

## 무엇을

- **diff shape 축**(`releases/services.py`)
  - `_uncertainty_summary(rec)` → `(kind, label)`, kind ∈ {none, exact, dist}. exact = 오차 0,
    dist = ± 요약("±0.9 (2σ)" / "95% HPD ±0.6").
  - `diff_releases` 반환에 `shape_diff` 추가 — 공유 경계의 모양이 바뀌면
    `{boundary, from, to, from_kind, to_kind}`. `_diff_summary` 에 `reshaped` 카운트,
    `affected_boundaries` 에 shape 경계 포함(verify/propose 로 흐름).
- **seed_demo 파트 3**(`releases/.../seed_demo.py`) — 멱등 retype 릴리스 쌍:
  - `Demo.Cryogenian.GSSA` : base-cryogenian = 결정 GSSA(720 Ma, exact). 이웃(tonian/ediacaran) 동일.
  - `Demo.Cryogenian.GSSP` : 같은 경계를 섹션 기반 GSSP 로 retype — 값 720→719.5(작게 이동),
    오차 exact→±0.9(2σ), method decreed→local-interpolation. **숫자는 예시**(실제 GSSP 는 진짜 보간;
    여기 시드 안 함) — note/docstring 에 명시.
  - diff A→B → topology(retype) + value(Δ-0.5) + shape(exact→±) 세 축이 나란히.
- **프론트**(`ReleasesDiff.jsx` + css) — Value diff 와 Topology diff 사이에 **"Shape diff"** 섹션
  (`reshape` 배지, `from → to`). Vault → Diff 에서 세 축을 함께 봄.
- **문서**(topology-diff.md/_en) — §6·상단 상태에 shape 축·데모 구현 반영(한/영 쌍).

## 검증

- 신규 테스트 통과: `test_shape_diff_detects_uncertainty_appearing`(exact→dist 세 축),
  `test_shape_diff_empty_when_shape_unchanged`(exact→exact 무변), `test_seed_demo_retype_pair`(멱등+세 축).
- dev DB(`/srv/cdGTS`)에 `seed_demo` 실행 → diff 확인:
  ```
  TOPO  [{boundary: base-cryogenian, op: retype, from: GSSA, to: GSSP}]
  VALUE [{boundary: base-cryogenian, from: 720.0, to: 719.5, delta: -0.5}]
  SHAPE [{boundary: base-cryogenian, from: exact, to: '±0.9 (2σ)', from_kind: exact, to_kind: dist}]
  ```
- 프론트 `npm run build` 정상.

## 메모

- retype 데모는 릴리스 쌍(BoundaryRecord)으로 구성 — provenance 서브그래프(marker/stratotype/correlation)
  까지 실제 노드로 그리는 건 별도(선택). 지금은 diff 가 보여주는 "정의·값·모양" 세 축이 목적.
- shape_diff 는 verify(graph vs baseline)에도 자동 흐름 — 편집이 경계 오차 모양을 바꾸면 CI diff 에 뜬다.
