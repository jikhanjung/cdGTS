# 20260712_139 — 공유 보정 노드 + 공분산 배선 L1 vertical slice

[R04](20260711_R04_radiometric-provenance-depth.md)가 그린 "공유 보정 파라미터만 1급으로 올리는 L1"을
실제 노드·커널·데모로 착지시킨 라운드. 방사연대 논문(Schmitz 2012) 검토 → "어느 깊이까지 구현하나" 논의에서
출발해, **공유 계통원을 진짜 노드로** 만들고 두 방사연대가 그걸 소비해 공분산을 얻는 데까지 배선했다.

## 왜 (설계 갈림길)

공분산 자체는 노드가 필요 없다 — `covariance(a,b)=Σ σ_a[ref]·σ_b[ref]`라 같은 ref 문자열만 공유하면 된다.
그래서 두 선택지가 있었다:
- **(A) 노드 안 드롭다운 → ref 문자열만** — 공분산은 되지만 크기(σ)는 연대마다 authored = 매직 스트링의 어휘 버전.
  "상수 한 곳 바꾸면 하류 재계산"·단일 진실원(SSOT)은 못 얻음.
- **(C) constant 노드에서 입력** — ref+σ를 노드에 한 번 authored → 소비 연대가 엣지로 상속. SSOT + 그래프-
  네이티브 전파(증분 엔진이 자동 dirty → diff가 영향 경계 표시) + 프로비넌스가 엣지로 가시.

cdGTS 정체성(모든 게 DAG 노드, 변화가 엣지로 전파)에 맞는 (C)로 결정. 드롭다운은 나중에 그 wire를 만드는
UX로 얹으면 된다.

## 한 일

1. **`calibration-constant` NodeType** (data leaf; params distribution·kind·symbol; out `value`).
   커널 `calibration_constant()`가 출력 불확실성 전액을 자기 자신(ref=symbol)의 `shared_component`로 자동
   태깅(L4 joint 승격). 이미 태그 있거나 불확실성 없으면 원본 통과. — 커밋 `7ab87c0`.
2. **소비자 배선** — `radiometric-uPb`에 `calibration` 입력 포트(distribution·multiple). 커널
   `radiometric_age()`가 보정 입력의 계통 σ를 (a) 자기 marginal budget(systematic)에 제곱합 + (b)
   shared_component로 태깅. **값 불변 = 재계산 아닌 공분산 배선(L1)**. 입력 없으면 기존 불투명 leaf
   그대로(하위호환). data 카테고리지만 compute()에서 slug 특수처리로 early-return 우회.
3. **캡스톤 데모 재구성**(`seed_demo` demo-cov) — 매직 스트링 → 진짜 공유 노드. 경계마다
   `[calibration-constant]→[radiometric-uPb]→[boundary]` 사슬.
   - **shared**: 한 decay-238U 노드가 두 연대에 갈라짐 → 같은 ref → Cov 1.96 → **L1b pass**.
   - **independent**: 각자 다른 노드(ref `decay-238U·A`/`·B`) → Cov 0 → **L1b warn**.
   - 차이가 그래프 구조에 보임(노드 하나 vs 둘). 숫자·판정 종전과 동일 → 기존
     `test_seed_demo_capstone`가 그대로 통합 검증.
4. **문서** — tutorial-science-engine(KR/EN) §2 "공유 태그" → "공유 노드 하나/둘"로 갱신. R04에 L1
   vertical slice 착수·구현 반영.

## 숫자 (재현)

각 연대는 분석오차 1σ≈0.5385만 authored, 보정 노드가 계통 σ 1.4 공급 → marginal √(0.5385²+1.4²)=1.5.
gap 2.0. shared: Var_gap=1.5²+1.5²−2·1.96=0.58 → 2σ_gap≈1.52<2 → pass. independent: Cov 0 →
2σ_gap≈4.24>2 → warn.

## 검증·배포

- 전체 **174 passed**(커널 단위 5케이스 신규: 자기태깅·병합·공분산 상속/비상속·dispatch). 프런트 변경·
  마이그레이션 없음(팔레트·포트·인스펙터 동적, 시드 데이터).
- 테스트 서버 **0.1.54** 배포 + `seed --mode=replace`·`seed_demo` 재시드. 라이브 평가로 확인:
  independent→warn(`decay-238U·A` 태그) / shared→pass(`decay-238U` 태그) — 태그가 **calibration 노드에서
  유래**함을 검증.

## 남은 것 (L2, 대기)

상수 값을 바꾸면 연대 **값**을 재계산하는 rescale — 여기서 비로소 raw invariant(동위원소비) 또는 민감도 계수
노드가 필요(= R04 L2). 증분 엔진이 하류를 이미 dirty로 잡으므로, L2 rescale까지 가면 "상수 바꾸면 diff가
영향 경계 표시"는 자동으로 따라온다. 유스케이스 생길 때 착수.
