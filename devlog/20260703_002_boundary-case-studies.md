# 20260703_002 — 게이트웨이 재해석 + 경계 두 사례 검증

> 브레인스토밍 단계 devlog. 요약 수준.

## 한 일

레이어 모델을 깊게 파고, 실제 경계 두 개로 검증했다.

### 1. 개념 진전
- **중간 티어의 빈 구멍 발견.** Layer 3(국소 age model) → Layer 4(배포) 사이에 **공간·상관(correlation/synthesis)** 이 빠져 있었다. GSSP가 경계를 정의해도 *숫자*는 correlation/보간으로 얻으므로 load-bearing.
- **게이트웨이 재해석.** 레이어를 고정 "단계"가 아니라 **계약(contract)** 으로. 게이트웨이(합의된 고정 타입·버전·인용 단위) 사이를 **자유로운 노드 네트워크**가 채운다. 지저분한 과학(순환·대안모델·확률전파)은 게이트웨이 사이에 가둔다. → 거버넌스 축소, 순환 격리, CD 의미가 또렷해짐. (비유: 컴파일러 IR 체크포인트.)

### 2. 사례 검증 (문헌 확인)
- **case-permian-triassic.md (GSSP형).** Meishan Bed 27c, *H. parvus* FAD(2001 비준). 경계 지점엔 datable 물질이 없어, 재층 bed 25(251.941±0.037)·28(251.880±0.031)을 CA-ID-TIMS U-Pb로 재고 **베이지안 age-depth 모델로 보간 → 251.902±0.024 Ma** ("mathematical construct"). 노드 그래프 포함.
- **case-precambrian-gssa.md (GSSA형, 거울상).** 숫자가 곧 정의(예: Archean–Proterozoic 2500 Ma, 오차 없음). 화살표가 반대 — 경계는 계산의 출력이 아니라 **결정된 입력(leaf)**, 암석을 분류하는 "자". Ediacaran은 이미 GSSP(635.21±0.57, 2004), Cryogenian은 GSSP 전환 추진 중.

### 3. 열린 질문에 반영한 발견
- 중간 티어는 하나가 아니라 **(a) 국소 age-depth 보간 / (b) 섹션 간 상관** 두 성격.
- **경계 게이트웨이 스키마는 다형(polymorphic)** 이어야 — 계산된 분포(GSSP형, ±) vs 결정된 상수(GSSA형, 오차 없음).
- **토폴로지 재배선도 diff/버전 대상** — GSSA→GSSP 전환(Ediacaran 완료, Cryogenian 진행)은 값이 아니라 배선이 바뀜.

## 커밋

- `9b2183f` Add P-T and Precambrian case studies; refine layer/gateway model

## 다음 후보

- 세 번째 "중간형" 사례 — 섹션 간 correlation이 실제 load-bearing한 경계로 티어 (b) 검증.
- 또는 경계 게이트웨이 스키마 초안 스케치(다형 타입 표현).
