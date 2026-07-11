# 20260711_R02 — 소스코드 수준 리뷰

대표 구현 파일 직접 검토:
`graph/models.py` · `engine/evaluate.py` · `releases/services.py` · `releases/views.py` ·
`frontend/src/api.js` · `frontend/src/Editor.jsx` · `accounts/permissions.py`.

## 한 줄 결론

코드베이스는 이미 "아이디어가 큰 프로토타입" 단계를 넘었다. 백엔드는 **도메인 모델링·책임 분리·운영 감각**
측면에서 수준이 높고, 프론트는 핵심 기능을 빠르게 밀어 넣으며 제품을 완성한 흔적이 강하다. 현재 가장 큰
기술부채는 **거대 프론트 컴포넌트(`Editor.jsx`)** 와 **성장 중인 서비스 레이어의 응집도 관리**다.

## 총평

- **백엔드 수준**: 좋음. 개념 모델이 흔들리지 않고, 서비스 함수 경계도 현재 규모에서는 읽기 쉽다.
- **프론트 수준**: 기능 밀도는 높지만 구조적 압축이 심하다. 지금은 작동하지만, 후속 기능이 쌓일수록 회귀
  위험이 커질 지점이 보인다.
- **운영/제품 감각**: 좋음. 세션 인증, SQLite WAL, bake/transient 분리, baseline verify 같은 선택이
  연구용 코드가 아니라 실제 서비스 코드를 지향한다.

## 강점 5개

1. **도메인 모델링이 좋다.**
   `Graph / NodeInstance / NodeGroup / Gateway / Edge` 가 각자 개념적 역할을 갖고 있고, boundary/unit/order/cite
   같은 도메인 개념이 자연스럽게 모델에 들어와 있다. `graph/models.py` 는 문서 구상을 코드로 잘 옮긴 축이다.

2. **백엔드 책임 분리가 비교적 선명하다.**
   평가 로직은 `engine/evaluate.py`, 릴리스 유스케이스는 `releases/services.py`, API 노출은 `releases/views.py`
   중심으로 정리돼 있다. View 가 완전히 비어 있지는 않지만, 핵심 판단과 상태 전이는 서비스 레이어에 있다.

3. **설계 의도가 주석에 남아 있다.**
   주석이 "무엇을 한다"보다 "왜 이렇게 나눴는가"를 설명한다. 이 프로젝트는 개념 밀도가 높은 편이라 이런
   설계 주석이 유지보수 비용을 실제로 낮춘다.

4. **운영 감각이 들어가 있다.**
   `config/settings.py` 의 WAL, same-origin session auth + CSRF, Vite dist/static 처리, transient bake 와
   immutable bake 분리 같은 부분은 실제 운영 경험 없이 나오기 어려운 선택이다.

5. **확장 축이 이미 구조 안에 있다.**
   sandbox override, proposal/ratify, authored clamp, bibliography/provenance seam 이 해킹성 부속물이 아니라
   후속 기능으로 자라날 수 있는 형태로 심어져 있다.

## 기술부채 5개

1. **`frontend/src/Editor.jsx` 가 너무 크다.**
   현재 1252줄. 상태 관리, synthetic node 구성, group drill-in, selection/menu, 저장/검증/제안 흐름이
   한 파일에 몰려 있다. 가장 명확한 회귀 위험 지점이다.

2. **릴리스 서비스 레이어가 점점 비대해질 여지가 크다.**
   `releases/services.py` 는 지금은 읽히지만 bake/diff/proposal/clamp/reconcile 이 한 모듈에 계속 쌓이면
   변경 충돌과 맥락 전환 비용이 커진다.

3. **문서와 코드 기준선이 완전히 동기화돼 있지 않다.**
   README 와 HANDOFF 의 버전/테스트 수치 차이는 새 작업자가 오래된 상태를 현재라고 오해하게 만든다.
   코드 품질 자체의 문제는 아니지만, 협업 속도를 떨어뜨리는 유지보수 부채다.

4. **권한 규칙이 흩어질 위험이 있다.**
   `visible_*`, `can_write_*`, `can_ratify()` 류 정책이 늘어나는 방향인데, 기능이 더 커지면 규칙 추적이
   어려워질 수 있다. 지금은 감당 가능하지만, 멀티유저 기능 확장 전 한 번 정리할 타이밍이다.

