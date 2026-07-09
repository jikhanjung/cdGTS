# 20260708_123 — P06.4a: 비동기 평가 잡 + 워커 (인프라)

[P06.4 계획](20260708_P06-4_bayesian-joint-worker.md)의 첫 단계 **06.4a** 구현. 계획대로 **인프라만** —
잡 큐 + 워커 + 하이브리드 동기/비동기 라우팅. **커널은 아직 해석적**이라 동기·비동기 결과가 동일하다
(진짜 PyMC MCMC 는 후속 06.4b). 저위험으로 배관을 먼저 깔아 06.4b/c 가 위에 얹히게 한다.

## 무엇을 넣었나

- **`EvalJob` 모델**(`engine/models.py`) — status(queued/running/done/failed)·graph FK·params·
  run FK(완료 산출 EvalRun)·error·requested_by·타임스탬프. migration `engine/0003_evaljob`.
- **잡 로직**(`engine/jobs.py`) — 뷰/워커 공유 순수 로직.
  - `claim_next_job()` — 가장 오래된 queued 를 **compare-and-set**(`update(... where status='queued')`
    영향 행수)으로 원자적 클레임. SQLite 단일 라이터 가정, 이중 처리 방지.
  - `process_job(job)` — evaluate_graph 실행 → done, 예외는 잡아 error 에 남기고 failed(워커가
    한 잡 실패로 죽지 않게).
- **워커 명령**(`engine/management/commands/run_worker.py`) — queued 폴링 루프.
  `--poll`(간격)·`--once`(큐 한 번 비우고 종료; 테스트/배치). SIGTERM/SIGINT graceful.
- **하이브리드 라우팅**(`engine/evaluate.needs_async`) — **joint-inference 노드** 또는 **순환
  상호제약 클러스터**(저장 검증 통과 그래프에 남은 데이터 순환 = breaker 를 지나는 순환)가 있으면
  async, 아니면 종전 동기. 대부분의 편집은 여전히 즉답, 무거운 그래프만 큐잉.
- **API**(`engine/views.py`·`urls.py`) —
  - `POST /api/graphs/{id}/evaluate/` : 해석적 → 200 + run(종전). joint/순환 → **202 + 잡 상태**.
  - `GET  /api/eval-jobs/{id}/` : 폴링. done 이면 `run` 에 전체 EvalRun(결과·인증서) 임베드.
- **프론트**(`api.js`·`Editor.jsx`) — `evaluateGraph` 응답에 `status`가 있고 `results`가 없으면 잡으로
  판정 → `getEvalJob` **폴링**(1s, 최대 120회). "Evaluating… (job#N status)" 상태 표시, done 시 종전
  경로로 결과 반영. failed/타임아웃 에러 처리.
- **배포** — `entrypoint.sh` 인자 있으면 그대로 exec(worker), 없으면 web(migrate+gunicorn). `worker`
  서비스 추가(host + dev compose): 같은 이미지·DB, `python manage.py run_worker` 상주. migrate 는 web 만
  수행(경합 방지), 워커는 web 이 스키마 올린 뒤 폴링(미완이면 restart 재시도).

## 검증

- 백엔드 pytest **144 passed**(신규 7): needs_async 판별(해석/joint), 202 큐잉, 워커 처리(done+run),
  원자적 클레임, eval-jobs GET(run 임베드), 실패 기록.
- 프론트 `npm run build` 정상.

## 설계 메모

- **워커/큐 선택 = DB-잡 + 관리명령 워커**(계획 A안). Redis/Celery 의존 0. 나중에 필요하면 잡 로직이
  `engine.jobs` 에 있으니 인터페이스 유지한 채 교체.
- **결정론**: 06.4a 는 해석적 커널이라 캐시(content_hash) 그대로. MCMC 도입(06.4b) 시 seed 고정 +
  사후표본 저장 재설계 필요(계획 C안, 이월).
- **하이브리드**로 라우팅만 갈랐을 뿐 결과는 아직 동일 — 사용자 관점 변화는 joint/순환 그래프의
  "Evaluating…" 비동기 UX 뿐. 진짜 값은 06.4b(공유 계통 → 실측 사후 공분산)에서.

## 다음 (06.4b/c)

- **06.4b** — PyMC joint 커널(단일 joint-inference: 공유 계통 + order 제약), Distribution L5 사후 저장.
  이미지에 PyMC/pytensor 의존 추가(빌드 무거워짐).
- **06.4c** — 순환 클러스터 자동 접기(breaker 지나는 SCC → joint 모델) + age-depth 관측모형 통합.
- **캡스톤** — 두 경계가 tie point 를 공유하는 순환: 06.4 전(1회 근사) vs 후(joint 사후) duration 공분산 대비.
