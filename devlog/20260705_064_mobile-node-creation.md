# 20260705_064 — 모바일 노드 생성 (탭-투-추가 + 롱프레스 메뉴)

> 폰에서 노드 생성이 안 됐다 — 생성은 HTML5 드래그앤드롭(터치 미지원), 컨텍스트 메뉴는 우클릭(터치 없음).
> 모바일 편집 완성.

## 한 일 (`Editor.jsx` · `index.css`)
- **탭-투-추가** — 터치에서 팔레트 항목 탭 → 배치 대기(pending, 서랍 닫힘 + 안내 배너), 캔버스 탭 → 그 자리에 생성.
  노드 생성 로직을 `addNodeAt(slug, position)` 공통 함수로(데스크톱 드롭·터치 탭 공용). 배너에 취소 버튼. armed 팔레트 하이라이트.
- **롱프레스 컨텍스트 메뉴** — `.flow` touchstart ≈0.5s(이동 없으면) → `elementFromPoint` 로 노드/그룹/빈곳 판별해 메뉴.
  touchmove/touchend 는 타이머 취소.
- **롱프레스 직후 click 삼킴** — 손 떼는 순간의 합성 click 이 백드롭에 닿아 메뉴가 즉시 닫히는 문제를,
  `lpFiredRef` 로 1회 삼켜 방지(onPaneClick·backdrop 양쪽 가드).
- 데스크톱은 종전대로(드래그앤드롭·우클릭). 팔레트 onClick 은 `IS_TOUCH` 일 때만 arm.

## 검증
- 프론트 빌드 클린. 백엔드·시드·마이그레이션 무관. **실기기 육안 확인 권장**(탭 배치·롱프레스 메뉴).
- `.canvas` position:relative 는 place-banner 앵커용 — 기존 오버레이(ctx-menu/backdrop=fixed, results=flex)에 영향 없음 확인.

## 남은 모바일 항목
- 없음(핵심 완료). 필요 시 롱프레스 시간·햅틱 등 미세조정.