5. **프론트 자동화 검증이 상대적으로 약하다.**
   백엔드 pytest 는 강하지만, 핵심 가치 흐름인 로그인→fork→edit→bake→diff→propose→ratify 는 브라우저
   상호작용 비중이 높다. 수동 검증만으로는 이후 프론트 리팩터링 속도를 보장하기 어렵다.

## 파일별 인상

### `graph/models.py`

- 가장 인상 좋은 축. 모델 네이밍이 명확하고, 자연키·제약·도메인 개념의 대응이 좋다.
- 특히 `nature`, `kind`, `Edge.kind`, `Gateway` 분리가 "초기 개념이 코드로 내려온 정도"를 잘 보여준다.

### `engine/evaluate.py`

- 증분 해시, 동기/비동기 라우팅, L0~L2 certify 가 비교적 단정하게 모여 있다.
- 현재 수준에선 응집도가 괜찮다. 다만 P06.4b 이후 joint/Bayesian 로직이 본격화되면 이 파일 하나에 더
  얹는 방식은 한계가 올 가능성이 높다.

### `releases/services.py`

- 유스케이스 중심 파일로서는 좋다. 읽을 때 "시스템이 무엇을 할 수 있는가"가 눈에 들어온다.
- 반면 기능이 가장 많이 모이는 허브라서, 다음 단계부터는 `bake`, `diff`, `proposal`, `clamp` 모듈 분리가
  필요해질 것이다.

### `releases/views.py`

- DRF 액션 구성이 실용적이고, 현재는 과도하게 뚱뚱하지 않다.
- 다만 action 수가 계속 늘면 권한/오류 메시지/입력 검증이 view 마다 퍼지기 쉬워, 이후 thin-view 원칙을 더
  강하게 적용하는 편이 낫다.

### `frontend/src/api.js`

- 얇고 직관적이다. 백엔드 엔드포인트 매핑을 한곳에 모아 프론트 추적성이 좋다.
- 프론트가 커질수록 도메인별 API 모듈 분리 정도는 고려할 수 있지만, 지금은 큰 문제 아니다.

### `frontend/src/Editor.jsx`

- 기능 자체는 강하다. 그룹 드릴인, synthetic node, read-only gating, bake/propose 연결까지 한 파일에서
  실제로 잘 돌아가게 만든 점은 분명 성과다.
- 하지만 현재 구조는 "핵심 제품을 빠르게 완성한 파일"에 가깝다. 앞으로는 기능 추가보다 **분해**가 더
  큰 가치가 있다.

## 리팩터링 우선순위 3개

1. **`Editor.jsx` 분해**
   우선순위 최고. 최소한
   `buildView 계열`, `selection/context menu`, `graph actions(save/evaluate/bake/propose)`, `read-only gating`
   정도는 분리할 가치가 있다.

2. **릴리스 서비스 계층 재편**
   `releases/services.py` 를 `bake.py`, `diff.py`, `proposal.py`, `clamp.py` 정도로 쪼개면 다음 기능 추가가
   훨씬 안전해진다.

3. **권한 정책 중앙화**
   graph visibility, release write, ratify authority 같은 규칙을 정책 함수 모음으로 조금 더 명시적으로
   정리해두면 P05 이후 멀티유저 확장에 도움이 된다.

## 판단

현재 코드베이스는 **좋은 솔로/소규모 제품 코드**다. 개념과 구현이 잘 연결돼 있고, 테스트와 배포 감각도
갖췄다. 품질의 병목은 "기초 설계 부재"가 아니라 **성장한 기능을 구조적으로 다시 접는 시점이 왔다**는 데 있다.
새 기능 하나를 더 얹는 것보다, 프론트 핵심 파일과 릴리스 서비스 허브를 한번 정리하는 편이 다음 속도를 더
지켜줄 가능성이 크다.

---

## R02 검토 노트 (2026-07-11 갱신)

> 위 리뷰를 실제 코드·이후 작업에 대조한 메타-검토. 요지: **정확하고 균형 잡힌 "구조/건강성" 리뷰이지만
> "correctness" 리뷰는 아니며, 일부 항목은 이후 이미 움직였다.**

