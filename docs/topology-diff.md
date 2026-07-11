# 토폴로지 diff

*[English](topology-diff_en.md) · 한국어*

> 상태: **검토 → 스키마에 일부 반영.** [boundary-gateway-schema.md](boundary-gateway-schema.md) §4의
> "토폴로지 diff"를 펼친 것. [node-graph-paradigm.md](node-graph-paradigm.md)의 *"토폴로지도 버전 대상"* 의 구체화.
>
> **[일부 구현됨]** 값·토폴로지 diff 는 릴리스 diff 로 구현됐고, split/merge 계보(delete+add 오인 방지)는
> `chrono.BoundaryLineage` 가 담는다. **shape diff**(§6 의 스칼라→분포, `±0→±nonzero`)도
> `diff_releases` 에 추가돼 세 번째 축으로 표면화된다(Vault → Diff). Cryogenian base GSSA→GSSP
> retype 워크드 예시는 `manage.py seed_demo` 의 `Demo.Cryogenian.GSSA/GSSP` 릴리스 쌍으로 실연.
> 아래는 그 설계 근거(여전히 유효).

## 1. 핵심 통찰 — 값 diff와 토폴로지 diff는 직교하는 두 축

지금까지 상상한 diff는 대부분 **값 diff**였다("이 U-Pb 넣으면 P–T가 251.902 → 251.88"). 그러나:

| 변화 | 값 diff | 토폴로지 diff |
|---|---|---|
| 새 U-Pb로 숫자 이동 | **큼** | 0 |
| **GSSA→GSSP 전환** (예: 2500 유지) | **≈0** | **큼** |
| 같은 숫자를 *다른 모델/데이터*가 산출 | 0 | **큼** |
| stage 분할 | (대응 자체가 없음) | **큼** |

**한 축이 0인데 다른 축이 거대할 수 있다.** GSSA→GSSP는 값은 거의 안 변하는데 숫자의 *의미*가 완전히 바뀐다
(결정 상수 → 노두 파생값). 값 diff만 보면 "변화 없음"이라고 거짓말한다. → 둘은 **따로 보고**돼야 한다.

## 2. "토폴로지"가 걸치는 층위

- **경계/단위 집합 (Layer 0):** stage 신설·분할·병합·개명·폐기, 위계 재배치.
- **정의 타입·마커·노두 (Layer 1):** GSSA→GSSP 전환, 마커 변경, GSSP 노두 이전(캄브리아 GSSP 재검토가 실례).
- **provenance 배선 (Layer 2–5):** 관측 가감, age-model 노드 스왑, correlation 엣지 가감, ModelCandidate 선택, clamp 배치.

거친 층위(차트의 명명된 경계 집합)부터 미세 층위(한 숫자 뒤 provenance DAG의 배선)까지.

## 3. 이건 그래프-diff / 트리-diff 문제다

스칼라 비교가 아니라 **구조 비교**. 값 diff는 "같은 정체성, 다른 숫자"라는 **안정적 대응**을 전제하는데,
토폴로지 변화가 그 전제를 깬다:

- stage 분할 시 옛 경계 ↔ 새 경계의 1:1 대응이 없음 → 값 diff는 "split"을 못 보고 "삭제+추가"로 오인.
- 그래서 **안정적 식별자(persistent id)** 가 전제이고, **split/merge는 구조만으로 추론 불가** → 새 경계가
  "나는 옛 경계 X에서 분할됨"이라고 **명시적 lineage를 선언**해야 한다. Git의 rename 탐지와 비슷하되,
  과학에선 이게 **큐레이션된 결정**이므로 추측이 아니라 **기록**돼야 한다.

**연산 분류(edit operations):** create / deprecate / rename / **split·merge** / **rewire** / **retype** / move.

## 4. 표기 — 세 층위

1. **Edit script** — `graph_v1 → graph_v2`를 만드는 타입 붙은 연산의 순서 목록. 기계가독·재현 가능(변경 원장).
2. **2색 합집합 그래프** — 두 버전을 겹쳐 노드/엣지를 added/removed/unchanged로 색칠. 시각화(DAG의 시각적 diff).
3. **의미적 changelog** — "Stage X를 X1/X2로 분할(20xx 비준)", "Cryogenian base GSSA→GSSP 전환". 사람·인용용.

셋은 서로 파생된다 (edit script + lineage → changelog → 시각화).

## 5. 기존 기계와의 연결

