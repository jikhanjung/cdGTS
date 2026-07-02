# CLAUDE.md

이 파일은 이 저장소에서 작업하는 Claude Code를 위한 안내입니다.

## 이 저장소의 성격

cdGTS는 **"continuously deployed Geologic Time Scale"** 에 대한 **개인 브레인스토밍 공간**입니다. 코드베이스가 아니라 아이디어 저장소입니다.

- **아직 정해진 것이 없습니다.** 스키마·코드·아키텍처·기술 스택 모두 미정.
- 사용자는 여기서 아이디어를 자유롭게 던지고 굴려보려 합니다.

## 작업 방식

- **기본은 대화형 브레인스토밍.** 좋은 사고 파트너가 되어 주세요 — 아이디어를 확장하고, 함의를 짚고, 어려운 지점을 정직하게 지적.
- **성급하게 구조를 만들지 마세요.** 설계 문서·스키마·스캐폴딩·디렉토리 구조는 **사용자가 요청할 때만** 생성.
- 아이디어를 기록해 달라고 하면 `docs/` 에 정리.
- 정확성이 중요한 도메인입니다. 지질연대학 용어·사실은 추측하지 말고, 불확실하면 그렇다고 말하세요.

## 도메인 용어 (혼동 주의)

- **ICS** — International Commission on Stratigraphy.
- **ICC** — International Chronostratigraphic Chart. ICS가 발행하는 공식 합의 시대표. 부정기 개정(예: v2023/09).
- **GTS2020 / GTS2030** — *Geologic Time Scale* 참조 저작. GTS2030 준비 중.
- **GSSP** — Global Boundary Stratotype Section and Point. 현생누대 경계를 물리적 노두의 "지점"으로 정의. 연대는 파생값.
- **GSSA** — Global Standard Stratigraphic Age. 선캄브리아 경계를 약속된 숫자 연대로 정의.
- **이중 명명 체계** — 연대층서(Eonothem/Erathem/System/Series/Stage) ↔ 지질연대(Eon/Era/Period/Epoch/Age).

## 핵심 아이디어 (요약)

지질시대표를 표가 아니라 **재현 가능한 파이프라인의 산출물**로 취급. 데이터 → 모델 → 경계 연대를 **노드 그래프(DAG)** 로 표현. Fixed version 릴리스 + 학자들이 새 데이터를 넣어보는 샌드박스("과학을 위한 CI"). 자세한 내용은 `docs/` 참조.

## 문서

- `docs/idea.md` — 전체 개념 정리 (배경, 문제의식, 데이터 모델 Layer 0~4, 열린 질문)
- `docs/node-graph-paradigm.md` — 노드 그래프 패러다임
