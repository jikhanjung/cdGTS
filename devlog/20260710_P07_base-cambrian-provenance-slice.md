# 20260710_P07 — Base of Cambrian provenance vertical slice (계획)

`docs/base-cambrian-vertical-slice.md` 검토 결과를 실제 변경 대상으로 정리한 계획.
문서의 방향(하나의 boundary를 source→section→horizon→age→correlation→estimate→chart 까지 깊게)은 옳으나,
**문서가 "만들 것"으로 서술한 대부분이 이미 구현돼 있다.** 이 계획은 그 델타만 남긴다.

## 현재 상태 (탐색 실측 · seed/03_graphs.json)

`example-cambrian-base` (예제③) 실배선:

```
oman     [radiometric-uPb] ──data──┐
namibia  [radiometric-uPb] ──data──┼─▶ global-age-model [cross-section-correlation]
siberia  [radiometric-uPb] ──data──┘        │
fad-fortunehead [biostratigraphic] ──calibration-transfer──┘
                                             │
                          gateway base-cambrian-gw ─▶ chrono.Boundary base-cambrian
```

확정 사실:
- **`age-depth-model` 노드 없음** — U-Pb anchor 3개가 correlation 노드로 직접 모임. → horizon depth 를 흘려보낼
  compute 대상이 없음 (Option A 성립).
- **gateway `base-cambrian-gw` 이미 존재** — `global-age-model` 출력 distribution → `base-cambrian` boundary.
  evidence→estimate→boundary seam 은 **이미 작동**. bake 시 `BoundaryRecord`(value_ma + uncertainty Distribution
  + method + references + narrative) 로 동결됨.
- **seed 에 cambrian NodeGroup 없음** — 문서 §8 "Group 15" 는 라이브 에디터 산물. 실제 작업은 *개명*이 아니라
  *명명된 그룹 신규 추가*.

## 검토 결론 — 이미 있는 것 (재구축 금지)

문서 §5·§13.1 제안 node type 대부분이 실재한다:

| 문서 제안 | 실제 |
|---|---|
| Publication / Reference | `reference` NodeType + `cite` 엣지 + `references` 앱(DOI) (devlog 127) |
| Radiometric Age | `radiometric-uPb` (data) |
| Datum / Signal | `biostratigraphic`·`magnetostratigraphic`·`astronomical` (data) |
| Age-depth Model | `age-depth-model` (process, 선형+spline/MC) |
| Correlation / Calibration | `cross-section-correlation`·`calibration-transfer` (process) |
| Boundary Age Estimate | **별도 타입 불필요** — boundary 노드 출력 = Distribution, Gateway→`BoundaryRecord` 로 실현 |
| Boundary | `boundary` 노드 + `nature=boundary` + `chrono.Boundary` |
| Time Period / Span | `NodeGroup(kind=unit)` + `chrono.Unit` + `unit`/`merge` |
| Chart Output | `merge` → ICC chart |

문서 §9 `BoundaryAgeEstimate` 객체도 이미 `Distribution`(L0–L5 fidelity ladder) + `BoundaryRecord` 로 존재하며,
제안 YAML 보다 정교하다. → **§9 재구현 안 함.**

## 진짜 갭 = 두 가지뿐

1. **Stratigraphic Section / Horizon** node type 부재 — provenance 층의 유일한 실제 공백.
2. **computed vs display 값 분리** (`display_value_ma`) — 낮은 우선순위 backlog.

---

## 단계

### P07.1 — Section / Horizon provenance 노드 · 난이도 下 · 스키마 migration 0

**설계 결정(사용자 확정): provenance 노드로 두고 compute 에서 제외.**

- `seed/02_nodes.json` 에 NodeType 2개 추가: `section`·`horizon`, **`category=reference`**.
  - reference 카테고리는 이미 "provenance / citation" 이며 평가에 안 흐름(`compute()` fallback→None, 무해).
  - NodeType 은 DB row → **Django migration 불필요, 커널 변경 0.**
