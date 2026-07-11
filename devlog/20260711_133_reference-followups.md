# 20260711_133 — 레퍼런스 후속 (노드 DOI 링크 · Crossref 자동 메타데이터 · narrate 참고문헌)

레퍼런스 노드([127](20260709_127_reference-nodes.md)) · bake→bibliography([128](20260709_128_bake-bibliography.md)) ·
Bibliography nav([129](20260709_129_bibliography-nav.md))의 후속 묶음. TODOs "레퍼런스 후속" 항목 3종을 구현한다.

## 1. 노드 얼굴 DOI 직접 클릭 (프론트)

- **`CdgtsNode.jsx`** — `reference` 노드 얼굴의 DOI 를 텍스트 → **클릭 가능한 링크**(`ref.link`, 새 탭).
  React Flow 드래그와 충돌하지 않도록 `nodrag` 클래스 + `onMouseDown/onClick` stopPropagation.
  DOI 없고 URL 만 있으면 `link ↗`, 둘 다 없으면 링크 없음.
- **`index.css`** — 얼굴 내 `a.doi` 링크 스타일(amber, hover 밑줄).

## 2. Crossref DOI 자동 메타데이터 (백+프론트)

DOI 하나로 title·authors·year·container·kind 를 채운다. 외부 API 는 **서버 사이드 프록시**로 감싼다
(CORS·레이트리밋 회피, polite-pool User-Agent 부여, 오픈 프록시 방지 위해 로그인 필수).

- **`references/crossref.py`** (신규) — stdlib `urllib` 만으로 `api.crossref.org/works/{doi}` 조회 →
  Reference 필드로 정규화. `normalize_doi`(https://doi.org/ 프리픽스 제거) · `_format_authors`
  (`Family, G. & …`, seed 관례) · `_year`(issued→published→created 폴백) · `_suggest_slug`
  (`firstauthor-year`) · Crossref type→우리 kind 매핑. 404/타임아웃/네트워크 오류를 `CrossrefError(status)`로.
- **`references/views.py`** — `@action GET /api/references/crossref/?doi=…`. 로그인 필요(생성과 동일 기준),
  `CrossrefError` → 그대로 상태코드로.
- **프론트** — `api.js` `crossrefLookup(doi)`. 인스펙터 인라인 추가 폼(`Inspector.jsx NewReferenceForm`)과
  Bibliography 레지스트리 다이얼로그(`Library.jsx RefDialog`) 양쪽에 **"Fetch" 버튼** — DOI 입력 후 누르면
  필드 자동 채움(신규일 때 slug 는 제안값, 기존 항목은 자연키라 slug 미변경).

## 3. narrate 참고문헌 자동 삽입 (백+프론트)

- **`releases/views.py ReleaseNarrateView`** — narrate 응답에 `bibliography` 추가. 릴리스 레코드에 bake 시
  스냅샷된 `references`(cite provenance) 를 dedup 해 `ReferenceSerializer` 로 직렬화. references 액션과 동일 소스.
- **`Narrate.jsx`** — 서술 문서 말미에 **References 섹션**(번호 목록: authors·year·title·container·DOI 링크).

## 검증

- 백엔드 `pytest` **164 passed**(기존 159 + Crossref 신규 5: normalize/매핑/404/blank/액션 권한).
  Crossref 테스트는 `urllib.request.urlopen` monkeypatch 로 네트워크 없이. narrate 테스트에 `bibliography` 키 단언 추가.
- 프론트 `npm run build` 정상(210 modules).
- 배포: 테스트서버 **0.1.49** (web + worker). ⚠️ 컨테이너에 외부망(api.crossref.org) 도달 필요 — 없으면 Fetch 는
  502 로 우아하게 실패(수동 입력 폴백).

## 메모 / 다음

- 남은 레퍼런스 후속: **narrate(GTS) 본문에 인용 마커** 삽입(현재는 참고문헌 목록만), Crossref 중복 DOI 병합,
  reference 노드 인스펙터에서 title 도 클릭 링크화.
