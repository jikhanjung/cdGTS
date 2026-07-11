# 20260711_R03 — FastAPI+uvicorn 전환 / 싱글유저 데스크톱 .exe 가능성 검토

> **성격: 가능성 타진(exploratory).** 이전을 결정한 게 아니라, "만약 옮긴다면 / 데스크톱 .exe 를 낸다면"의
> 비용·이득을 정리한다. 결론은 "지금 전면 이전은 불필요, 단 데스크톱 슬라이스는 별개로 유의미".

## 발단 (동기)

그래프를 만들고 노드를 추가/수정/삭제하는 편집 작업을, 멀티유저 CI 서버와 별개로 **개인 PC 에서 오프라인
단일 사용자로 돌리는 `.exe`** 로 배포하고 싶다. 겸사겸사 "**admin 을 거의 안 쓰는데 굳이 Django 를 쓸 이유가
있나? FastAPI+uvicorn 이면 .exe 도 쉽게 나올 텐데**" 라는 프레임워크 재검토.

## 사실 확인 (코드 기준)

- **모델 26개** (chrono 6·nodes 2·graph 5·engine 4·releases 7·accounts 1·references 1). 다만 **절반이
  멀티유저/릴리스/CI 쪽**(accounts·releases·chrono 레지스트리). **데스크톱 그래프 슬라이스는 ~7개**:
  `NodeType·Port` + `Graph·NodeInstance·Edge·NodeGroup·Gateway`.
- **Django 풀스택(템플릿·폼·서버뷰) 사용량 0** — `forms.py` 없음, 서버 템플릿은 SPA `index.html`뿐. 순수 SPA 백엔드.
- **데이터/운영 배터리는 실사용**: ORM+마이그레이션 · admin 등록 ~42개(그러나 **운영에서 거의 안 씀**) ·
  세션 인증+CSRF · 관리 명령 3개(`seed`·`seed_demo`·`run_worker`) · 자연키 fixture seed.
- **프레임워크 무관 코드**: `engine/evaluate.py`(293)+`engine/kernels.py`(260)=**553줄, numpy/scipy 순수 파이썬,
  Django 의존 0**.

## 핵심 논점

### 1. 패키징 축에서는 FastAPI 가 실제로 유리

FastAPI/Django 둘 다 "로컬 서버 + PyInstaller"지만, **Django 를 얼리는 게 더 성가심**: `django.setup()`·
settings 모듈 탐색·app registry·런타임 migrate·collectstatic/staticfiles·management command·admin·template
loader 가 hidden-import/데이터 번들 이슈로 옴. FastAPI+uvicorn 은 ASGI 앱 하나라 훨씬 납작. 사용자가 이미
FastAPI .exe 경험 있음 → 이 축은 FastAPI 손.

### 2. "admin 안 쓰면 Django 명분?" — 대체로 타당

- 풀스택 절반은 어차피 0. **admin 이 사실상 마지막 Django-특이 lock-in 이었는데 그걸 안 씀** → consolidate
  on FastAPI 는 방어 가능한 판단(실수 아님).
- 남는 실질 가치 = **ORM + 마이그레이션**(스키마 진화·관계 무결성; 이번 세션 gateway CASCADE 가 그 예). 단
  **SQLAlchemy + Alembic 으로 대체 가능 → 막는 요인이 아니라 취향**.
- 참고: 불편의 정체가 DRF ceremony 였다면 **django-ninja**(Pydantic·OpenAPI·FastAPI 문법 + ORM/마이그레이션/
  admin/인증 유지)가 재작성 없는 중간해였을 것. 그러나 이번 동기는 DRF 가 아니라 admin/why-Django 라 해당 약함.

### 3. 비용은 "테이블"이 아니라 "이미 디버깅된 로직 + 테스트"

- **공짜로 이전**: 엔진(553줄) verbatim, React 프론트 100%(같은 JSON 계약이면 `api.js` 무변경).
- **다시 표현해야(재발명 금지, 이식)**:
  - **그래프 왕복/검증** `graph/serializers.py _replace_topology` — 자기참조 group FK 2-pass forward-ref ·
    순환 검사 · **gateway 보존**(이번 세션 gateway-wipe 버그 잡은 곳). 버그 숨는 지점.
  - **seed 시스템** — 자연키 2-pass(순환 FK).
  - **인증/소유권 쿼리셋**(멀티유저 서버 유지 시).
  - **166 테스트 중 API-결합분** 재작성(엔진 테스트는 생존).

## 권고 — big-bang 말고 "데스크톱 먼저"

원하는 것 = (a) 쉬운 .exe (b) Django 를 공짜로 안 이기. **가장 낮은 위험**의 순서:

1. **데스크톱 FastAPI 앱을 먼저 만든다.** 작게(≈7테이블 또는 그래프=JSON-doc 저장), 엔진·프론트 재사용,
   그래프 왕복 로직을 **여기서 한 번** Pydantic 으로 이식. → `.exe` 즉시 확보 + FastAPI/scipy 패키징을 실도메인 검증.
2. **멀티유저 서버는 당분간 Django 유지.** 돌아가고 테스트도 있음.
3. 데스크톱이 만족스러우면 → 서버 이전 시 **위험한 그래프-로직 이식이 이미 1번에서 끝나 있어** 재사용 수준.
   이 데스크톱 앱이 곧 (선택적) 서버 마이그레이션의 **씨앗**.

이러면 "기능 멈추고 포팅·테스트 재획득"의 big-bang 없이, 프레임워크 질문을 **경험적으로** 판정하고 .exe 를
바로 얻는다.

## 아키텍처 메모 (엔진 중복 방지)

서버(Django)·데스크톱(FastAPI)이 둘 다 엔진을 쓰면 **`engine/`(+ 그래프 왕복 로직)을 공유 패키지**로 두고
양쪽이 import → 포크 없이 한 번만 유지. 데스크톱 = "엔진+프론트를 공유하는 형제 앱", cdGTS 의 교체가 아님.

## 결정 상태 / 다음

- **결정 없음.** 전면 전환은 지금 불필요(수지 안 맞음). **데스크톱 FastAPI 슬라이스는 별개로 유의미** —
  하고 싶어지면 위 순서로.
- 착수 시 다음 산출물부터: 프론트 `api.js` 기대 **엔드포인트 계약 목록** · 엔진 재사용 지점 · 그래프 저장
  선택(경량 SQLAlchemy 7테이블 vs JSON-doc) · single-user 진입점 · PyInstaller 유의점.
- 관련: [R02](20260711_R02_source-code-review.md)(코드 구조 리뷰) · cross-cutting 엔진/serializer 는 R02 §파일별 인상 참고.
