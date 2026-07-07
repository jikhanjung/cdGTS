# 20260708_112 — Editor 툴바 정리 (0.1.29 · 0.1.30)

예제 드롭다운 옆에 기능 버튼들이 흩어져 어수선하다는 피드백. 정리:

- **`Actions ▾` 드롭다운**으로 5개 버튼 접기 — Fork·Evaluate·Verify·Bake·Propose 를 하나의 메뉴로.
  구분선 그룹핑: (Evaluate·Verify) / (Bake…·Propose…) / (Fork). 권한·상태별 노출·비활성·툴팁은 그대로 유지.
- **뷰 토글 우측 정렬** — `flex` 스페이서로 Results·Properties 를 툴바 오른쪽 끝으로.
- **하단 status line** — 툴바 우측에 붙어 있던 "Auto-evaluated…" 상태 텍스트를 캔버스 아래 얇은 바로 이동
  (clean 초록 / dirty 주황 점 + 최신 메시지, 비면 "Ready"). `.editor-statusbar` 신설.
- **Save 라벨** — `Save (PUT)` → `Save`(구현 세부 노출 제거).
- 그룹 만들기/해제는 **선택 컨텍스트 편집 동작**이라 인라인 유지(그래프 단위 Actions 메뉴와 성격 분리).

순수 프론트 변경. 테스트 서버 0.1.29(툴바·status)·0.1.30(Save 라벨) 배포.
