# docs/archive — 보관된(superseded) 문서

구현으로 대체됐지만 **역사적 기록**으로 남기는 브레인스토밍/설계 문서를 모읍니다.
여기 있는 내용은 **현재 구현의 근거가 아닙니다** — 현행 문서를 참조하세요.

- 현재 척추: [../tier-category-model.md](../tier-category-model.md) · [../concept-map.md](../concept-map.md) · [../app-architecture.md](../app-architecture.md)
- 진입점: [../concept-map.md](../concept-map.md)

## 목록

- [idea-layer-model-0-6.md](idea-layer-model-0-6.md) — `idea.md` §5의 원래 선형 **Layer 0–6** 데이터 모델. 구현에서
  **티어 × 카테고리 + 16 노드 타입**으로 접혔다. 서사적 읽기 순서로만 유효.

## 제자리 배너(이동 안 함)

인바운드 링크가 많아 옮기지 않고 문서 상단에 "superseded" 배너만 단 것들:
- [../boundary-gateway-schema.md](../boundary-gateway-schema.md) — 경계 게이트웨이 스키마 v0(YAML 초안). 실제 구현은
  경계를 단일 게이트웨이 레코드가 아니라 그래프의 `boundary` 노드 + `published-age` leaf + `order` edge 로 표현.
  대체: `releases/models.py` · [../boundary-span-duality.md](../boundary-span-duality.md) · [../app-architecture.md](../app-architecture.md).
