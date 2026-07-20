# R06 — GTS2012 코퍼스(32장) vs 현재 구현 대조 리뷰

**날짜**: 2026-07-20 · **대상**: `docs/GTS2012_Chap*_요약.md` 32개 전장 × cdGTS **v0.1.70** as-built
**방법**: 32장을 주제별 7개 그룹으로 병렬 정독(각 그룹에 구현 capsule 제공) + Anthropocene(Ch32) 직접 정독 + `releases/services.py`·`Editor.jsx`·seed·NodeType 실측. 결과를 본 문서로 종합.

> ⚠️ **방법론 주의.** 이 요약들은 GTS2012의 2차 한국어 요약이며, 여러 장(특히 Ch16~18, 그리고 19·20 §45~46 등)에 **"cdGTS 관점 데이터 모델링" 절이 이미 포함**돼 있다. 즉 이 코퍼스는 cdGTS 프로젝트를 염두에 두고 작성됐고, 아래 gap 상당수는 그 요약들이 이미 지적한 것을 **독립 확인·통합**한 것이다(순수 외부 비판이 아님). 그 modeling 절들은 미구현 프리미티브의 사실상 스펙 초안으로 재사용 가치가 있다.

---

## 한 줄 결론

cdGTS는 GTS 구성의 **철학**과 **쉬운 경계 사례**는 충실히 구현했으나, GTS2012의 숫자 대부분을 실제로 만들어내는 **어려운 방법론**은 대부분 *선언되었으나 미구현*(astronomical·magnetostratigraphic 타입)이거나 *아예 부재*(생층서 composite + 스플라인, 상관신호/기준곡선 프리미티브)다. 단 두 지점에서는 cdGTS가 GTS2012보다 **원리적으로 더 옳다**(오차 공분산 모델 · retype/거버넌스).

---

## 1. cdGTS가 제대로 잡은 것 (COVERED)

| 영역 | 근거 장 | 평가 |
|---|---|---|
| 전체 아키텍처·철학 | Ch1·2 | GTS를 버전화·provenance 모델로 보는 것, registry→graph→release, "정의 vs 파생 연대" 분리, GSSP/GSSA 이중성, ratification — Ch1·2가 사실상 cdGTS의 헌장. |
| GSSP + 국소 보간 사례 | Ch24·25 | **Permian–Triassic(Meishan)** = 진짜로 충실. Bed 25/28 U-Pb ash 브래킷 → 국소 age-depth 보간 = example ②/④ 그대로. |
| 상관 주도 단일 경계 | Ch19 | **Base of Cambrian**(BACE δ13C + U-Pb + cross-section-correlation + calibration-transfer → T. pedum GSSP) = 충실. |
| 내부/외부 오차 구분 | Ch6·14 | `calibration-constant`의 σ를 shared_component로 태깅하는 공분산 백본이 internal/external을 포착 — "duration은 internal만, 절대연대는 external 필요"까지. **GTS2012의 독립오차 Monte Carlo보다 오히려 더 정확**(Ch14 스스로 상관 systematic을 과소전파한다고 인정). |
| retype/topology diff | Ch16~18·30 | 선캄브리아 GSSA→GSSP · **Quaternary Gelasian/Vrica 재배치**(점·연대 불변, 소속 엣지만 rewire) = cdGTS `diff_releases` topology retype의 교과서. |
| 거버넌스/CI | Ch32 | **Anthropocene** propose→ratify + 다중 후보 GSSP = P05(fork/propose/ratify)가 이례적으로 잘 맞음. |

## 2. 핵심 격차 — cdGTS는 *쉬운* 경계를 모델링하지만, GTS2012의 실제 숫자 생성 기계는 다르다

