# 경쟁 모델 공존 방식

*[English](competing-models_en.md) · 한국어*

> 상태: **검토 노트 → 스키마에 일부 반영.** [boundary-gateway-schema.md](boundary-gateway-schema.md) §4의
> "경쟁 모델 공존 방식"을 펼친 것. node-graph 문서의 **"노드 스왑 = what-if"** 의 정면.

## 1. "경쟁 모델"을 먼저 쪼갠다

한 단어로 뭉치면 안 된다. 경쟁의 결이 층위별로 다르다:

| 무엇이 다른가 | 예 | 그래프에서 |
|---|---|---|
| **방법(method)** | 스플라인 vs 베이지안 age-depth | 같은 배선, 노드만 교체 |
| **입력 집합** | 논쟁적 재층 포함/제외, Oman vs Namibia 앵커 | 엣지 가감 |
| **상관 가설(wiring)** | BACE 위치 → Bowyer 2022 model A/B vs C/D | **위상(topology) 차이** |
| **공유 상류 노드** | 붕괴상수·tracer 버전 | 상류 노드 스왑 (다수 경계 동시 영향) |
| **데이터 자체** | 새 U-Pb | 새 리프 |

어떤 경쟁은 노드 스왑(같은 그래프), 어떤 건 배선 차이(위상 diff), 어떤 건 입력 차이다. 그리고 결정적으로
**스코프가 다르다**(경계별 vs 전역) — §4에서 다시.

## 2. 두 선택지는 거짓 이분법

§4가 제시한 (a) `chosen + alternatives`를 한 레코드에 vs (b) 각 모델이 독립 후보 — 이건 우리가 이미 가진
**게이트웨이/네트워크 2계층 구조**와 같은 문제다:

- **경쟁 모델들은 게이트웨이 *사이의 자유 네트워크*에 산다.** 각 모델은 같은 입력·같은 경계-위치 노드에 물린
  프로세스 노드이고, node-graph 문서의 "대안 그래프 브랜치"가 바로 이것. → **복수로 공존, 각자 완전한 provenance**
  (option b의 알맹이).
- **게이트웨이(= 얼린 경계 레코드)는 그중 하나를 *선택*해 고정한다.** → 하나의 숫자 (option a의 알맹이).

즉 답은 "둘 중 하나"가 아니라 **네트워크엔 복수, 게이트웨이/릴리스에선 선택**. `chosen`은 데이터를 품는 필드가
아니라 **후보 노드를 가리키는 포인터**여야 한다. 대안을 레코드 안에 각주로 눌러 담으면 provenance를 잃고
"승자 교체"가 어색해진다.

## 3. 선택은 레코드가 아니라 *릴리스*에 붙는다

버전 노트와 봉합되는 지점. 전역 릴리스 매니페스트는 이미 "모델 선택"을 핀한다:

- **모델 후보** = 독립적으로 주소지정 가능한 객체 (복수, 각자 인용·provenance·출력값).
- **각 릴리스**(ICC-2024/12, 샌드박스 브랜치)가 `{boundary → 어느 후보}` **선택 매핑**을 들고 있음.
- **"공식값"은 파생된다:** `release.selection[boundary] → 후보 → 그 출력값`.

**샌드박스 = 베이스라인 + 선택 오버라이드** ("ICC-2024/12를 쓰되 base-cambrian은 model D로"). 즉 경쟁 해소는
레코드의 영구 속성이 아니라 **릴리스 단위 바인딩** — "continuous deployment를 모델 선택에 적용"한 것. 후보는
CI로 계속 쌓이고, 비준된 선택만 주기적으로 갱신.

## 4. 불확실성 — 여기서 또 ICC/GTS가 갈린다

경쟁 모델은 점값만 다른 게 아니라 **모델(인식론적) 불확실성**을 나타낸다. 측정 불확실성과는 다른 층. 두 처리법:

- **선택(select one):** 한 모델 값 ± 내부오차. 깔끔하지만 이견을 숨기고 ±를 **과소평가**.
- **모델 평균/포락(envelope):** 경쟁 모델 결합(BMA)/범위. 정직하지만 어느 단일 모델도 지지 않는 값 + **가중치를
  누가 정하나** 문제.

정합성 게이트의 검증/재조정 갈림과 같은 축이다:

- **ICC = bake = 선택.** 권위엔 단일 숫자가 필요.
- **GTS = narrate = 복수 보존.** model A/B/C/D·포락·이견을 서술.

## 5. 비틀기: 어떤 모델은 경계 하나가 아니라 *여러 경계*를 건다

Bowyer 2022의 글로벌 δ¹³C age model A–D는 base-Cambrian 하나가 아니라 주변 여러 Ediacaran–Cambrian 경계를
**동시에** 정한다. 그래서 후보엔 두 종류:

- **경계별(local) 후보** — 한 경계의 age-depth 모델.
- **전역(global) 후보** — 다수 경계를 한꺼번에 정하는 모델.

**전역 후보는 그 자체로 내부 정합적**(한 모델이 여러 경계를 일관되게 냄)이다. 반대로 서로 다른 전역 모델에서
경계를 하나씩 골라 섞으면(model A의 base-Cambrian + model C의 이웃) 정확히 거기서 정합성이 깨진다.
→ **모델 선택과 [정합성 게이트](coherence-gate.md)는 동전의 양면: 정합한 선택 = 일관된 모델 집합에서 뽑기.**

## 6. 스키마에 반영한 것

[boundary-gateway-schema.md](boundary-gateway-schema.md) §2를 이렇게 조정:

- `age.age_model = {chosen, alternatives[]}` 임베드 → **`age.model_ref`**(선택된 후보 포인터). `value_ma`는 그
  후보 출력의 **bake 사본**.
- **`ModelCandidate`** 를 독립 객체로 신설: `id/version`, `scope: boundary|global`, `sets`(전역이면 정하는 경계들),
  `kind`, `inputs`, `correlation_via`, `output`, `provenance_ref`.
- 권위 바인딩은 **릴리스 매니페스트의 `selection`** (경계 레코드가 아니라 릴리스가 소유).

## 7. 남는 열린 질문

- **후보 큐레이션:** 샌드박스엔 누구나 모델 노드 추가. ICC가 고려하는 후보 집합의 문지기는 누구/무엇.
- **모델의 정체성/버전:** 모델 = 코드+설정+입력. 입력이 바뀐 재실행은 새 후보인가 같은 후보의 새 버전인가.
- **포락 가중치:** 모델 평균 시 가중치를 누가/어떻게.
- **조합 폭발:** 경계 N × 후보 M × 정합 제약. 대부분 경계는 후보 하나뿐이라는 현실로 관리 가능한가.
- **전역 후보의 부분 채택:** 전역 모델의 일부 경계만 받아들일 때 정합성을 어떻게.

## 8. 링크

- [boundary-gateway-schema.md](boundary-gateway-schema.md) §2 (`ModelCandidate`·`age.model_ref`) · §4
- [versioning-global-vs-per-boundary.md](versioning-global-vs-per-boundary.md) — 릴리스 selection/매니페스트
- [coherence-gate.md](coherence-gate.md) — 전역 후보와 정합성의 맞물림
- [node-graph-paradigm.md](node-graph-paradigm.md) — 노드 스왑 = what-if · 대안 그래프 브랜치
- 사례: [case-cambrian-base-correlation.md](case-cambrian-base-correlation.md) (model A–D)
