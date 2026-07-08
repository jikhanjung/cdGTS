# 20260708_114 — 모달 닫힘 버그 수정 (0.1.32)

로그인 팝오버에서 **패스워드 칸을 클릭하면 팝오버가 사라지는** 문제. 에디터의 bake/fork/info 다이얼로그도 같은 구조.

- **원인**: `modal-backdrop` 의 `onClick` 이 닫기를 담당했는데, 안쪽 `stopPropagation` 만으로는
  패스워드 매니저/오토필이 흘리는 클릭이나 **textarea 드래그-선택 후 바깥에서 손 뗀 경우**(release 가 backdrop 위)
  까지 못 막아 backdrop onClick 이 발동 → 닫힘.
- **수정**: **pointer-down 이 backdrop 자체에서 시작됐고 click 대상도 backdrop 일 때만** 닫음
  (`onMouseDown` 으로 origin 추적 + `e.target === e.currentTarget`). 필드 안에서 시작된 클릭/드래그는 절대 안 닫힘.
  LoginBar + Editor 3개 다이얼로그에 동일 적용.