### (a) Ch14 전역 joint 스무딩 스플라인 ↔ cdGTS 국소 subgraph+merge
GTS2012는 한 구간의 *모든* 경계 연대를 **공유 상대축 위 하나의 가중 3차 스무딩 스플라인**으로 공동 추정(SF는 leave-one-out CV, 95% CI는 MC 10,000회, 재적합마다 단조성 강제). cdGTS는 경계마다 독립 subgraph로 유도하고 `merge`는 통계결합이 아니라 기하 타일링(age→period→era→chart). **cdGTS 스플라인 커널은 존재하나 시드 age-depth는 전부 `method="linear"`**, 전역 joint 추정기 없음(`joint-inference` 미사용, L3·full-joint·composite-scale 로드맵). → **GTS2012 숫자가 실제로 만들어지는 방식과의 최대 격차.** (cdGTS의 L2 게이트 = duration>0는 Ch14의 단조성과 같은 물리 제약을 *사후 검사*로 인코딩 — fitting 내 제약이 아니라 사후 검출.)

### (b) 생층서 composite scaling(CONOP/RASC) — 없는 x축
Ch3, 그리고 **Ordovician·Silurian·Devonian·Carboniferous·Permian 숫자 스케일의 뼈대**. 수천 taxa × 수백 섹션(예: Ordovician 512섹션/2000+taxa, Donets 2641종/5282이벤트) → ranking(이벤트 순서)→scaling(간격) → composite 좌표 → dated ash에 rubber-band → 스플라인. cdGTS엔 **biozone·occurrence·taxon-concept·composite-scale 프리미티브가 전무**(R05 composite-scale 계획, 미구현). `cross-section-correlation`이 이 전 층위를 엣지 하나로 추상화. → Cambrian(쉬운 상관)과 실제 Ordovician 재구성은 *스케일 차이가 아니라 방법 차이*: "correlation-driven single boundary" vs "composite-driven whole-period joint calibration".

### (c) 천문·자기층서 — 타입은 있는데 커널이 없다
`astronomical`·`magnetostratigraphic` NodeType은 **존재하나 어떤 시드에서도 미사용**. 그런데 **Neogene ATNTS(스케일 전체가 궤도 튜닝, GSSP가 곧 cycle node)·후기 Triassic Newark·Jurassic 405kyr·Cretaceous cycle-count·M/C-sequence 자기이상** — 즉 **중생대~신생대 숫자 백본 전부**가 이것. cdGTS는 증거를 *명명*할 뿐 연대를 *계산*하지 못함.
- 필요 ①: **천문튜닝 커널**(process 신형). floating 주기수 × 주기길이 = 매우 낮은 σ의 *duration* 성분 + anchor에서 상속된 (큰) *절대위치* 성분. 이 2부분 불확실성이 **shared_components 선형 공분산 백본에 자연 매핑**(anchor 오차·miss-one-cycle 오프셋 = 완전상관 shift). 경쟁 튜닝 = merge/joint-inference로 들어가는 병렬 노드(덮어쓰기 금지).
- 필요 ②: **자기층서 상관→해양이상거리→확장속도→연대 체인**. GPTS 연대모델은 구조상 age-depth-model과 동형(이상거리↔깊이, 확장속도↔퇴적률, tie-point 스플라인/MC 이미 지원). polarity 계열은 본질적으로 order-edge 사슬(L1에 맞음). 빠진 건 그 아래 chron registry + local-zone→global-chron 상관 가설 층.

### (d) 일반화된 "상관신호/tie-point" + "기준곡선" 프리미티브
Ch7~13(Sr·Os·S·O·C 동위원소·시퀀스·식물층서)이 전부 같은 형태: 측정신호→선별/보정→국소프로파일→인식된 feature(excursion/surface/datum)→섹션간 상관(confidence)→독립 보정으로 연대 전이. cdGTS는 마지막 두 단계만, 그것도 손으로 짠 엣지로 보유 — **δ13C BACE가 손으로 만든 유일 인스턴스**(특수 사례가 아니라 *우연히 하드코딩된 한 멤버*; Ch11이 δ13C를 최다 사용 상관도구로 확인). R05의 tie-point는 너무 좁음 → subkind(동위원소 excursion·시퀀스면·bio-datum)를 갖는 **1급 correlatable-feature 노드**로 일반화해야 Sr/Os/S/O/C/biozone/시퀀스면이 한 기계로 통합.
- 별도 필요: **버전화·역함수 가능한 "기준곡선" 객체**(Sr LOWESS·S barite·O LR04 stack). 연속 Age↔value 보정함수로, **비단조→다중해 모호성**과 **기울기 지배 해상도**(평탄 구간은 분석정밀도 무관하게 무용)를 담아야 하며, 그 곡선이 의존하는 경계연대가 바뀌면 재계산되는 피드백까지. age-depth-model 옆에 위치하되 tie-point와는 다른 타입.

