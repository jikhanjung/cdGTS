# 20260704_040 — 선후 제약 노드 (order, 검사 버전)

> 휴면이던 `order` clamp 를 **두 경계의 시간적 선후 검사**로 활성화. coherence-gate L1a 를 전역 스텁이
> 아니라 **국소·authored 제약(그래프 노드)** 으로 실현. **결정: 검사(validate)부터 · 세로 핸들(아래=older).**

## 배경

- `order` 클램프는 정의만 있고 커널 없이 pass-through 였음(무동작). `_certify` 의 L1 은 게이트웨이 나열순
  단조 휴리스틱 스텁(36경계 그래프에서 warn 나던 그것).
- 사용자 아이디어: clamp 같은 제약 노드를 **A·B 사이에 두고 연결**해 선후를 제한. → 이미 있는 order 를
  깨우되, 토폴로지를 **파라미터 참조 대신 두 입력 엣지**로, 판정은 **검사만**(값 불변)으로.

## 결정

- **검사(validate) 먼저** — 값을 바꾸지 않고 `age(older) ≥ age(younger) + Δ` 판정만. 사이클 없음(sink).
  강제(joint reconcile, L3b)는 후속.
- **세로 핸들** — 위=younger(작은 Ma) / 아래=older(큰 Ma). **아래=older 는 ICC/층서 컬럼 관례**.
  위치가 방향을 인코딩("제약은 데이터흐름 아님"을 시각적으로 신호).

## 한 일

### 엔진
- `kernels.order_check` — 포트 `older`/`younger` 로 두 입력 구분, `gap = older − younger`,
  `ok = gap ≥ min_gap`. 결과는 분포가 아니라 판정 dict `{kind:order, ok, gap, min_gap, note}`. 레지스트리 등록.
- `evaluate._certify` — **authored order 노드가 있으면 L1 을 그걸로 판정**(위반+mode=hard → FAIL /
  mode=warn → WARN / 전부 통과 → PASS). 없으면 기존 게이트웨이 단조 휴리스틱으로 폴백.

### 스키마(seed)
- `order` 노드타입 재설계: params `min_gap`(Δ Ma) · `mode`(hard/warn). 포트 `younger`(in)/`older`(in),
  출력 없음(sink). 기존 target/out 포트 제거.

### 프론트
- `OrderNode.jsx` — 세로 핸들(top=younger / bottom=older), 몸통에 판정 인라인(✓/⚠ + gap), 위반 시 붉게.
- Editor: `rfType('order')→cdgtsOrder`, 선택·우클릭에서 order 도 실노드(`isRealNode`)로 취급.

## 검증
- `pytest` **76 passed**(신규 9: order 커널 5 + `_certify` 통과/hard-FAIL/warn/min_gap 4). 프론트 빌드 클린.
- 판정식·방향(아래=older)·mode·Δ 모두 테스트로 고정.

## 배포/이월
- `order` 노드타입 변경 → 재시드 **`seed --mode=replace`** 필요(add 는 nodetype 자연키로 skip).
- 이월: **강제(reconcile)** = joint truncation → 상관 사후분포(coherence-gate L2 공분산·L3b). 진짜 사이클/
  solver 필요. L2 지속시간(음수/누수)·hard vs warn 릴리스 차단 정책.
