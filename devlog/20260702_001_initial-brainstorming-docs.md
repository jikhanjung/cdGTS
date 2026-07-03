# 20260702_001 — 초기 브레인스토밍 문서 셋업

> 브레인스토밍 단계 devlog. 실제 개발 진입 전이라 요약 수준으로만 기록.

## 한 일

프로젝트를 **개인 브레인스토밍 공간**으로 규정하고 기초 문서를 만들었다.

- **CLAUDE.md** — 저장소 성격(코드가 아니라 아이디어 저장소), 작업 방식(대화형 브레인스토밍, 성급한 구조화 금지), 도메인 용어(ICS/ICC/GTS/GSSP/GSSA/이중 명명 체계) 정리.
- **README.md** — cdGTS 개요: 지질시대표를 "10년 주기 책"이 아니라 continuously deployed 데이터로.
- **docs/idea.md** — 배경, 문제의식, 핵심 아이디어, **계층형 데이터 모델(Layer 0~4)**, 열린 질문.
- **docs/node-graph-paradigm.md** — 블렌더 지오메트리 노드에서 출발한 **노드 그래프(DAG)** 은유, provenance·증분 재평가·what-if, 순환 의존성 문제.

## 핵심 개념 (이 시점 정리)

- 지질시대표 = **표가 아니라 재현 가능한 파이프라인의 산출물.**
- 데이터 → 모델 → 경계 연대를 **노드 그래프**로. Fixed release + 샌드박스("과학을 위한 CI").
- 같은 그래프에서 두 산출물: **narrate → GTS(책)**, **bake → ICC(스냅샷)**.

## 커밋

- `1e46bf3` first commit
- `bdfff10` Add CLAUDE.md and initial brainstorming docs

## 남은 것 (당시 열린 질문)

- Layer 3(모델)의 위상: 실제 계산까지 할지, 발표값+출처 기록 수준일지.
- 권위 vs 실험 경계, 기존 포맷 정합(Macrostrat/GeoSciML), 버전 전략.
