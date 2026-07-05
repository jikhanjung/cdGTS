# 네이밍 — cdGTS

*[English](naming_en.md) · 한국어*

프로젝트 이름·표기에 대한 결정과 근거. (표기 규칙의 단일 출처.)

## 최종 표기

```markdown
# cdGTS

**Continuously Deployed Geologic Time Scale**

*A graph-based geologic time scale engine.*
```

- 제품명: **cdGTS**
- 풀네임: **Continuously Deployed Geologic Time Scale**
- 부제: *A graph-based geologic time scale engine*

## 기본 의미

cdGTS는 기존의 정적인 Geologic Time Scale을 표나 그림이 아니라 **노드와 의존성으로 구성된 실행 가능한 데이터/프로세스 엔진**으로 구현하려는 개념이다.

- 지질시대 단위와 경계(boundary)를 노드로 표현한다.
- 각 노드는 서로 의존 관계를 가진다.
- 하나의 경계나 단위가 변경되면 관련 노드들이 자동으로 갱신된다.
- 전체 GTS를 재계산하거나, 필요한 부분만 증분적으로 다시 생성할 수 있다.
- 결과적으로 GTS는 정적인 차트가 아니라 **지속적으로 갱신·배포되는 그래프 기반 시스템**이 된다.

## 이름 후보 비교

- **cdGTS — Continuously Deployed** *(채택)* — CI/CD에서 영감. "변경이 발생하면 자동으로 전파되고 갱신된다"는 핵심과 잘 맞는다. 개발자에겐 CI/CD·build system·dependency graph의 이미지를, 지질학자에겐 첫 등장 시 풀어 쓰면 충분히 전달된다.
- **ciGTS — Continuously Integrated** — 가능하나 "integration"은 여러 변경의 *병합* 뉘앙스가 강함. cdGTS의 핵심은 **변경 전파와 결과 재생성**이라 CI보다 CD가 적합.
- **cGTS** — 짧지만 `c`가 열려 있음(continuous/computational/composable/connected/compiled). 핵심 아이디어를 바로 전달하지 못함.

## 표기 규칙

- **geologic** (not *geological*). `geologic time`, `geologic time scale`, `geologic map`, `geologic unit` 처럼 **공식 용어·데이터·시스템 명칭**에 자연스럽다. *geological* 은 더 일반·설명적(geological history/evidence/interpretation).
- **Time Scale** — 두 단어로 (not *TimeScale*).
- 괄호 앞에는 **공백**: `cdGTS (Continuously Deployed Geologic Time Scale)`.
- 제목/부제는 **줄바꿈**하면 README·문서 첫머리가 깔끔하다.

## README 첫 문장 (권장)

> cdGTS is a graph-based geologic time scale engine that represents chronostratigraphic units and boundaries as interconnected nodes. Changes propagate through dependency relationships, allowing the geologic time scale to be rebuilt incrementally and reproducibly.

더 기술적으로:

> cdGTS models the Geologic Time Scale as an executable dependency graph, where boundaries, stages, series, systems, and higher-level units are represented as nodes whose derived properties can be updated automatically when upstream information changes.
