# 20260703_005 — 경계 게이트웨이 스키마 초안 v0

> 브레인스토밍 단계 devlog. 요약 수준. (순수 개념 → 첫 구체 구조로 넘어간 산출물.)

## 한 일

세 케이스에서 뽑은 요구사항을 하나의 **경계 게이트웨이 스키마 초안(v0)** 으로 모았다.
한/영 쌍으로 작성(`docs/boundary-gateway-schema.md` + `_en.md`), README 양쪽 인덱스에 링크.

### 핵심 설계 — 두 개의 독립적 다형 축
- `definition.type`: **GSSP | GSSA** — *어디/무엇*(위치)
- `age.method`: **decreed | local-interpolation | cross-section-correlation** — *숫자가 어떻게 나왔나*
- 커플링: GSSA ⇒ decreed / GSSP ⇒ {보간, 상관}.

### 세 케이스 요구사항 → 필드 매핑
- 다형 → 두 축 polymorphic
- 위치↔연대 분리 → `definition`(위치) vs `age`(연대) 별도 블록
- provenance = 그래프 참조 → `age.provenance_ref`(지리적 분산 가능)
- age model 1급 → `age.age_model.chosen` + `alternatives`
- 게이트웨이 = 계약 → `version` · `status.level` · `supersedes`

### 검증용 예시
- P–T(GSSP·보간·251.902±0.024), Archean–Proterozoic(GSSA·decreed·2500, 오차 없음),
  캄브리아 base(GSSP·상관·538.8±0.6, contested) YAML 3개로 두 축의 조합을 구체화.

## 커밋

- (이 커밋) 스키마 초안 KR/EN + README KR/EN 인덱스 + devlog 005.

## 다음 후보 (스키마 §4 열린 질문)

- 전역 vs 경계별 버전, 분포 표현 깊이, 경쟁 모델 공존 방식, 토폴로지 diff, 순환 처리.
- 표기를 YAML 예시에서 JSON Schema / TypeScript 타입으로 굳힐지.
