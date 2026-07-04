# cdGTS — Continuously Deployed Geologic Time Scale

*[English](README_en.md) · 한국어*

> 상태: 개념(브레인스토밍) → **구현·배포**. 스키마 v0 를 Django 앱 5개 + React 노드 에디터로 구현, 운영서버 [cdgts.paleobytes.info](https://cdgts.paleobytes.info) 에 **v0.1.4** 배포 중(ICC 테이블 bake + ICS chart.ttl 경계 시드). 개념 코퍼스는 `docs/` 에 그대로 유지됩니다.

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

## 레이어 척추 (Layer 0–6)

명명(0) → 경계 정의(1) → 원시 관측(2) → 국소 age model(3) → 상관(4) → 전역 종합·정합성 게이트(5) → 배포(6). 상위는 하위에서 파생. 배포에서 **ICC = bake(얼린 스냅샷)**, **GTS = narrate(서술)** 두 산출물.

## 문서

전체를 잇는 상위 지도는 **[docs/concept-map.md](docs/concept-map.md) — 여기서 시작하세요** (레이어 척추 · 문서 지도 · 수렴점 5개).

**개념**
- [docs/idea.md](docs/idea.md) — 배경·문제의식·레이어 0–6·게이트웨이·열린 질문
- [docs/node-graph-paradigm.md](docs/node-graph-paradigm.md) — DAG·게이트웨이/네트워크·순환·엣지=분포

**사례 (세 유형)**
- [docs/case-permian-triassic.md](docs/case-permian-triassic.md) — GSSP · 국소 보간 (숫자는 계산)
- [docs/case-precambrian-gssa.md](docs/case-precambrian-gssa.md) — GSSA · 결정 (숫자가 정의 — P–T의 거울상)
- [docs/case-cambrian-base-correlation.md](docs/case-cambrian-base-correlation.md) — GSSP · 섹션 간 상관 (숫자는 타 대륙에서)

**스키마 & 설계**
- [docs/boundary-gateway-schema.md](docs/boundary-gateway-schema.md) — 경계 게이트웨이 스키마 v0 (§4 열린 질문 5개 모두 정리됨)
- [docs/versioning-global-vs-per-boundary.md](docs/versioning-global-vs-per-boundary.md) — 전역 vs 경계별 버전 (레코드 + 매니페스트)
- [docs/coherence-gate.md](docs/coherence-gate.md) — 정합성 게이트 (Layer 5): 핀된 경계 집합 → 유효한 차트
- [docs/competing-models.md](docs/competing-models.md) — 경쟁 모델 공존 (네트워크 복수 후보 + 릴리스 선택)
- [docs/cycles.md](docs/cycles.md) — 순환 의존성과 **clamp** (subcommission이 놓는 hand-crafted 게이트)
- [docs/topology-diff.md](docs/topology-diff.md) — 토폴로지 diff (값 diff와 직교하는 구조 변화의 축)
- [docs/distribution-representation.md](docs/distribution-representation.md) — 분포 표현 (충실도 사다리 L0–L5)

## 핵심 수렴점

서로 다른 스레드가 반복해서 같은 구조로 모였습니다 (상세는 [concept-map](docs/concept-map.md) §3):

- **provenance 깊이 = 하나의 축** — 정합성 레벨·분포 충실도·순환 해소가 모두 여기에 종속.
- **clamp가 통일자** — GSSA(pin=점질량) · 순환 절단 · 분포 연산이 한 원시타입으로.
- **ICC/GTS = bake/narrate 이분법**이 게이트·경쟁모델·diff·분포에서 반복.

## 상태

개념(브레인스토밍) → **구현·배포** 단계입니다. 스키마 v0(§4 열린 질문 5개 모두 정리)를 실행 가능한 앱으로 내렸습니다.

- **스택**: Django 5.2 + SQLite + DRF + React Flow(Vite). 5개 앱(chrono·nodes·graph·engine·releases) + 프론트 노드 에디터·ICC 테이블·릴리스 diff 뷰. 백엔드 `pytest` 65 passed.
- **엔진**: 값+provenance 전파(pass-through) · 정합성 게이트 · 값/토폴로지 diff 골격. 계산 커널(numpy/scipy)로 age-depth model 실계산.
- **배포**: Docker 이미지 `honestjung/cdgts`. 운영 [cdgts.paleobytes.info](https://cdgts.paleobytes.info) @ **v0.1.4**, 개발/테스트 @ v0.1.1. 원자적 DB 스냅샷 + NAS 오프사이트 백업(04:00 cron).

현재 상태 헤드라인은 [HANDOFF.md](HANDOFF.md), 라운드별 변경은 [`devlog/`](devlog/), 미해결 열린 질문은 [TODOs.md](TODOs.md) 참조.
