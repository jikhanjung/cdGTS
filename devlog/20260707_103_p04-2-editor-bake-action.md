# 20260707_103 — P04.2: Editor Bake 액션 (프론트)

[P04](20260707_P04_editor-bake-vault-restructure.md) 2단계. Editor에서 **Bake**를 Save/Evaluate/Verify와
구분되는 1급 액션으로 노출.

## 변경

- **api.js**: `bakeGraph(id, label)` — label body 전송(없으면 서버 자동 명명). `suggestBakeName(id)` —
  GET로 편집 가능한 기본 이름(`{suggested}`) 프리필용.
- **Editor.jsx**:
  - 툴바에 **`Bake…`** 버튼(accent). Save(PUT)·Evaluate·Verify vs published과 나란히.
  - `onOpenBake` — dirty면 **먼저 저장**(bake는 서버 그래프를 평가하므로) → 이름 제안 fetch → 다이얼로그 오픈.
  - **Bake 다이얼로그** — 편집 가능한 이름 입력(제안 프리필), Enter/버튼 확정, Cancel. 확정 시
    `bakeGraph` → `Baked → <version> (<n> boundaries) · saved to Vault` 상태 표시.
  - `onBaked(release)` prop 배선(P04.3에서 App이 Vault로 이동시키는 콜백; 지금은 옵션).
- **index.css**: `.bake-btn`(accent) + `.modal-backdrop`/`.bake-dialog`/`.bake-name`/`.bake-actions`.

## 검증

`npm run build` 통과(202 modules). Bake는 항상 **새 불변 Release** 생성(P04.1) → 덮어쓰지 않음.

## 다음

P04.3 — nav를 Editor·**Vault** 2개로 축소, Vault 허브(Release 목록 + Table/Chart/Narrative 토글 + Diff),
`onBaked` → Vault 진입 배선. 이후 P04 묶어 배포(스키마 migration 포함).
