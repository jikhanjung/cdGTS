# CLAUDE.md

이 파일은 이 저장소에서 작업하는 Claude Code를 위한 안내입니다.

## 이 저장소의 성격

cdGTS = **Continuously Deployed Geologic Time Scale**, 부제 *"A graph-based geologic time scale engine"*. 지질시대표를 연대층서 단위·경계의 실행 가능한 의존성 그래프로 구현하는 엔진입니다. **브레인스토밍으로 시작해 실행 가능한 코드베이스로 전환**되었습니다 — 개념 코퍼스(`docs/`)와 구현(Django 앱 + React 프론트)이 함께 있습니다. (표기 규칙은 `docs/naming.md`: "Geologic"·"Time Scale"·괄호 앞 공백.)

- **현재 상태**: 스키마 v0 를 Django 5.2 + DRF + React Flow 로 구현, 운영서버(cdgts.paleobytes.info)에 **v0.1.4** 배포 중. 상세는 **[HANDOFF.md](HANDOFF.md)** (현재 상태) · **[TODOs.md](TODOs.md)** (백로그) · `devlog/` (라운드별 기록).
- 개념 코퍼스는 여전히 살아있는 브레인스토밍 대상입니다 — 아이디어를 던지고 굴려볼 수 있습니다.
- **새 작업 시작 전 `HANDOFF.md` 를 먼저 읽으세요.** 무엇이 이미 구현/배포됐는지 여기에 요약돼 있습니다.

## 작업 방식

- **개념/설계 논의는 대화형 브레인스토밍이 기본.** 좋은 사고 파트너가 되어 주세요 — 아이디어를 확장하고, 함의를 짚고, 어려운 지점을 정직하게 지적.
- **성급하게 구조를 만들지 마세요.** 새 설계 문서·스키마·큰 스캐폴딩은 **사용자가 요청할 때만** 생성. 기존 코드/문서 수정은 요청 범위 내에서 진행.
- 아이디어를 기록해 달라고 하면 `docs/` 에 정리(한/영 쌍 유지). 작업 라운드는 `devlog/` 에 기록(요청 시).
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

문서는 한/영 쌍(`.md` / `_en.md`)으로 유지합니다. 진입점은 **`docs/concept-map.md`** (레이어 척추 · 문서 지도 · 수렴점).

- `docs/idea.md` — 전체 개념 정리 (배경, 문제의식, 데이터 모델 Layer 0~6, 열린 질문)
- `docs/node-graph-paradigm.md` — 노드 그래프 패러다임
- `docs/app-architecture.md` — 앱 아키텍처(구현 스택·5개 앱 설계)
- 그 외 사례 3종·스키마·정합성 게이트·경쟁 모델·순환/clamp·토폴로지 diff·분포 표현 문서. 목록은 `README.md` 참조.
- `HANDOFF.md`(현재 상태) · `TODOs.md`(백로그) · `devlog/`(라운드별 기록).
