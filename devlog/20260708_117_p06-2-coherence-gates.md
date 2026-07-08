# 20260708_117 — P06.2 공분산 인지 정합성 게이트 (L0 · L1b · L2)

[P06](20260708_P06_arc-a-science-engine.md) 2단계. P06.1 공분산 백본을 `_certify` 에 배선 —
게이트가 진짜 구조·순서·지속시간을 판정하고, 공유 계통이 순서 해상도를 좁힌다. **사용자 가시**(Results 패널 경고).

## 백엔드 (engine/evaluate.py)

- **L0 구조**: 하드코딩 `"pass"` → `find_unbroken_cycles`(graph.dag 재사용)로 실검사. breaker(clamp/joint-inference)
  안 지나는 순환 남으면 **fail**.
- **`duration_gate(unit_dist, rank_of)`** 순수 함수 추출(DB 불요) — rank 별 base 타일링:
  - **L2**: 인접 base 점추정 duration ≤ 0(퇴화/영-길이) → **fail** (기존 동작 보존).
  - **L1b**: 인접 두 경계의 **공분산 인지** 지속시간이 2σ 안에서 ≤0 가능(gap < 2σ_gap, `duration_stats`) →
    **warn**("순서 통계적 미해결"). 공유 계통(P06.1)이 σ_gap 을 줄여 겹침을 해소.
- `checks` 에 `L1b` 키 + `notes[]`(사람용 경고 문구) 추가. warn 은 `passed` 를 떨어뜨리지 않음.

## 프론트

- **ResultsPanel**: consistency 배지가 pass/**warn**/fail 3색 + 체크별 칩(L0·L1·L1b·L2·L3) + `notes` 경고 줄.
  warn 이면 passed=True 여도 배지가 amber(기존엔 pass 로만 보임).
- **Editor** status line: consistency 를 fail/warn/pass 로 정확히(기존 pass/warn 이분 → 3분).

## 검증

engine/test_kernels.py +5 (duration_gate: 분리 pass · degenerate fail · 2σ 겹침 warn · 공유성분 해소 · rank 격리).
전체 **pytest 130 passed**. 시드 그래프는 여전히 L0/L2 pass.

## 다음 (P06.3)

L3 reconcile = authored `releases.Clamp`(pin/range/order/freeze)를 평가·게이트에 배선(값 이동 = GTS/narrate 계약).
