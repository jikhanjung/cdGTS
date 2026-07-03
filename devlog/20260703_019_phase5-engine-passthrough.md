# 20260703_019 — Phase 5: engine 앱 (pass-through 평가)

> 계획 [P01](20260703_P01_app-build-plan.md) Phase 5 완료 기록. 설계 [app-architecture §2.4](../docs/app-architecture.md).

## 한 일

다섯 번째 앱 `engine` — 그래프를 "돌게" 만드는 평가. **pass-through 스코프**(값+출처 전파, 계산 없음).

### 모델 (`engine/models.py`)
- `EvalRun` — 한 그래프의 평가 작업 + `stats{computed,cached}`.
- `NodeResult` — 노드별 산출: `distribution`(전파된 분포 dict|null) + `content_hash` + `provenance`(기여
  상류 key, 역추적) + `cached`. 노드는 재저장 시 교체되므로 FK 아닌 **node_key 문자열** 참조.
- `CoherenceCertificate` — Layer 5 게이트 인증서 스텁(L0–L3 checks, passed).

### 평가 로직 (`engine/evaluate.py`)
- `topo_order` — Kahn 위상순, 순환 잔여(breaker 경유)는 뒤에 붙여 1회 평가.
- `_compute` — data=params.distribution 방출 / pin=exact(value)(GSSA) / process·기타 clamp=첫 입력 분포 통과.
- **증분**: `content_hash(타입,params,입력해시)`. 직전 run 의 같은 node_key 가 같은 해시면 결과 재사용(cached).
  leaf param 이 바뀌면 해시 전파로 하류 자동 dirty.
- `_certify` — 게이트웨이 경계값 단조성만 대략(L1), 나머지 skip.

### API (engine 소유 — graph 는 engine 을 모름)
- `POST /api/graphs/{id}/evaluate/` — 평가 후 run(+results+certificate) 반환. GET = 마지막 run.
- graph 의 evaluate 스텁 @action 제거(엔드포인트를 engine 으로 이관, 의존 방향 유지).

### 프론트 (결과 뱃지)
- 평가 시 결과를 node_key 로 매핑 → 각 노드 data.result. `CdgtsNode` 하단에 `value_ma Ma` + 캐시 점(•).
  툴바 status 에 run#·computed/cached·정합성 표시.

## 검증
- check 0 · migrate OK · **pytest 35 passed**(engine 7: 전파·provenance·pin exact·캐시 히트·leaf dirty·API).
- **live curl**: uPb(251.902)→age-depth-model **전파**(prov=['uPb']) · 재평가 **cached 2/computed 0** · cert pass.
- 프론트 `npm run build` 성공.
- **DoD 충족**: 그래프가 "돈다" — 입력 바꾸면 하류 갱신(해시 dirty), provenance 역추적, 증분 캐시.

## 스택
- 추가 없음(Django+DRF). `engine.apps.EngineConfig` → INSTALLED_APPS, `/api/` 마운트.
- 무거운 계산(MC/베이지안/joint)은 여전히 후속(별도 과학 스택). 현재는 값 전파만.

## 다음
- **Phase 6 `releases`** — ModelCandidate/Release(selection+clamps)/BoundaryRecord(bake)/Diff(값+토폴로지).
