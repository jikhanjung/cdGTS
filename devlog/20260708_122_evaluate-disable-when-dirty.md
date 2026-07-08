# 20260708_122 — 미저장이면 Evaluate 비활성 + 데모 노드 younger-위로 배치

사용자가 "order edge 지우고 evaluate 해도 warn 그대로"를 겪음 → **저장을 안 해서**였다. Evaluate 는 서버에
**저장된** 그래프를 평가하므로, 에디터에서 지운 edge 가 반영되려면 Save 가 먼저여야 한다. (backend 확인:
order edge 삭제 후 재평가 시 L1b·L2 = skip — 설계대로 정상.)

## 변경

**1) dirty 면 Evaluate/Verify 비활성 (Editor.jsx)**
- Actions ▾ 의 **Evaluate**·**Verify vs published** 를 `disabled={dirty}`. 툴팁: "Save first — runs on the saved
  graph, not your unsaved edits". 둘 다 서버 저장본 기준이라 미저장 상태 평가는 오해를 부름.
- Save 는 이미 저장 후 자동 재평가(silent)하므로, 저장하면 결과가 바로 최신화됨.

**2) 데모 노드 younger-위로 (seed_demo.py)**
- 위→아래 = younger→older(ICC 관례): **Base Anisian(247) · Olenekian unit · Base Olenekian(249)** 세로 정렬
  (x=120 한 열, y=40/160/280). order edge 인터리브도 이 방향과 일치(younger 포트=위).

frontend 빌드 통과. 재시드로 위치 반영.
