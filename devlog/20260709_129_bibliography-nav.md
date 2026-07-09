# 20260709_129 — Bibliography nav (레퍼런스 레지스트리 목록·편집)

레퍼런스 노드([127](20260709_127_reference-nodes.md)) · bake bibliography([128](20260709_128_bake-bibliography.md))의
후속. 지금까지 레퍼런스는 노드 인스펙터에서 인라인 생성만 됐고, 수정/삭제 UI 가 없어 권한(생성자·staff)이
API/admin 기준으로만 걸렸다. 상단 nav 에 **Bibliography** 서피스를 추가해 전체 레지스트리를 목록·검색하고
상세 편집(CRUD)까지 UI 로 노출한다.

## 프론트

- **`Library.jsx`** (신규) — 전역 레퍼런스 레지스트리 관리 뷰.
  - 목록: 검색 가능한 테이블(저자·연도·제목·container / DOI·URL 링크 ↗ / kind / added by).
    검색은 slug·doi·title·authors·container·year 대상.
  - 상세 편집: 행 클릭 → 모달(slug·title·authors·year·container·doi·kind·url·note).
    `+ New reference` 생성 · Save(PATCH) · Delete.
  - 권한 미러링: 생성은 로그인 필요, Edit/Delete 는 **생성자 또는 staff** 만 활성(그 외엔 동일 모달을
    read-only "View" 로 — fieldset disabled, Save/Delete 숨김). slug 는 생성 후 잠금(자연키).
  - **409 cited-block** 처리: 그래프가 인용 중인 레퍼런스 삭제 시 백엔드 메시지 + 인용 그래프 목록 표기,
    항목 유지.
- **`App.jsx`** — nav 에 `Bibliography` 버튼 + `library` 뷰 분기, `user`(whoami) 전달로 권한 게이팅.
- **`api.js`** — `updateReference`(PATCH) · `deleteReference`(DELETE) 추가.
- **`index.css`** — 검색창 · danger 삭제 버튼 · 테이블 셀 크기.

Vault 의 "References" 탭(릴리스별 bake 참고문헌, [128])과는 별개 — 이쪽은 편집 가능한 **전역 라이브러리**.

## 검증

- 프론트 `npm run build` 정상(210 modules). 백엔드 변경 없음(엔드포인트는 [127]에서 이미 배포됨).
- 배포: 테스트서버 **0.1.43** (web + worker).

## 메모 / 다음

- 후속 후보: Crossref DOI 자동 메타데이터 채우기 · 중복 DOI 병합 · 레퍼런스별 "인용하는 그래프" 목록.
