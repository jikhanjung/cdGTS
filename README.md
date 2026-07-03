# cdGTS — Continuously Deployed Geologic Time Scale

*[English](README_en.md) · 한국어*

> ⚠️ 상태: 초기 브레인스토밍. 확정된 것은 아직 없으며, 아이디어를 던지고 굴려보는 공간입니다.

## 무엇인가

지질시대표를 **~10년 주기의 대형 릴리스(책)** 로만 다루지 말고, **소프트웨어처럼 버전 관리되고 지속적으로 배포되는(continuously deployed) 데이터**로 다루자는 구상입니다.

- **International Chronostratigraphic Chart (ICC)** — ICS가 발행하는 공식 합의 시대표.
- **Geologic Time Scale 2020 (GTS2020)** — 방사연대·천문연대 보정까지 담은 상세 참조 저작. 현재 **GTS2030** 준비 중.

cdGTS는 이 둘을 **하나의 재현 가능한 파이프라인의 산출물**로 보려 합니다:

> 원시 관측(데이터) → 처리·모델 → 경계 연대

핵심 차별점은 **테스트/샌드박스 환경**입니다. 학자가 새로 얻은 데이터를 continuously integrate 해보고, 그것이 경계 연대에 미치는 영향을 **diff**로 즉시 확인할 수 있게 — 일종의 **"과학을 위한 CI"**.

## 개념적 은유: 노드 그래프

블렌더의 지오메트리 노드처럼, **데이터 노드**와 **프로세스/모델 노드**의 네트워크(DAG)로 구성하는 것을 핵심 은유로 삼습니다. 그래프를 평가하면 지구 위 특정 지점의 연대가 결정되고, 이를 모두 모으면 ICC/GTS가 됩니다.

- 그래프를 **길게 서술**하면 → GTS2030 (책)
- 그래프를 **crystallize/bake**하면 → ICC (얼린 스냅샷)

Provenance(FAIR 원칙), 증분 재평가, what-if 비교가 그래프 구조에 자연스럽게 내장됩니다.

## 문서

- [docs/idea.md](docs/idea.md) — 배경, 문제의식, 핵심 아이디어, 계층형 데이터 모델(Layer 0~4), 열린 질문
- [docs/node-graph-paradigm.md](docs/node-graph-paradigm.md) — 노드 그래프 패러다임 상세
- [docs/case-permian-triassic.md](docs/case-permian-triassic.md) — Permian–Triassic 경계로 모델을 검증한 첫 케이스 스터디 (실제 데이터 + 노드 그래프)
- [docs/case-precambrian-gssa.md](docs/case-precambrian-gssa.md) — 선캄브리아 GSSA 대조군 (숫자가 곧 정의 — P–T의 거울상)
- [docs/case-cambrian-base-correlation.md](docs/case-cambrian-base-correlation.md) — 캄브리아기 base (Fortune Head): 섹션 간 correlation이 숫자를 만드는 세 번째 유형
- [docs/boundary-gateway-schema.md](docs/boundary-gateway-schema.md) — 세 케이스를 아우르는 경계 게이트웨이 스키마 초안 (v0)
- [docs/versioning-global-vs-per-boundary.md](docs/versioning-global-vs-per-boundary.md) — 전역 vs 경계별 버전 문제 검토 (열린 질문)
- [docs/coherence-gate.md](docs/coherence-gate.md) — 정합성 게이트 구체화 (Layer 5): 핀된 경계 집합 → 유효한 차트
- [docs/competing-models.md](docs/competing-models.md) — 경쟁 모델 공존 방식 (네트워크 복수 후보 + 릴리스 선택)
- [docs/cycles.md](docs/cycles.md) — 순환 의존성과 clamp (subcommission이 놓는 hand-crafted 게이트)

## 상태

브레인스토밍 단계입니다. 스키마·코드·아키텍처는 아직 정하지 않았습니다.