- `example-cambrian-base` 에 section/horizon 노드 추가 후 **`cite` 엣지**(NON_DATA_KINDS, 평가 제외)로 배선:

  ```
  [section] Ara Group (Oman) ──cite──▶ oman
  [horizon] ash-bed @ level ──cite──▶ oman        (params: locality, stratigraphic position; depth 는 메타)
  ... namibia / siberia 동일
  [section] Fortune Head (Canada) ──cite──▶ fad-fortunehead
  ```

- depth 는 노드 승격 안 함(age-depth-model 이 없으므로) — horizon `params` 의 순수 메타데이터.
- 프론트: 팔레트에 section/horizon(reference 계열), 인스펙터에 locality/stratigraphic position 표시. 스키마 아님.

**소수 결정점**: 순수 provenance 배선에 `cite` 재사용(source 가 reference 타입이 아니어도 mechanism 은 동일).
의미 순정성이 나중에 문제되면 `co-location` 을 `NON_DATA_KINDS` 에 추가하거나 전용 `provenance` kind 신설(소규모 후속).

### P07.2 — Publication provenance 심화 · 난이도 下 · P07.1 무관

- `references` 앱에 실제 Reference row 추가(Oman/Namibia/Siberia ash-bed U-Pb 출처, T. pedum FAD 문헌; DOI).
- `reference` 노드 + `cite` 엣지로 anchor/datum 노드에 연결 → provenance seam 완성.
- bake→bibliography(devlog 128) 가 자동으로 이 cite 상류를 `BoundaryRecord.references` 스냅샷에 반영.

### P07.3 — 명명된 evidence 그룹 · 난이도 下

- `example-cambrian-base` 에 `NodeGroup(kind=container, name="Base Cambrian · δ13C calibration")` 추가,
  evidence 노드(anchors·datum·section·horizon·correlation) 를 멤버로.
- 문서 §8 ID 컨벤션은 `key` slug 로: `evidence/base-cambrian/global-d13c-age-model` 등(선택).
- 그룹은 presentation-only(엔진 평탄) → 평가/bake 영향 0.

### P07.4 — 문서 정정 · 난이도 下 · 한/영 쌍

`docs/base-cambrian-vertical-slice.md`(+ `_en` 신규) 를 현실에 맞춤:
- §4 다이어그램을 **compute seam(data 엣지) vs provenance seam(cite 엣지)** 두 축으로 분리 서술.
- §5·§9 를 "이미 있음 / 진짜 갭" 으로 재정리(Boundary Age Estimate·Distribution 이미 실현).
- §12(TSC 차별점) = provenance seam 의 기계적 표현임을 명시.

### (backlog) computed vs display 값 분리

- `BoundaryRecord` 에 `display_value_ma`(release 라운딩) vs `value_ma`(computed) 분리 — release profile 추가 시.
  지금 미착수.

---

## 안 하는 것 (명시)

- `BoundaryAgeEstimate` 신규 node type/객체 — Distribution + BoundaryRecord + Gateway 로 이미 실현.
- age-depth-model / horizon-depth-series compute 배선 — 이 slice 에 age-depth 없음(Option B 는 범위 밖).
- 커널·정합성 게이트 변경 — P06 계열 소관(cross-section-correlation 의 독립가정 등은 P06.4/공분산 이슈).
- version/release graph 다중화 — 문서 §10 대로 이번 slice 범위 밖.

## 권고 경로

**P07.1 → 07.2 → 07.3 → 07.4.** 전부 seed + 프론트 작업, **백엔드 스키마 migration 0 · 커널 0.**
문서가 암시하던 무거운 node type 확장이, provenance 노드 결정 덕에 가벼운 데이터/UI 작업으로 축소됨.
핵심 산출: `example-cambrian-base` 가 source→section→horizon→age→correlation→(gateway)→boundary→chart 로
이어지는 **깊은 provenance graph** 로 완성되고, bake→bibliography 가 그 provenance 를 자동 스냅샷.
