# 20260703_011 — 분포 표현 (스키마 §4 마지막 열린 질문)

> 브레인스토밍 단계 devlog. 요약 수준.

## 한 일

### 1. 문서화
`docs/distribution-representation.md` (+ `_en`). 스키마 §4 마지막 열린 질문을 펼침.
- **재프레이밍:** 입도 문제가 아니라 세 난제 — (A) 구조화, (B) 비가우시안, (C) joint.
- **A 분해 예산:** analytical/systematic/model. CA-ID-TIMS의 `±X/Y/Z` 실제 관행. **계통 공유 = 게이트 L2
  공분산** → 분포 표현과 정합성 공분산은 같은 문제의 양 끝.
- **B 모양:** 비대칭 HPD·다봉·혼합. `value±`는 모양을 잃음.
- **C joint:** 지속시간·순서는 결합 제약 → 진짜 객체는 결합 사후분포, marginal은 손실 투영.
  cycles의 동시추정 joint와 같음.
- **충실도 사다리 L0–L5:** 점→대칭±→분해예산→모양→joint요약→완전사후. 게이트·순환과 **같은 provenance
  깊이에 종속**. ICC는 중간 rung, GTS는 L5.
- **통일:** GSSA = δ(점질량, `fidelity: exact`), **clamp = 분포 연산자**(pin=δ, range/order=절단).
- **canonical rung:** ICC가 얼리는 정본 단. 잠정 방향 — 경계 정본 L2/L3, joint(L4)는 릴리스 층(희소 공분산).

### 2. 스키마 반영 (KR/EN)
- `age.uncertainty`: 단일 `plus_minus` → **구조화 분포**(`fidelity`·`budget`·`shape`·`shared_components`·
  `posterior_ref`). GSSA = `{ fidelity: exact }`.
- 세 예시 갱신(P–T 분해예산+공유성분, 선캄 exact, 캄브리아 분해예산+note).
- §4 "분포 표현" 항목 **정리됨** 표시.

## 커밋

- (이 커밋) distribution-representation KR/EN + 스키마 반영 KR/EN + README + devlog 011.

## 마일스톤

**스키마 §4의 열린 질문 4개(전역/경계별 버전 · 경쟁 모델 · 순환 · 토폴로지 diff · 분포 표현)가 모두 정리됨.**
→ 스키마 v0가 한 바퀴 닫힘.

## 다음 후보

- 지금까지 문서(13쌍)를 잇는 **통합 개념 지도** 정리.
- 또는 스키마 v0 → v1로 승격(열린 질문 반영본).
