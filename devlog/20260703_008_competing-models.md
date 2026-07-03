# 20260703_008 — 경쟁 모델 공존 방식 + 스키마 조정

> 브레인스토밍 단계 devlog. 요약 수준.

## 한 일

### 1. 문서화
`docs/competing-models.md` (+ `_en`). 스키마 §4 "경쟁 모델 공존 방식"을 펼친 검토 노트.
- **경쟁의 결을 쪼갬:** 방법 / 입력 / 상관 배선(위상) / 공유 상류 노드 / 데이터. 스코프도 경계별 vs 전역.
- **거짓 이분법:** `chosen+alternatives` vs 독립 후보 = 게이트웨이/네트워크 2계층과 같은 문제.
  → **네트워크엔 복수 후보, 릴리스에선 선택.** `chosen`은 데이터가 아니라 후보 포인터.
- **선택은 레코드가 아니라 릴리스에 붙는다** (매니페스트 selection). 샌드박스 = 베이스라인 + 선택 오버라이드.
- **불확실성:** 선택(ICC/bake) vs 포락·모델평균(GTS/narrate) — 정합성 게이트 검증/재조정과 같은 축.
- **비틀기:** 전역 모델 후보는 다수 경계를 한꺼번에 정하고 **그 자체로 내부 정합** → 모델 선택과
  정합성 게이트가 동전의 양면.

### 2. 스키마 조정 (KR/EN)
`boundary-gateway-schema` §2:
- `age.age_model = {chosen, alternatives[]}` 임베드 → **`age.model_ref`**(선택 후보 포인터).
- **`ModelCandidate`** 독립 객체 신설(`scope: boundary|global`, `sets`, `output` …).
- **`Release`** 가 `selection: {boundary → candidate}` 소유.
- 세 예시를 `model_ref`로 갱신, 캄브리아 예시에 전역 후보 2개(modelAB/modelD) 추가.
- §4 "경쟁 모델" 항목 **정리됨**으로 표시, "순환" 항목 참조를 `ModelCandidate.inputs`로 수정.

## 커밋

- (이 커밋) competing-models KR/EN + 스키마 조정 KR/EN + README 인덱스 + devlog 008.

## 다음 후보

- 스키마 §4 남은 열린 질문: 분포 표현, 토폴로지 diff, 순환.
- competing-models §7: 후보 큐레이션(문지기), 모델 정체성/버전.
