# 20260703_014 — Django 개발 환경 뼈대 (브레인스토밍 → 코드 착수)

> 문서 저장소에서 **첫 실행 가능한 코드**로 넘어간 라운드. 앱 모델은 아직 없음(뼈대만).

## 결정 (사용자 확인)

- **DB**: dev 는 **SQLite** 로 시작. 공간(GSSP 지점) 기능 착수 시 PostGIS 로 전환.
  (로컬 `psql` 미설치 — PostGIS 는 추후 Docker `postgis/postgis` 로.)
- **범위**: 이번엔 **환경 뼈대만** — config 프로젝트 + 설정 + runserver 부팅 확인.
  경계 게이트웨이 스키마 v0 → Django 모델 이식은 다음 라운드.
- **스택**: 잠정 방향(TODOs §0)을 확정 착수. **Django 5.2.12**, fsis2026 패턴 재사용.

## 한 일

### 1. 프로젝트 스캐폴드
- `django-admin startproject config .` — fsis2026 과 동일한 `config/` 레이아웃(루트에 `manage.py`).
- 기존 빈 venv `/home/jikhanjung/venv/cdGTS` 에 설치.

### 2. 의존성
- `requirements.txt` — Django 5.2.12, python-decouple 3.8, PyYAML 6.0.1(스키마 예시가 YAML).
- `requirements-dev.txt` — pytest, pytest-django.

### 3. settings 조정 (fsis2026 관행)
- `SECRET_KEY`/`DEBUG`/`ALLOWED_HOSTS`/`DATABASE_PATH` 를 **python-decouple** 로 외부화
  (dev 기본값 포함 — `.env` 없이도 동작).
- SQLite `OPTIONS`: `timeout=20`, `transaction_mode=IMMEDIATE`.
- 로케일 `ko-KR` / `Asia/Seoul`.
- 주석으로 "공간 기능 착수 시 PostGIS 전환" 명시.

### 4. 부수 파일
- `.gitignore`(Python/Django/venv/`.env`/sqlite), `.env.example`(템플릿), 로컬 `.env`(gitignore).

## 검증

- `manage.py check` → 이슈 0.
- `migrate` → auth/sessions/admin 기본 마이그레이션 적용, `db.sqlite3` 생성.
- `runserver` → **HTTP 200**(환영 페이지) 확인 후 종료.
- `.env`·`db.sqlite3` gitignore 정상 작동 확인.

## 커밋

- (이 커밋) Django 뼈대(config/·manage.py·requirements·settings·gitignore·.env.example) + devlog 014.

## 다음 후보

- 첫 앱 `boundaries` 생성 + 스키마 v0(`Boundary`·`ModelCandidate`·`Release`·`Clamp`·`identity.lineage`)
  을 모델로 이식. → HANDOFF 다음작업, TODOs §0 데이터 직렬화 포맷과 연결.
- PostGIS 전환 시점(공간 차원 착수) 판단.
