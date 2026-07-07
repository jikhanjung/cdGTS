# 20260707_094 — 노드 선택 시 Inspector 자동 표시 (0.1.25-WIP)

frontend 전용. 재시드 불필요.

## 선택 시 접힌 Inspector 자동 펼침 (Editor.jsx)
노드/그룹 선택 시 collapsed 상태의 Inspector 를 자동으로 표시. 선택 **식별자**(selectedId,
selectedGroupKeys[0])에만 키를 걸어, 노드 객체 갱신(편집·평가)엔 재실행 안 됨 → 수동으로 숨긴 뒤
같은 노드 유지 상태에서 무관한 변경으로 다시 열리지 않음. 선택 해제 시엔 펼치지 않음(숨김 유지).
