# cdGTS

**Continuously Deployed Geologic Time Scale**

*그래프 기반 지질시대표 엔진 — a graph-based geologic time scale engine.*

*[English](README_en.md) · 한국어*

> 상태: 개념(브레인스토밍) → **구현·배포**. 스키마 v0 를 Django 앱 + React 노드 에디터로 구현, 운영서버 [cdgts.paleobytes.info](https://cdgts.paleobytes.info) 에 **v0.1.47** 배포. ICC 테이블·차트(3 스케일 모드)·서술 + 경계·구간 이중성 모델 + 노드그룹·중첩·order/L2 정합성 게이트 + merge geometry + Science CI 위에, **불변 Bake·Vault**(P04) · **멀티유저 CI**(세션 인증·소유/가시성·fork·propose→review→ratify, P05) · **과학 엔진**(공분산 백본·정합성 게이트·clamp reconcile·비동기 워커, P06) · **레퍼런스 노드 + bake→bibliography 와 realistic base-of-Cambrian 모델**(538.82351 Ma, P07) 까지 모두 배포됨. 개념 코퍼스는 `docs/` 에 그대로 유지됩니다.

## 무엇인가

cdGTS는 지질시대표(Geologic Time Scale)를 정적인 표·그림이 아니라 **연대층서 단위와 경계를 서로 연결된 노드로 표현한 실행 가능한 의존성 그래프**로 구현하는 엔진입니다. 상류 정보가 바뀌면 의존 관계를 따라 변경이 전파되어, 지질시대표를 **증분적·재현 가능하게** 다시 만들 수 있습니다.

여기에 더해 — 지질시대표를 **~10년 주기의 대형 릴리스(책)** 로만 다루지 말고, **소프트웨어처럼 버전 관리되고 지속적으로 배포되는(continuously deployed) 데이터**로 다루자는 구상입니다.

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

## 구조 — 티어 × 카테고리

파이프라인은 세 **티어**로 조직됩니다: **registry**(정본 단위·경계) → **graph**(평가되는 노드 네트워크) → **release**(얼린 산출). graph 티어 안의 노드는 **data / process / clamp** 세 **카테고리**로 분류됩니다. 배포에서 **ICC = bake(얼린 스냅샷)**, **GTS = narrate(서술)** 두 산출물이 나옵니다.

> 초기의 선형 레이어(명명0 → 경계1 → 관측2 → age model3 → 상관4 → 종합5 → 배포6)는 이제 **사람이 읽는 서사 순서**로만 유효합니다 — 구현이 티어×카테고리로 접었습니다. 상세: [docs/tier-category-model.md](docs/tier-category-model.md).

## 문서

전체를 잇는 상위 지도는 **[docs/concept-map.md](docs/concept-map.md) — 여기서 시작하세요** (티어×카테고리 척추 · 문서 지도 · 수렴점 5개).

**개념**
- [docs/naming.md](docs/naming.md) — 이름·표기 결정과 근거 (Continuously Deployed · geologic · Time Scale)
- [docs/idea.md](docs/idea.md) — 배경·문제의식·레이어 0–6·게이트웨이·열린 질문
- [docs/node-graph-paradigm.md](docs/node-graph-paradigm.md) — DAG·게이트웨이/네트워크·순환·엣지=분포

**사례 (세 유형)**
- [docs/case-permian-triassic.md](docs/case-permian-triassic.md) — GSSP · 국소 보간 (숫자는 계산)
- [docs/case-precambrian-gssa.md](docs/case-precambrian-gssa.md) — GSSA · 결정 (숫자가 정의 — P–T의 거울상)
- [docs/case-cambrian-base-correlation.md](docs/case-cambrian-base-correlation.md) — GSSP · 섹션 간 상관 (숫자는 타 대륙에서)
- [docs/gssp-gssa-key-papers.md](docs/gssp-gssa-key-papers.md) — GSSP·GSSA 핵심 논문 목록 (정의 데이터·age model·ratification notice; 검증된 서지)
- [docs/gtc-boundaries-report.md](docs/gtc-boundaries-report.md) — **전 경계 종합 보고서** (선캄브리아~현생누대 모든 경계별 정의·discussion·근거 논문; 위 문서의 완전판)

**스키마 & 설계**
- [docs/boundary-gateway-schema.md](docs/boundary-gateway-schema.md) — 경계 게이트웨이 스키마 v0 (§4 열린 질문 5개 모두 정리됨)
- [docs/versioning-global-vs-per-boundary.md](docs/versioning-global-vs-per-boundary.md) — 전역 vs 경계별 버전 (레코드 + 매니페스트)
- [docs/coherence-gate.md](docs/coherence-gate.md) — 정합성 게이트 (Layer 5): 핀된 경계 집합 → 유효한 차트
- [docs/evaluation-order.md](docs/evaluation-order.md) — 평가 순서 = 의존순(topo) ≠ 연대순; order 노드 = 사후 정합성 검사
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

- **스택**: Django 5.2 + SQLite + DRF + React Flow(Vite). 7개 앱(chrono·nodes·graph·engine·releases·accounts·references) + 프론트: 노드 에디터 · **Vault**(ICC 테이블·차트·서술·diff 허브) · **Proposals**(CI 리뷰) · **Bibliography**(레퍼런스 레지스트리). 백엔드 `pytest` 159 passed.
- **엔진**: 값+provenance 전파(pass-through) · 정합성 게이트(L1 authored order edge · L2 duration) · 값/토폴로지 diff · **공분산 백본·clamp reconcile**(P06 과학 엔진) · **비동기 평가 워커**(P06.4a) · merge 노드 geometry 타일링(age→period→era→chart). 계산 커널(numpy/scipy)로 age-depth model·MC 실계산.
- **에디터/차트**: 노드그룹(중첩·병합·드릴인, 로그아웃 읽기전용도 드릴인 열람 가능) + 경계·구간 이중성(boundary/unit) + order edge · auto-evaluate/saved 표시 · 선택 링/다중선택 · **레퍼런스 노드(cite 엣지)** · ICC 차트 3 스케일 모드(Log·Linear·Table) + 줌/팬 + 불확실성 밴드 · Science CI 원클릭 diff · 모바일 대응.
- **아티팩트/CI**(P04·P05·P06·P07, 배포 완료): **Bake**(그래프 → 불변 Release) → **Vault**(Release 열람·비교 허브) · 세션 로그인 · 소유/가시성 · **Fork** · **Propose→Review→Ratify**(권한자 승인 시 새 공표 baseline) · **bake→bibliography**(그래프 인용 → 참고문헌) · **realistic base-of-Cambrian 모델**(δ13C-dated 섹션 → cross-section correlation → T. pedum FAD, 538.82351 Ma).
- **배포**: Docker 이미지 `honestjung/cdgts`. 운영 [cdgts.paleobytes.info](https://cdgts.paleobytes.info) @ **v0.1.47**, 테스트 `:8011` @ **0.1.48**. 배포는 `deploy-prod.sh`(배포 전 DB 스냅샷) + nginx 점검 페이지. 개발/테스트가 운영 DB 를 일일 pull(NAS 오프사이트 백업, 04:00 cron).

현재 상태 헤드라인은 [HANDOFF.md](HANDOFF.md), 라운드별 변경은 [`devlog/`](devlog/), 미해결 열린 질문은 [TODOs.md](TODOs.md) 참조.