- **clamp가 retype의 어휘를 준다.** GSSA = `Clamp{pin}`이므로 **GSSA→GSSP 전환 = clamp 제거 + provenance
  서브그래프 추가 + definition retype.** 토폴로지 diff가 clamp 연산으로 서술된다. ([cycles.md](cycles.md))
  > ⚠️ **재검토(2026-07):** clamp가 축소되면서 GSSA는 이제 `Clamp{pin}`이 아니라 authored `published-age` **leaf** — 따라서 GSSA→GSSP는 "clamp 제거"가 아니라 **leaf 값을 파생 서브그래프로 retype**하는 것으로 읽는다. 근거: [cycles.md §12](cycles.md#12-재검토-노트-2026-07--clamp는-별도-개념으로-필요한가).
- **정합성 게이트 재실행 트리거.** 분할은 순서 집합을, retype은 요구 provenance를 바꿈 → 토폴로지 diff는
  게이트 재검증을 부른다. ([coherence-gate.md](coherence-gate.md))
- **릴리스 매니페스트 diff = 거친 토폴로지 diff** (경계 집합 + selection + clamps). 미세 층위는 provenance 그래프 diff.
  ([versioning-global-vs-per-boundary.md](versioning-global-vs-per-boundary.md))
- **ICC/GTS 또 갈림.** ICC diff(bake) = 값 + 거친 토폴로지(집합·타입). GTS diff(narrate) = 전체 배선 diff까지.

## 6. 워크드 예시 — Cryogenian base 전환 (실제 진행 중)

```
retype:      definition.type  GSSA(720 pin)  →  GSSP(marker + stratotype)
clamp 제거:  Clamp{pin, 720 Ma}  삭제
서브그래프:  + marker, + stratotype, + correlation/age 서브그래프, + ModelCandidate
값 diff(결과): 720 (정확)  →  파생값 ± (불확실성이 '없음 → 있음')
```

미묘한 점: **retype이 값의 *모양*을 바꾼다 — 스칼라(오차 0) → 분포(오차 있음).** 두 스칼라를 비교하는 순진한
값 diff는 이 "±0 → ±nonzero" 변화를 표현조차 못 한다. 스키마의 다형 value(decreed-exact vs
computed-distribution)와 직결.

> **[구현됨]** `diff_releases` 가 `shape_diff` 를 별도 축으로 낸다 — 각 경계의 `BoundaryRecord.uncertainty`
> 를 `exact`/`dist` 로 요약해 모양이 바뀌면(예: `exact → ±0.9 (2σ)`) 기록. Vault → Diff 의 "Shape diff"
> 섹션에 표시. 실연: `seed_demo` 의 `Demo.Cryogenian.GSSA → Demo.Cryogenian.GSSP` diff — retype(정의) +
> 작은 값 이동 + 오차 등장이 **세 축으로 나란히** 보인다.

## 7. 펀치라인 — 변화 = 토폴로지 델타 + 전파된 값 델타

토폴로지 변화는 대개 하류 값 변화를 낳는다(분할·retype이 연대를 바꿈). 완전한 "영향 리포트"는:

> **토폴로지 diff**(무엇이 구조적으로 바뀌었나) → 전파 → **값 diff**(그 결과 어떤 숫자가 움직였나)

**둘이 인과로 합성된다** — 토폴로지 변화가 *원인*, 값 변화가 *결과*. 이게 cdGTS 논지에 필수인 이유: "CI for
science"의 가장 중요한 변화(경계 재정의·stage 분할·모델 스왑)는 값이 아니라 **토폴로지**다. 값 diff만 되면
정확히 제일 중요하고 손으로 추적하기 제일 어려운 변화를 놓친다.

## 8. 스키마 반영

- `identity.lineage` 신설: 버전 간 정체성 계보 — `op: created|renamed|split|merged|retyped|deprecated`,
  `from: [boundary_id]`. split/merge·retype를 **선언**해 diff가 정렬 가능하게. → [boundary-gateway-schema.md](boundary-gateway-schema.md) §2.
- diff는 레코드 필드가 아니라 두 버전 간 **연산**(위 §3 분류)임을 명시.

## 9. 남는 열린 질문

- **식별자 영속성 & lineage:** 안정 id를 누가 부여·얼마나 영구히, split/merge lineage 기록의 형식.
- **토폴로지의 입도:** 같은 변화가 줌 레벨에 따라 값 변화이기도 토폴로지 변화이기도 → 어느 층에서 diff를 정의할지.
- **대규모 재배선 정렬:** id 우선 정렬 + 나머지 휴리스틱 + 미정렬 플래그.
- **selection diff vs 구조 diff:** ModelCandidate A→B 교체를 토폴로지 diff로 볼지 가벼운 selection diff로 볼지.

## 10. 링크

- [boundary-gateway-schema.md](boundary-gateway-schema.md) §2 (`identity.lineage`) · §4
- [cycles.md](cycles.md) — clamp = retype 어휘 · [coherence-gate.md](coherence-gate.md) — 재검증 트리거
- [node-graph-paradigm.md](node-graph-paradigm.md) — "토폴로지도 버전 대상" (원 출처)
- [versioning-global-vs-per-boundary.md](versioning-global-vs-per-boundary.md) — 릴리스 매니페스트 diff