## 3. 모든 장이 만장일치로 요구하는 교차 역량 격차

1. **릴리스 *내부*의 병렬 경쟁 가설(branching)** — 가장 일관된 요구. Ediacaran EN2 vs EN3 세분, Triassic Option 1 vs 2 연대모델, Jurassic seafloor vs deep-tow, Os K–Pg 2단계, 시퀀스층서 학파, Anthropocene 3후보(그림 32.2/27절 boundary hypothesis graph). cdGTS는 릴리스*간* 선형 diff는 있으나 **덮어쓰지 않고 나란히 유지하는 intra-release 분기**가 없음.
2. **해석/보정 사슬 provenance** — measured→보정→파생(δ18O: 측정→vital-effect 보정→온도; Os 측정→initial). L0–L5 fidelity 래더는 "얼마나 아는가"는 담지만 "raw/보정/파생 어느 형태인가"·"한 측정에 N개 해석"은 못 담음.
3. **R04 L2 상수-값 캐스케이드** — FCs/붕괴상수 값 변경 → 의존 연대 rescale(Ch6 §20 핵심). cdGTS는 σ(공분산)는 공유하나 값 의존은 미구현 → "상수 하나 바꿔 전 스케일 재계산" 대표 서사가 아직 실행 불가.
4. **정합성 게이트가 너무 거침** — L1(order)·L2(duration>0)은 좋으나, 실제로 필요한 건 proxy 교차검증 게이트("Sr+U-Pb에서 상관이 살아남나")·fitting 내 단조성(Ch14는 SF를 올려 시간역전 제거)·cycle-count 일관성.
5. **경계 ≠ 기후사건 ≠ proxy 반응**(lead/lag 관계; E/O GSSP≠Oi-1, MIS 5e vs Eemian ~6kyr) · **dating leaf의 방법 semantics**(14C 죽음 vs OSL 마지막 빛 vs U-Pb 결정화; max/min/syn-depositional/direct 제약역할). 현재 `radiometric-uPb`는 이미 해석된 분포만 보유, Ar/Ar·Re-Os는 별도 타입 없이 뭉뚱그려짐(방법별 external-error 구조 손실).
6. **GSSP provenance의 다층 버전화** — 물리적 점 / 원래 의도한 marker / 현재 최선 상관 / review status를 별개 객체로. Silurian(GSSP≠의도 biozone; Wenlock 이중 상관; Telychian mélange 의혹; turriculatus→guerichi 개정)·Devonian(Givetian 무앵커 → 직선보간 예외; SHRIMP/TIMS ~1.3% 편차)이 강하게 요구. cdGTS는 GSSP를 단일 파생연대로만 취급.

## 4. 도메인별 충실도 스코어카드

