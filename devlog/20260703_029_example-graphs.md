# 20260703_029 — 예제 네트워크 3종 (세 케이스 시드)

> 브레인스토밍의 세 케이스 문서를 실제 노드 그래프로 시드. `graph/fixtures/example_graphs.json`.

## 왜

docs 의 세 케이스([GSSA](../docs/case-precambrian-gssa.md)·[P–T](../docs/case-permian-triassic.md)·
[캄브리아 base](../docs/case-cambrian-base-correlation.md))는 cdGTS 데이터 모델의 세 축을 대표한다.
이를 에디터에서 바로 열어보고 평가할 수 있는 **예제 그래프**로 넣었다. 세 경계 시드와 1:1 대응:
`base-proterozoic` · `base-triassic` · `base-cambrian`.

## 세 예제 (기존 12 NodeType 만으로 구성)

| 그래프 | 구조 | 게이트웨이 출력 | 문헌값 |
|---|---|---|---|
| `example-gssa-precambrian` | `pin(2500)` → GW | **2500 (exact, ±없음)** | 2500 Ma, 오차 없음 |
| `example-permian-triassic` | bed25·bed28 `radiometric-uPb` → `age-depth-model`(linear) → GW | **251.902 ± 0.024** | Burgess+2014 = 251.902 ± 0.024 |
| `example-cambrian-base` | Oman·Namibia·Siberia `radiometric-uPb` + FAD `biostratigraphic` → `cross-section-correlation` → GW | **538.80 ± 0.54** | ICS 538.8 ± 0.6 |

- **화살표 방향 대조**가 그대로 드러난다: GSSA 는 숫자=정의(leaf), P–T·캄브리아는 데이터→모델→숫자.
- P–T: bed25(depth −0.14)·bed28(+0.08)·target 0.0 으로 두면 linear 보간이 **문헌 251.902 ± 0.024 를 정확히 재현**.
- 캄브리아: 상관 노드가 타 대륙 anchor 를 역분산 결합(숫자의 주경로가 correlation = tier b). FAD 는
  signal(연대측정 불가)로 상관에만 연결(`calibration-transfer` 엣지). Namibia/Siberia 값은 예시·근사(note 명시).

## 검증
- loaddata 21객체(그래프 3·노드 9·엣지 6·게이트웨이 3). 각 그래프 evaluate → 위 표의 값,
  정합성 인증서 3건 모두 pass.
- `Graph.created_at`(auto_now_add)은 loaddata 가 채우지 않아 fixture 에 타임스탬프 명시.

## 시드 편입
- 최초 시드 명령에 `example_graphs` 추가(deploy/README). node types·boundaries 뒤에 로드(FK 의존).
