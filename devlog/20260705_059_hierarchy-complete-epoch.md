# 20260705_059 — 계층 완성 ② Epoch + 전 ICC 재구성

> [056](20260705_056_age-groups-all-periods.md)(전 period age) 이후 2단계. **조립 그래프가 전 175 ICC 경계를
> 재구성** → 공표 릴리스와 완전 대칭(Eon 4·Era 10·Period 22·Epoch 37·Age 102).

## 한 일

### 데이터 정리 (`seed/01_chrono`)
- **early-triassic orphan 제거** — 중복(base None) 유닛. induan 을 chart.ttl 정본 `lowertriassic` 로 재부모.
  units 176→**175**. 유닛 rank 오름차순 정렬(자기참조 parent FK 로드 순서 보장).
- **Carboniferous 계보** — Mississippian/Pennsylvanian(subperiod, 미시드) 아래 epoch 6개를
  carboniferous 로 재부모 → Carboniferous age(6)도 그룹화.
- **이름 공백 보정 26건** — chart.ttl 파생 CamelCase("LowerTriassic"→"Lower Triassic",
  "CambrianStage10"→"Cambrian Stage 10"). Epoch 가 차트에 노출되며 눈에 띔.

### Epoch 계층 + 타일링 폐합 (`seed/03_graphs`)
- **Epoch = 노드 없이 게이트웨이로.** epoch base = 그 첫(가장 오래된) age base 와 일치 →
  일치 age pub 노드에 `base-<epoch>-gw` 만 추가(25개). 새 노드 0.
- **첫 age/epoch 게이트웨이(23개).** 각 period 의 첫 age/epoch 는 base=period base 인 **coincident 경계**
  (하나의 GSSP 가 base-triassic ≡ base-lowertriassic ≡ base-induan 을 동시 정의). period 산출노드에 등록.
  → finer 컬럼 밴드가 period 경계에서 **닫힘**. (없으면 이전 period 마지막 밴드가 P–T 경계를 넘어
  Induan/Lower Triassic 을 삼켰다 — step 1 age 컬럼에 있던 버그.)

## 결과
- example-icc-partial: 노드 **270**·게이트웨이 152→**175**·그룹 **12**. cert L1·L2 pass.
- **bake 120→175 = 전 ICC 경계.** 그래프-bake 차트 = 공표 릴리스와 동일 5 rank(37 epoch·102 age).
- 회귀 가드: Induan[250.8–251.9]·Lower Triassic[247–251.9] 등장, Changhsingian/Lopingian 이 251.9 에서 폐합.

## 검증
- `pytest` **81 passed**(bake 175·5 rank·타일링 폐합·계층 재구성·계보 테스트 갱신). 마이그레이션·프론트 무관.

## 남은 것
- Mississippian/Pennsylvanian **subperiod** 는 여전히 미표현(계보만 우회). 진짜 6-rank(subperiod 포함)는 별도.
- 중첩 노드그룹(Period⊃Epoch⊃Age 시각적 3단)은 [057] 한계대로 미지원.