| 도메인 | 판정 | 이유 |
|---|---|---|
| 선캄브리아(16~18) | **개념 최강 / 인스턴스 최약** | GSSA leaf+retype이 정의적 특성을 우아하게 포착; 세 요약이 cdGTS 스키마를 재유도. 단 증거 substrate(빙성퇴적·동위원소곡선·correlation 가설·geochronologic-role 타이핑·proposal-status lattice) 전무. **Cryogenian base retype은 2024/25 실제 비준** — 로드맵 데모가 실사건 retrodiction. |
| Cambrian base | **COVERED** | flagship, 충실. 단 10-stage 내부구조·excursion 5종·provincialism은 미모델. |
| Ord·Sil·Dev(19~22) | **MISSING** | CONOP composite + 스플라인 — 근본적으로 다른 파이프라인. order-edge scaffolding만 존재. |
| Carb·Perm(23·24) | **PTB 외 MISSING** | 동일 CONOP-9 + rubber-band + 스플라인 백본. PTB만 COVERED. |
| Tri·Jur·Cret(25~27) | **MISSING** | astro+magneto 백본(미사용 타입) + 경쟁 모델 + superchron(증거가 국소적으로 무정보). "타입은 있는데 아무것도 안 함"이 가장 아픈 구간. |
| Pg·Ng·Q(28~30) | **혼합** | Neogene ATNTS=astro → MISSING(가장 뚜렷); Paleogene 하이브리드 구간선택; **Quaternary 재배치=topology COVERED**. |
| Anthropocene(32) | **원리상 COVERED** | P05 거버넌스 최적합; forcing→response→record 인과사슬·병렬 boundary 가설은 미구현. |
| 행성(15)·인류(31) | **범위 밖** | 인접 모듈. 단 둘 다 "같은 데이터, 다중 모델연대" = 병렬가설 요구를 외부 검증. |

## 5. 우선순위 권고 (레버리지 순)

1. **천문튜닝 커널 + 자기층서 상관 체인** — 중생대~신생대 숫자 백본 전체를 잠금해제. 미사용 타입 두 개에 커널을 *배선*하는 작업(어휘는 이미 있음). Neogene ATNTS가 최고 레버리지 캡스톤; Ch28의 24-vs-25 cycle 경쟁가설이 딸린 검증셋.
2. **상관신호/tie-point 일반화(R05 확대) + 기준곡선 객체** — δ13C 하드코딩 은퇴, Sr/Os/S/O/C/biozone/시퀀스면을 한 기계로. 동시에 Ch2/Ch3의 correlation-hypothesis 프리미티브도 해결.
3. **생층서 composite-scale 노드 + Ch14 스무딩-스플라인 보정 노드** — 하부고생대~석탄/페름 재구성의 관문. 기존 스플라인 커널을 구간-수준 joint fit에 배선.
4. **릴리스 내 병렬 모델 분기 + R04 L2 값 캐스케이드** — 경쟁가설 보존과 "상수 바꿔 재계산" 서사를 실행 가능하게.

## 6. 큰 그림

cdGTS의 **그래프 패러다임은 선캄브리아와 거버넌스에서 진짜로 빛나고**, 오차 공분산 모델은 GTS2012보다 원리적으로 우수하다. 하지만 현재 세 경계(P–T·Cambrian base·선캄브리아 GSSA)만 실제 provenance를 가지며, 이들은 모두 *가장 유리한* 사례(깨끗한 GSSP+국소보간, 단일 상관, 결정 숫자)다. 현생누대 대부분의 숫자를 실제로 만드는 네 방법 — **CONOP 생층서 composite · 천문튜닝 · 자기층서 · 전역 joint 스플라인** — 은 어휘만 있거나 아예 없다. **flagship이 쉬운 이유가 곧 나머지가 어려운 이유다.**

## 7. 후속 연결

- 로드맵상 **R05**(상관 provenance = tie-point/composite-scale)와 **R04 L2**(상수→값 rescale)가 위 (b)(c)(d)와 3-③을 직접 겨냥 — 본 리뷰는 그 우선순위를 데이터로 뒷받침한다.
- 각 요약의 "cdGTS 관점 데이터 모델링" 절(Ch16 §30~35 · Ch17 §23~27 · Ch18 §25~26 · Ch19 §46 · Ch20 §45 · Ch32 §26~32)은 미구현 프리미티브의 **스펙 초안**으로 재사용 가능.
- 참고: `docs/GTS2012_*`는 저작권 자료 기반이라 `.gitignore` 처리(로컬 참고용) — 본 리뷰는 그 요약을 인용·종합한 2차 산출물이다.
