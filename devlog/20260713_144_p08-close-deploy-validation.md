# 20260713_144 — P08 마무리: 실배포 검증 + 워커 핫픽스 + 문서 정합

[P08](20260713_P08_deploy-data-contract-retrofit.md)(배포·데이터 계약 retrofit)을 종결하는 기록.
설계·구현은 [140](20260713_140_seed-replace-lane-boundary.md)~[143](20260713_143_git-free-deploy.md) 에서
착지했고, 이 라운드는 **0.1.56~0.1.60 실배포로 파이프라인 전 구간을 실증**하며 나온 두 갭을 닫고 문서를 맞췄다.

## 실배포 검증 (0.1.56 → 0.1.60)

- **0.1.56** — P08.1~P08.6 전량 첫 실배포. m710q·dolfinid-2 모두 git-free `deploy-{dev,prod}.sh 0.1.56`
  + `seed --mode=replace`(운영 데이터 보존 upsert **실동작**: prod `inserted 1053·updated 797`)·`seed_demo`.
  `/healthz` node_types 17 확인. 호스트 래퍼가 옛 2줄 버전이라 이번 1회 `sync_to_srv.sh` 부트스트랩.
- **0.1.57 — prod 실배포에서 나온 2 갭 수정**([커밋 9f6f620]):
  - ⓐ **smoke SSL false-fail** — prod `.env` `SECURE_SSL_REDIRECT=True` 라 평문 HTTP `/healthz` 가 301 →
    `curl`(-L 없음) 빈 본문 → `status!=ok` 오판. `smoke.sh`·deploy 대기 루프에 `X-Forwarded-Proto: https`
    헤더(settings 의 `SECURE_PROXY_SSL_HEADER`)를 실어 로컬 컨테이너를 직접 검증. 로컬에서 301→빈본문→헤더→200 재현.
  - ⓑ **deploy 에 seed 단계 부재** — 시드 변경/빈 DB 최초 배포 시 재시드 전 smoke 가 실패. `--reseed` 플래그 신설
    (`deploy-{prod,dev}.sh X.Y.Z --reseed` → [5b] migrate 후 smoke 전 `seed --mode=replace`+`seed_demo`).
  - dolfinid-2 `deploy-prod.sh 0.1.57 --reseed` green(스냅샷→스왑→[5b] inserted 1053·updated 797→[6/6] smoke ok/17).
- **0.1.58 — 부트스트랩 self-heal**([커밋 14f1fd8]): `_extract_and_deploy.sh` 가 매 배포마다 부트스트랩 파일도
  이미지에서 갱신(래퍼=exec 후 즉시 덮어쓰기 · 자기 자신=임시파일→원자 rename). **prod·m710q 둘 다 self-heal 활성 확인**.
  이로써 **운영 서버에 repo 영영 불필요**(git-free 부트스트랩 docker cp 절차는 DEPLOY.md 명시).
- **0.1.59 — 전체 플로우 Claude 구동 end-to-end**: m710q 에서 `build.sh 0.1.59 --fast`(버전만) → `deploy-dev.sh`(테스트)
  → **`ssh dolfinid '/srv/cdGTS/deploy-prod.sh 0.1.59'`(prod 원격 배포)** → 공개 healthz 확인까지 한 세션 완주.
  prod 배포를 Claude 가 SSH 로 직접 수행한 첫 사례(사용자 지시). prod 는 self-heal + repo-free 로 무개입.

## 워커 배포 버그 (0.1.60 핫픽스)

`deploy.sh` 재기동이 `docker compose up -d cdgts`(**웹만**)였다. 그래서 prod 스냅샷 경로의 `down`(웹+워커 제거) 뒤
웹만 다시 뜨고 **워커(cdgts-worker, P06.4a 비동기 평가)가 계속 부재**했다(사용자가 예전에 "워커가 개발서버에만"
지적한 것의 근본 원인). dev 경로에서도 워커가 옛 이미지로 잔존.

- 수정: `up -d cdgts` → **`up -d`(전 서비스)**. `rollback.sh`(이미 `up -d cdgts worker`)와도 정합.
- 0.1.60 배포로 prod 에 워커 즉시 기동 + 스냅샷 down/up 경로에서도 유지 검증(cdgts+cdgts-worker 둘 다 0.1.60 Up,
  `run_worker` 폴링). **양 서버 웹+워커 둘 다 0.1.60.** (devlog 미기록 핫픽스였던 것을 이 로그로 포착.)

## 계약·문서 정합

이번 실배포에서 드러난 사실을 cross-project 계약 원본과 프로젝트 문서에 역반영:

- **`../devdocs/wiki/deploy-data-contract.md`** — 5건 정정(인프라표 인증 주석·cdGTS 현황·`up -d` 전 서비스·smoke SSL·
  git-free self-heal) + 파일럿 교훈 반영. (A=사실 정정 · B=파일럿 교훈)
- **`DEPLOY.md`**(릴리스별 델타) — 0.1.57~0.1.60 항목 + 상시 불변식에 워커/`--reseed`/git-free/SSL 추가, [5/5]→[5/6] 정정.
- **`deploy/README.md`** — 구성표(신규 파일 7종)·흐름 절 git-free 재작성·maintenance 상태 정정.
- **`HANDOFF.md`** — 현재 상태 배포/운영 절을 0.1.60·git-free·self-heal·worker·동사/게이트로 갱신.

## 최종 상태

- P08 6개 하위(레인 경계·매니페스트·DEPLOY.md·동사·/healthz·git-free) **전부 실배포 검증 완료**.
- **양 서버 @ 0.1.60**(dolfinid-2 운영 / m710q 테스트), 웹+워커 가동. 공개 `/healthz` = 0.1.60/node_types 17.
- 배포 = 한 줄(`deploy-{prod,dev}.sh X.Y.Z [--reseed]`), git pull/sync 불요, repo 없이 self-heal.
- pytest **178**(seed replace 운영 데이터 생존 + /healthz 회귀 포함).

## 범위 밖 / 후속

- **maintenance 점검 페이지 자동 nginx 토글** — `maintenance.html` 은 배포되지만 앞단 nginx fallback 은 아직 수동(후속).
- P08 이후 로드맵 복귀: **R04 L2**(상수 변경→연대 값 rescale 커널) · **P06.4b**(PyMC joint) · 아크 A(L2/L3).

*근거: [P08](20260713_P08_deploy-data-contract-retrofit.md) · [140](20260713_140_seed-replace-lane-boundary.md)~[143](20260713_143_git-free-deploy.md) · `../devdocs/wiki/deploy-data-contract.md`.*
