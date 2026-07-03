# 20260703_004 — 영어 버전 문서 세트 추가 (i18n)

> 브레인스토밍 단계 devlog. 요약 수준.

## 한 일

docs/의 모든 문서와 README에 대해 **영어 버전(`_en.md`)** 을 만들고 언어별 상호 링크를 붙였다.

### 생성한 영어 문서
- `README_en.md`
- `docs/idea_en.md`
- `docs/node-graph-paradigm_en.md`
- `docs/case-permian-triassic_en.md`
- `docs/case-precambrian-gssa_en.md`
- `docs/case-cambrian-base-correlation_en.md`

### 규칙
- 파일 접미사 `_en.md`.
- **언어 전환 라인**을 각 문서 H1 아래에 삽입 — EN: `*English · [한국어](…md)*`, KR: `*[English](…_en.md) · 한국어*` (양방향).
- **본문 상호 링크는 언어별로 유지** — 영어 문서끼리는 `_en.md`, 한국어 문서끼리는 `.md`.
- 숫자·오차·고유명사·종명·인용·URL, Mermaid/ASCII 다이어그램 구조와 노드 ID는 그대로 보존.

### 방식
- 문서 5개가 서로 독립적이라 **병렬 번역 에이전트 5개**로 처리, 공통 용어집(glossary)으로 일관성 확보.
- 검증: 이중 접미사(`_en_en`) 없음, 본문 링크 전부 `_en.md`, 언어 전환 라인 양방향, 핵심 숫자(251.902±0.024 / 538.8±0.6 / 635.21±0.57) 보존 확인.

## 커밋

- (이 커밋) 영어 문서 6개 + 한국어 문서/README에 언어 링크 + devlog 004.

## 다음 후보

- 내용 진전은 아직 003의 후보 그대로: 경계 게이트웨이 스키마 초안, tier (b) 상관의 확률적 표현.
- (선택) 새 문서를 추가할 때 KR/EN 쌍을 함께 유지하는 습관.