### 성격 — 구조 리뷰이지 정확성 리뷰는 아니다

인용 수치는 지금도 정확하다(`Editor.jsx` 1252줄 · `releases/services.py` 534줄·함수 31개 · `api.js` 얇음).
다만 **버그를 하나도 보고하지 않는데 실제로는 있었다**(아래). "소스코드 수준 리뷰"라는 제목이 "버그 없음"으로
과신될 여지가 있으니, 이 문서는 **아키텍처·유지보수성 리뷰**로 읽혀야 한다.

### 여전히 유효

- **Editor.jsx 분해(부채#1·우선순위#1)**, **services.py 허브(부채#2)** — 최상위 진단 그대로 유효.
- 백엔드/운영 감각 강점 평가 — 동의.

### 이후 이미 움직인 것 (R02는 오늘 오전 스냅샷)

- **강점#5 "authored clamp"** → [cycles §12](../docs/cycles.md#12-재검토-노트-2026-07--clamp는-별도-개념으로-필요한가)
  재검토로 **"clamp는 별도 개념 불필요"로 뒤집고 축소**(devlog 135, 0.1.51). R02는 clamp *기계의 존재*를 건강한
  확장 축으로 읽었으나, 실사용을 셌다면(그래프 pin 2개=둘 다 GSSA · 실 `releases.Clamp` 0건) **강점이 아니라
  미사용 스캐폴딩**이었다. → blind spot: 인프라를 *load-bearing 여부*가 아니라 *존재 자체*로 칭찬.
- **부채#3 문서 드리프트** → README 를 0.1.51/0.1.47 로 동기화해 현재 해소.
- **부채#5 프론트 검증 약함** → **Tier 1 시나리오 테스트(`test_ci_flow.py`, 세션+CSRF)** 추가로 API-계약 수준
  커버(devlog 134). 브라우저 Tier 2 는 여전히 열림.
- **우선순위#2 `clamp.py` 분리** → clamp 는 이제 DEMO-ONLY → "분리"보다 "격리/제거" 프레이밍이 맞음.

### R02 가 놓친 것

1. **gateway-wipe 버그.** 저장 흐름을 개념적으로 봤지만 `graph/serializers.py _replace_topology`(PUT)가
   `Gateway.node` CASCADE 로 **게이트웨이를 전부 삭제**하던 correctness 버그는 못 잡았다(fork→편집→bake 가
   조용히 깨짐). **읽기 기반 리뷰의 한계** — exercised 테스트(Tier 1)가 잡았고 devlog 134 에서 수정. R02 자신의
   부채#5 를 뒷받침하는 가장 강한 증거.
2. **권한 부채#4 는 과장.** 이미 `accounts/graph/releases` 각각에 `permissions.py` 가 **있다.** 문제는 "구조
   부재"가 아니라 일부 정책이 services/views 에 섞인 것 — 부채는 서술보다 가볍다.
3. **시퀀싱 통찰 부재.** #1(Editor 분해)과 #5(프론트 검증 약함)는 연결된다 — **테스트 안전망 없이 1252줄을 먼저
   쪼개는 건 순서가 거꾸로.** Tier 2 브라우저 스모크 → Editor 분해가 맞다. R02 는 둘을 따로 나열만 한다.

### 우선순위 재정렬 (제안)

1. **프론트 안전망 먼저** — Tier 2 해피패스 스모크 1개(비블로킹). Editor 분해의 전제.
2. **Editor.jsx 분해** — 안전망 확보 후. R02 의 분해 축 그대로 좋음.
3. **services.py 재편** — `bake/diff/proposal` 분리 + **clamp 는 분리가 아니라 demo 격리/제거**(§12 반영).
4. 권한은 중앙화보다 "services/views 에 샌 정책을 기존 `permissions.py` 로 회수" 수준이면 충분.

> 종합: R02 는 믿을 만한 건강성 리뷰다. 보완점 — (a) 자신을 correctness 리뷰로 오인하지 않기(버그 0 ≠ 버그 없음),
> (b) clamp 를 사용량으로 재평가(강점→축소, 반영됨), (c) 분해와 테스트의 순서를 묶기.
