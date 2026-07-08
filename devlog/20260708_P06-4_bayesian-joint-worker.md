# 20260708_P06.4 — 진짜 베이지안 joint 커널 + 비동기 워커 (상세 계획)

[P06](20260708_P06_arc-a-science-engine.md)의 마지막·최난도 단계. 06.1–06.3(전부 해석적, 인프라 0) 위에서
**유일하게 진짜 추론 엔진 + 워커 인프라**를 들인다. 착수 전 계획만 확정 — 실행은 별도 라운드.

## 전제 / 왜 지금이 아니어도 되나

06.1–06.3 뒤에도 남는 "가짜":
- **`joint-inference` = 역분산 가중합 스텁**(`kernels.py`): 입력을 **독립** 가정, 상관 무시. 06.1이 공유성분을
  *전파*하지만 **결합 σ 자체는 여전히 독립** — 공유원 있으면 과소평가.
- **순환(상호제약) 클러스터**: `evaluate.py`가 남은 노드를 뒤에 붙여 available 상류만으로 1회 평가 — 진짜 joint 미룸.
- **Distribution L5 `posterior_ref`**: 필드만, 아무도 안 씀.

정직한 판단(P06 권고 재확인): **정확성엔 06.4가 가장 덜 필수**. 정직한 duration 오차 = 06.1 해석적 공분산이 커버,
reconcile = cycles.md가 "자동 joint보다 authored clamp가 정직"이라 했고 06.3이 구현. → 06.4는 **해석적으로 안 되는
경우에만** 진짜 값: (a) 순환 상호제약, (b) 비가우시안 joint(order 절단+스플라인), (c) 역분산 콤바인의 독립 가정이
깨지는 상관 결합. **실사례가 필요해질 때 착수**가 맞다.

## 목표 (deliverables)

1. **PyMC joint 커널** — `joint-inference` 노드(및 breaker 지나는 순환 클러스터)를 하나의 베이지안 모델로 세워
   MCMC 샘플링. 상관·비가우시안·비선형 제약을 정확히 결합. cycles.md: 국소 상호제약을 접으면 "공짜로" L2/L3가
   원하는 **실제 사후 공분산**이 나온다(06.1의 authored 태그 근사 → 실측 공분산).
2. **Distribution L5 `full` 실사용** — 사후표본 저장 + `posterior_ref`로 참조. marginal(L2/L3)은 사후에서 요약,
   joint(L4 공유성분/공분산)은 사후 공분산에서 유도 → 06.1/06.2 게이트가 그대로 소비.
3. **비동기 평가 인프라** — 동기 in-request 평가를 잡 큐 + 워커로. (진짜 스코프.)

## 실 스코프 = 인프라 3대 결정

### A. 워커/큐 (권고: DB-잡 + 관리명령 워커)
| 선택지 | 장 | 단 |
|---|---|---|
| **DB 잡 테이블 + `manage.py run_worker` 루프** (권고) | 새 서비스 의존 0(SQLite/PG로 충분), 배포 = 프로세스 하나 추가, 관측 쉬움 | 폴링 지연, 수평확장 수동 |
| Celery + Redis | 표준·확장성 | Redis 운영 추가, 경량 앱엔 과함 |
| django-rq | 중간 | 여전히 Redis |

→ **DB-backed `EvalJob`**(status queued/running/done/failed, graph FK, params, result FK, error) + **워커 프로세스**
(`entrypoint`가 web과 별개로 기동, 또는 compose에 `worker` 서비스). 나중에 필요하면 Celery로 교체(인터페이스 유지).

### B. 동기→비동기 평가 UX
- `POST /api/graphs/{id}/evaluate/` → **즉시 job 반환**(202, `{job_id, status:queued}`). 기존 동기 응답과 갈림.
- **하이브리드**: 그래프에 joint/순환 클러스터가 **없으면 종전대로 동기**(빠른 해석적 경로 유지), 있으면 **큐잉**.
  → 대부분의 편집은 여전히 즉답, MCMC 필요한 그래프만 비동기.
- 프론트: `run_meta.status` = queued/running → **폴링**(또는 harness 재호출) → done 시 Results 갱신. Editor의
  auto-evaluate는 "평가 중…" 상태 표시. `GET /api/eval-jobs/{id}/`.

### C. 결정론 / 캐시 재설계
- MCMC는 확률적 ↔ `content_hash` 캐시는 결정론 가정. **seed 고정**(spline 커널의 `rng(0)` 관행 확장) → 같은 입력
  = 같은 사후. 사후표본을 `content_hash` 키로 저장(NodeResult에 `posterior_ref`/샘플 blob 또는 별도 테이블).
- 증분: 해석적 노드는 종전 캐시, joint 노드만 MCMC 재실행(비싸므로 캐시 적중이 핵심).

## PyMC 모델링 스케치 (커널)

joint 클러스터 = {경계 노드들, 이들에 붙은 data 노드(사전), 상호 order/상관 제약}.
- 각 경계 age = 잠재변수(사전 = 상류 data 분포: radiometric normal, astronomical 등).
- **공유 계통** = 공유 잠재변수(붕괴상수 하나가 여러 age에 곱해짐) → 사후 공분산이 자동으로 상관 반영.
- **order 제약** = `pm.Potential`(older ≥ younger) 또는 순서통계 재매개화 → 절단/비가우시안.
- **age-depth** = 관측모형(depth↔age 선형/스플라인, 오차 전파). MCMC로 tie point 불확실성까지 결합.
- 산출: 각 경계 marginal(L3 shape) + 클러스터 공분산(L4) + 원하면 전체 사후 참조(L5).

## 배포 영향
- 이미지 = web + **worker 프로세스**(compose에 `worker` 서비스 또는 supervisor). PyMC/pytensor 의존 추가(빌드 무거워짐).
- 마이그레이션: `EvalJob`(+ 사후표본 저장) 테이블. seed 무변경.

## 단계화
- **06.4a** — `EvalJob` + 워커 + 비동기 평가 배관(**커널은 아직 해석적**; 인프라만 먼저, 저위험 검증).
- **06.4b** — PyMC joint 커널(단일 `joint-inference` 노드부터: 공유 계통 + order), L5 사후 저장.
- **06.4c** — 순환 클러스터 자동 접기(breaker 지나는 SCC를 joint 모델로) + age-depth 관측모형 통합.

## 열린 질문
- 사후표본 저장 형식/보존(용량 vs 재현) — 샘플 blob vs 재실행 모델 참조(provenance 깊이, distribution-representation.md §5).
- joint 클러스터 경계 자동 탐지 규칙(어디까지 한 모델로 묶나).
- 워커 실패/타임아웃 UX, 동시성 상한.
- 캡스톤: Cryogenian GSSA→GSSP를 순환/joint까지 끌고 갈지, 아니면 별 예제.

## 검증 캡스톤(착수 시)
해석적으론 못 푸는 최소 예제 — 두 경계가 tie point를 공유하며 서로를 제약하는 순환 → 06.4 전(1회 근사)과 후(joint
사후)의 duration 공분산 차이를 나란히. 06.3b 데모 그래프의 확장으로.
