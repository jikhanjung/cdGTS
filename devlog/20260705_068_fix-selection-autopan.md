# 20260705_068 — 버그픽스: 좌-드래그 선택 박스 x 튐

> 증상: 왼클릭 드래그 선택 시 세로(y)는 정상인데 가로(x)가 두 값 사이로 튐(x1·x2 가 a,b↔b,c).

## 원인
React Flow 의 **selection auto-pan**(`autoPanOnSelection`, 기본 true). 포인터가 컨테이너 가장자리
(±40px) 근처면 `panBy` 로 viewport 를 이동시키고, 선택 박스 재계산 시
`screenStartX = rendererPointToPoint(startX, transform)` 가 **바뀐 transform 으로 재산출**돼 박스 x 가 튄다.
세로는 flow 컨테이너가 충분히 높아 위/아래 가장자리에 안 닿아 정상.

## 고침 (`Editor.jsx`)
- `autoPanOnSelection={false}` — 선택 중 viewport pan 금지 → screenStart 고정 → 박스 x 가 마우스에 선형 대응.
  (뷰포트 밖으로 끌어 선택하는 auto-pan 편의는 포기 — 안정성 우선.)

## 검증
- 프론트 빌드 클린. 백엔드 무관.
