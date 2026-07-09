cdGTS Base of Cambrian Vertical Slice 정리
작성일: 2026-07-09  
주제: Base of Cambrian boundary를 cdGTS의 첫 번째 상세 working graph 사례로 구성하기
---
1. 배경
cdGTS는 Continuously Deployed Geologic TimeScale의 약자로, 지질시대표를 단순히 그림으로 그리는 도구가 아니라, 지질시대표가 어떻게 만들어지고 갱신되는지를 노드 기반 그래프로 표현하고, 이를 bake하여 최종 time scale chart를 산출하는 것을 목표로 한다.
TimeScale Creator가 이미 정리된 GTS age model과 curated dataset을 이용해 figure/chart를 그려주는 도구라면, cdGTS는 그 뒤에 있는 다음 질문을 다룬다.
> 왜 이 boundary가 이 age를 가지는가?  
> 어떤 논문, section, datum, radiometric age, correlation logic이 그 값을 지지하는가?  
> 그 reasoning을 기계가 읽고 재현할 수 있는가?
현재 단계에서는 여러 release/version을 동시에 관리하는 구조까지 바로 구현하기보다는, 하나의 boundary를 끝까지 작동하는 상세 그래프로 만드는 것이 우선이다.
---
2. 첫 번째 vertical slice로 Base of Cambrian을 선택하는 이유
`Base of Cambrian`은 cdGTS의 첫 번째 상세 사례로 적합하다.
이유는 다음과 같다.
상징성이 크다.  
Precambrian–Cambrian boundary는 International Chronostratigraphic Chart에서 매우 중요한 경계다.
다양한 evidence type을 연결할 수 있다.  
Treptichnus pedum FAD, δ13C excursion / BACE, U-Pb ash-bed ages, regional stratigraphic sections 등이 함께 등장한다.
cdGTS의 장점을 보여주기 좋다.  
단순히 `538.8 Ma`라는 값을 표시하는 것이 아니라, 그 값이 어떤 evidence와 process를 거쳐 도출되었는지 그래프로 보여줄 수 있다.
현재 이미 초기 subgraph가 존재한다.  
현재 구현에서는 `T. pedum FAD`, `Oman Ara Group age`, `Namibia ash-bed U-Pb`, `Siberia ash-bed U-Pb` 등이 `Global δ13C age model` process node로 연결되어 `Base of Cambrian` boundary age를 산출하는 원형이 만들어져 있다.
---
3. 현재 구현의 개념 구조
현재 subgraph의 개념적 흐름은 다음과 같다.
```text
T. pedum FAD
Oman Ara Group age
Namibia ash-bed U-Pb age
Siberia ash-bed U-Pb age
        ↓
Global δ13C age model / correlation process
        ↓
Boundary age estimate
        ↓
Base of Cambrian boundary
        ↓
Cambrian age subdivisions
        ↓
ICC-like chart output
```
현재 구조는 데모용으로 충분히 좋은 방향이지만, 실제 cdGTS의 핵심 기능을 보여주기 위해서는 중간 층을 조금 더 세분화할 필요가 있다.
---
4. 발전 방향: 단순 age node에서 provenance graph로
현재의 `Oman Ara Group age 538.8 Ma`, `Namibia ash-bed U-Pb 538.6 Ma`, `Siberia ash-bed U-Pb 539 Ma` 같은 node는 이후 다음과 같이 더 풀어낼 수 있다.
```text
Publication
  ↓
Stratigraphic section
  ↓
Horizon / bed / sample
  ↓
Radiometric date or chemostratigraphic signal
  ↓
Local age-depth / correlation model
  ↓
Boundary age estimate
```
즉, 단순히 “어떤 age 값”이 아니라 다음 정보를 그래프 안에 넣는 것이 중요하다.
그 값이 어느 논문에서 나왔는가?
어느 stratigraphic section의 어느 horizon인가?
sample 또는 ash bed의 위치는 어디인가?
그 age가 boundary보다 위인지 아래인지?
fossil datum 또는 δ13C signal과 어떤 관계인가?
age-depth model 또는 cross-section correlation을 통해 어떻게 boundary age로 전달되는가?
---
5. 권장 node type
Base of Cambrian working graph에서는 처음부터 너무 많은 node type을 만들 필요는 없지만, 최소한 다음 정도는 분리하는 것이 좋다.
```text
Publication
Stratigraphic Section
Horizon / Bed / Sample
Datum / Signal
Radiometric Age
Age-depth Model
Correlation / Calibration Process
Boundary Age Estimate
Boundary
Time Period / Time Span
Chart Output
```
각 node type의 역할은 다음과 같다.
Node type	역할
Publication	논문, 책 장, 보고서, GSSP 문헌 등 provenance의 출처
Stratigraphic Section	Oman, Namibia, Siberia 등 실제 층서 단면
Horizon / Bed / Sample	age 또는 datum이 관찰된 구체적 층준
Datum / Signal	T. pedum FAD, δ13C excursion, isotope event 등
Radiometric Age	U-Pb age, uncertainty, calibration standard 등
Age-depth Model	section 내에서 depth와 age를 연결하는 process
Correlation Process	여러 section 또는 signal을 연결하는 process
Boundary Age Estimate	특정 boundary에 대한 수치 age 추정값
Boundary	Base of Cambrian 같은 chronostratigraphic boundary 자체
Time Period / Time Span	Cambrian period 등 chart를 구성하는 시간 단위
Chart Output	bake된 ICC-like chart 결과물
---
6. Boundary node는 얇게 유지하기
`Base of Cambrian` boundary node에 모든 정보를 직접 붙이면, boundary node가 너무 비대해질 수 있다.
따라서 boundary node는 다음처럼 얇은 중심 객체로 유지하는 것이 좋다.
```text
Boundary: Base of Cambrian
  receives:
    - boundary\_age\_estimate
    - formal\_definition
    - correlation\_summary
```
세부 evidence는 별도의 subgraph 안에 둔다.
```text
Subgraph: Base Cambrian · δ13C calibration
  contains:
    - publications
    - sections
    - horizons
    - samples
    - age anchors
    - fossil / isotope signals
    - correlation logic
    - inference process
```
이렇게 하면 top-level graph는 계속 읽기 쉽고, 세부 provenance가 필요할 때만 subgraph 내부로 들어갈 수 있다.
---
7. Subgraph의 역할
현재 cdGTS에는 node group / subgraph 기능이 이미 구현되어 있다. 이를 활용하면 전체 구조를 다음처럼 계층화할 수 있다.
```text
Top-level graph
  = ICC 전체 조립도

Period / system subgraph
  = Cambrian, Ordovician, Silurian 등 age subdivisions

Boundary evidence subgraph
  = Base of Cambrian처럼 특정 boundary의 evidence와 inference logic

Chart output node
  = bake된 결과
```
Base of Cambrian의 경우, top-level에서는 다음처럼 간단히 보이면 된다.
```text
Base Cambrian · δ13C calibration group
        ↓
Base of Cambrian boundary
        ↓
Cambrian age subdivisions
        ↓
ICC chart
```
그리고 group 내부에서는 자세한 evidence graph가 펼쳐진다.
---
8. Group / subgraph 명명 규칙 제안
임시 이름인 `Group 15` 대신, 의미가 드러나는 이름을 쓰는 것이 좋다.
예:
```text
Base Cambrian · δ13C calibration
Base Cambrian · evidence package
Base Cambrian · GSSP definition
Base Cambrian · age-depth model
```
내부 ID는 다음처럼 체계적으로 관리할 수 있다.
```text
evidence/base-cambrian/global-d13c-age-model
evidence/base-cambrian/treptichnus-pedum
calibration/base-cambrian/ash-bed-upb-anchors
assembly/cambrian/age-subdivisions
```
---
9. Boundary Age Estimate 객체
현재 `538.795284 Ma`처럼 계산값이 바로 boundary node로 전달되고 있지만, 실제 구조에서는 단순 scalar가 아니라 `BoundaryAgeEstimate` 객체로 다루는 것이 좋다.
예:
```yaml
boundary\_age\_estimate:
  target: base\_cambrian
  value\_ma: 538.795284
  display\_value\_ma: 538.8
  uncertainty\_ma: null
  method: global\_delta13c\_correlation
  signals:
    - treptichnus\_pedum\_fad
    - delta13c\_excursion
  anchors:
    - oman\_ara\_group\_age
    - namibia\_ash\_bed\_upb
    - siberia\_ash\_bed\_upb
  status: working\_demo
  precision\_note: computed value should be rounded for release/chart display
```
이렇게 하면 내부 계산값과 chart 표시값을 분리할 수 있다.
```text
computed\_age = 538.795284 Ma
display\_age  = 538.8 Ma
adopted\_age  = 538.8 Ma ± ?
```
현재 단계에서는 여러 release/version을 구현하지 않아도 되지만, 이런 객체 구조를 두면 나중에 release profile을 추가하기 쉽다.
---
10. 지금 단계에서는 version보다 working graph가 우선
장기적으로는 GTS2020, 최신 ICS chart, cdGTS experimental release, historical release 등을 나누는 것이 필요할 수 있다.
하지만 현재 단계에서는 다음이 우선이다.
```text
하나의 boundary에 대해
논문 → section → horizon/sample → datum/age anchor → correlation/model → inferred age → boundary node
까지 이어지는 working graph를 만든다.
```
즉, 지금은 version/release graph를 복잡하게 만들기보다 다음 목표에 집중하는 것이 좋다.
하나의 상세한 evidence subgraph
하나의 boundary age estimate
하나의 boundary node
하나의 period assembly
하나의 baked chart output
---
11. Base of Cambrian demo graph v0.1 제안
첫 번째 working demo는 다음 구성으로 만들 수 있다.
```text
Base of Cambrian demo graph v0.1

1. Formal boundary definition node
2. T. pedum FAD datum node
3. δ13C / BACE signal node
4. Oman / Namibia / Siberia section nodes
5. U-Pb age anchor nodes
6. Horizon / bed / sample nodes
7. Correlation / age-transfer process node
8. Boundary age estimate node
9. Base of Cambrian boundary node
10. Cambrian age subdivision group
11. ICC-like chart output node
```
이 중에서 v0.1에서 반드시 필요한 것은 다음이다.
```text
Publication
Section
Horizon / sample
Datum or signal
Radiometric age
Correlation process
Boundary age estimate
Boundary
```
이 정도만 있어도 cdGTS의 핵심 개념을 충분히 보여줄 수 있다.
---
12. TimeScale Creator와의 차별점
TimeScale Creator는 다음에 강하다.
```text
curated GTS age model + built-in/event data
        ↓
publication-quality chart / figure
```
cdGTS는 다음을 목표로 한다.
```text
published evidence + stratigraphic relations + calibration logic
        ↓
boundary age inference
        ↓
time scale assembly
        ↓
baked chart + provenance
```
따라서 Base of Cambrian vertical slice가 완성되면 cdGTS의 차별점은 매우 명확해진다.
> TimeScale Creator는 `Base of Cambrian = 538.8 Ma`라고 표시된 chart를 잘 그려주는 도구이고,  
> cdGTS는 왜 그 값이 나왔는지 추적 가능한 evidence graph를 만들 수 있는 시스템이다.
---
13. 다음 작업 제안
13.1 Graph schema 최소 확정
Base of Cambrian v0.1에 필요한 최소 node schema를 먼저 고정한다.
```text
Reference / Publication
Section
Horizon
Datum
RadiometricAge
CorrelationProcess
BoundaryAgeEstimate
Boundary
TimeSpan
```
13.2 Base of Cambrian evidence package 구성
현재의 `Group 15`를 다음과 같은 의미 있는 group으로 바꾼다.
```text
Base Cambrian · δ13C calibration
```
13.3 scalar age를 estimate object로 변경
현재 process node의 출력값을 단순 Ma 값이 아니라 `BoundaryAgeEstimate` 객체로 만든다.
13.4 chart bake와 연결
`BoundaryAgeEstimate`가 `Base of Cambrian` boundary node에 전달되고, 이 값이 `Cambrian age subdivisions`와 최종 ICC chart에 반영되는지 확인한다.
13.5 provenance preview 추가
boundary node 또는 estimate node를 클릭했을 때 다음 요약이 보이면 좋다.
```text
Base of Cambrian
Age: 538.8 Ma
Method: global δ13C correlation
Signals: T. pedum FAD, δ13C excursion
Anchors: Oman, Namibia, Siberia U-Pb ages
Status: working demo
```
---
14. 한 문장 요약
현재 cdGTS의 다음 마일스톤은 전체 ICC를 얕게 채우는 것이 아니라, Base of Cambrian 하나를 대상으로 source literature, stratigraphic section, datum, age anchor, correlation process, boundary age estimate, chart output까지 이어지는 깊은 working graph를 완성하는 것이다.
