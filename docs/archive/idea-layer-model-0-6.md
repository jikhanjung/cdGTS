# [보관] 데이터 모델 — 선형 계층 구조 Layer 0–6 (원래 브레인스토밍)

> **보관 문서.** 원래 `idea.md` §5의 데이터 모델. 구현에서 이 선형 레이어는 **티어(registry/graph/release) ×
> 카테고리(data/process/clamp) + 16개 노드 타입**으로 접혔다. 레이어 번호는 이제 **읽기 순서(서사)**로만 유효하다.
> 현행: [../tier-category-model.md](../tier-category-model.md) · [../concept-map.md](../concept-map.md) · [../idea.md](../idea.md) §5.

데이터를 다음 계층으로 나눈다. 상위 계층은 하위 계층으로부터 파생된다. (당시 참고: 이 계층 구조는
node-graph-paradigm 에서 노드 그래프(DAG)로 재해석된다 — Layer 2 = 데이터 노드, Layer 3~5 = 프로세스/모델 노드,
Layer 6 = 그래프 평가 결과.)

### Layer 0 — 명명 / 계층 (Nomenclature)
- 이중 체계: 연대층서 (Eonothem/Erathem/System/Series/**Stage**) ↔ 지질연대 (Eon/Era/Period/Epoch/**Age**). 같은 경계를 다른 이름으로 부르는 관계이므로 명시적으로 연결.
- 명명 체계 자체도 개정 대상 (스테이지 신설/분할 등). → 버전 관리 대상.

### Layer 1 — 경계 정의 (Boundary definition)
- **GSSP** (Phanerozoic): 물리적 노두, 마커(생물/화학/자기), 위치, ICS **비준 연도**. 경계는 "지점"으로 정의되고 연대는 파생값.
- **GSSA** (Precambrian): 물리적 노두 없이 **약속된 숫자 연대**로 정의.
- → 이 둘은 데이터 모델에서 근본적으로 다른 타입.

### Layer 2 — 원시 관측 (Primary observations) ← *continuous integration의 대상*
- 방사성 연대측정 (U-Pb, Ar-Ar …): 시료, **방법, 사용한 붕괴상수, 실험실, 오차(2σ)**, 층서적 위치.
- 천문연대 (astrochronology / cyclostratigraphy), 자기층서, 생층서 존(zone) 등.
- 각 관측은 **불변(immutable) · 인용 가능(cited)** 한 "사실". 학자가 추가하는 것은 여기.

### Layer 3 — 연대 모델 (Age model / method)
- Layer 2의 앵커들을 스플라인 / 베이지안 age-depth 모델 등으로 종합해 경계 연대 + 불확실성을 **산출**.
- 붕괴상수 재보정 같은 방법 변경이 반영되는 곳.

### Layer 4 — 상관 (Correlation)
- 서로 다른 노두(section)의 층서를 bio/chemo/magneto-strat로 **상관(correlate)** 해 엮는다. GSSP 지점이 датable하지 않을 때 숫자는 다른 지역에서 이 상관을 타고 온다 → 곁다리가 아니라 **load-bearing**. 사례: [../case-cambrian-base-correlation.md](../case-cambrian-base-correlation.md).

### Layer 5 — 전역 종합 / 정합성 게이트 (Global synthesis / coherence gate)
- 상관된 근거를 종합해 (a) 각 경계의 숫자+불확실성을 내고, (b) 경계들이 **전 지구적으로 정합**(단조 순서·지속시간·상관오차)하도록 만든다. 이 정합성 검사의 핵심 메커니즘이 **정합성 게이트**. 상세: [../coherence-gate.md](../coherence-gate.md).

### Layer 6 — 배포된 시대표 (Published timescale)
- Layer 1 + 5의 산출물. Fixed version으로 릴리스 (ICC vXXXX / GTSXXXX에 대응). ICC = bake, GTS = narrate.

---

### 이 모델이 구현에서 어떻게 접혔나

- **Layer 2 (원시 관측)** → **data 카테고리** 노드: `radiometric-uPb` · `astronomical` · `biostratigraphic` · `magnetostratigraphic` · `published-age`.
- **Layer 3–5 (모델·상관·종합)** → **process 카테고리** 노드: `age-depth-model` · `cross-section-correlation` · `calibration-transfer` · `joint-inference` · `boundary` · `unit` · `merge`.
- **Layer 1의 GSSA/GSSP 고정, Layer 5의 정합성 pin** → **clamp 카테고리** 노드: `pin` · `range` · `order` · `freeze-version`.
- **Layer 0 (명명)** → registry 티어(`chrono` 앱: Boundary/Unit 이중 명명).
- **Layer 6 (배포)** → release 티어(bake/narrate, `releases` 앱).
