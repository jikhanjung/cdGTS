# HANDOFF — Current Work Status

**Last updated**: 2026-07-22. 운영 `cdgts.paleobytes.info`(dolfinid-2) @ **0.1.72** · 테스트 서버 **m710q**(tailscale serve → `127.0.0.1:8011`) @ **0.1.72**. 이미지 `honestjung/cdgts:0.1.35~0.1.72` dockerhub push 완료. 공개 `https://cdgts.paleobytes.info/healthz` = 0.1.72/node_types 16(boundaries 177·prod graphs 8[사용자 fork 1]·test graphs 7). **양 서버 cdgts + cdgts-worker 둘 다 가동, 비-root(prod uid 1001·test uid 1000), DB = `/srv/cdGTS/db/` 서브디렉터리 마운트**.
- **홈 대시보드 신설·배포(0.1.72)**([커밋 3f4f4e5]): 초기 화면이 Editor → **Home 대시보드**로 — 릴리스·오픈 제안·그래프·레퍼런스 카운트 타일(클릭 시 해당 화면), 최근 릴리스 6개(클릭 시 Vault 에서 선택)·최근 제안 6개, 표면별 바로가기 카드, baseline 링크. 좌상단 **cdGTS 워드마크가 버튼**(클릭 시 홈 복귀). 기존 공개 API(`releases`·`proposals`·`graphs`·`references`)만 소비 — **백엔드·시드·마이그레이션 무변경**, `--reseed` 불요. `<title>` "Node Editor" → "Continuously Deployed Geologic Time Scale". 양 서버 배포·smoke green. ⚠️ 0.1.70·0.1.71 은 DEPLOY.md 릴리스 노트 누락 상태(0.1.72 항목만 추가됨 — 71 은 마이그레이션·reseed 릴리스였으므로 소급 기재 후보).
- **R07 감사 quick win·배포(0.1.71)**([R07](devlog/20260720_R07_project-wide-gts2012-review.md)): 프로젝트 전반 as-built 감사(R07)의 구체 코드 결함을 전수 검증 후 선반영. ⓐ **비공개 그래프 평가 API IDOR 수정** — `EvaluateView`·`EvalJobView` 가 `AllowAny`+`Graph.objects` 직접조회라 비공개 sandbox 가 pk 로 새던 것(결과 열람·평가·익명 job 큐잉)을 `visible_graphs()` 경유로 차단(공개/시스템 그래프 익명 평가는 유지 — quickstart 읽기전용 흐름 보존). 회귀 3종 추가. ⓑ **누락 마이그레이션 `graph/0011_alter_nodeinstance_nature`** 생성(`makemigrations --check` 클린). ⓒ **`calibration-constant` seed 설명 정정** — "every dependent age re-computes" → 현재는 공분산 재배선, 값 rescale 은 R04 L2 로드맵(node-manual 재생성). pytest **192→195**. 양 서버 `--reseed` 배포·smoke green(재시드 inserted 1053·updated 794, migrate 0011·write probe 통과). ⚠️ **남은 P0(무결성) 미착수**: `status` read-only · 불변 `GraphRevision` · destructive re-bake 차단 · Release revision/hash 고정 — 스키마 얽힘, 백로그 R07 참조.
- **예제④ base-of-Cambrian δ13C 클러스터 재배치·배포(0.1.70)**([커밋 d7dcc37]): admin fork(`example-icc-partial-fork`)에서 정리한 배치를 시스템 example ④(`example-icc-partial`)에 반영. δ13C 그룹·Cross-section·calibration·Fortune 체인을 Base of Cambrian 근처로 모아 캔버스를 가로지르던 긴 엣지 제거. **노드 6개 좌표만 변경 — 위상·값·경계 연대 전부 불변**(순수 레이아웃). 마이그레이션 없음, `--reseed` 로 배포. 양 서버 0.1.70 배포·smoke green(node_types 16·boundaries 177·graphs 7).
- **반출 위생 — 운영 DB 사본의 세션 토큰 제거(릴리스 없음, 호스트 스크립트)**([devlog 151](devlog/20260715_151_egress-sanitize-session-tokens.md)): 사용자 질문("운영 DB 를 cron 으로 복사해 테스트 DB 로 쓰는데 보안 문제 없어?")에서 출발. 대부분은 🟢(**제3자 PII 0** — auth_user=본인 1개 · 해시 pbkdf2 **100만회** · 테스트서버 **tailnet 전용**(funnel 아님) · DEBUG=False · SECRET_KEY prod≠test)이나 **`django_session` 이 문제**: `session_key` 는 **쿠키에 담기는 값 그 자체(bearer 토큰)** 라, 사본을 읽은 사람이 **운영에** 되제시하면 운영이 자기 SECRET_KEY 로 디코드해 **admin 으로 로그인된다** — **SECRET_KEY 가 달라도 안 막힌다**(키 차이는 "테스트가 해독하는 것"만 막음). 대칭적으로 그 세션은 **테스트선 무용지물**(서명 검증 실패) = **순수 손해**. 노출면 **사본 29벌**(m710q /srv·~/backups 15 + **NAS 0777** 14, 보존 90일), 7/3자 사본에도 유효 세션 실측. → **반출 위생**: `sync-cdgts-db.sh` 가 운영에서 만드는 **임시 스냅샷에만** `secure_delete=ON` + `DELETE FROM django_session` + **`VACUUM`** + `journal_mode=DELETE`(위생 실패 시 `exit 1` 로 반출 중단). **`VACUUM` 이 필수인 이유**([151 §9](devlog/20260715_151_egress-sanitize-session-tokens.md)): `backup()` 이 소스의 **free page 까지 복사**하는데 거긴 *과거에* 지워진 세션의 잔류가 있고 `DELETE` 는 행이 아닌 그것에 **구조적으로 닿지 못한다**(`secure_delete=ON` 이어도 — 실측 200→200→VACUUM 후 0). 즉 노출은 위생 실행 빌드가 아니라 **그 DB 를 평생 건드린 모든 writer** 에 걸린다(실제 writer 는 호스트가 아니라 컨테이너). 초판이 소급 정리에만 VACUUM 을 넣고 상시 경로엔 빠뜨린 걸 사용자 지적으로 발견·수정. ★ **라이브 운영 DB 는 읽기만 — 로그인 세션 무영향**(실측 3→3). 해시는 남김(강하고, 지우면 테스트 로그인 불가 — 세션과 성질이 다름). **소급 정리: 사본 28벌에서 세션 44행 제거(44개 전부 아직 유효했음)** + `VACUUM`(free page 에 토큰 문자열 잔존 방지). cron 은 repo 경로를 직접 실행 → 배포 불요. ⚠️ 남은 것: **NAS 0777**(무엇을 내보내나는 고쳤고 어디 두나는 그대로) · sync 는 배포 경로가 아니라 **smoke 가 못 잡는다**(150 의 센티넬 같은 노출 채널 없음).
- **hourly 보존 12 → 24·배포(0.1.69)**: `RETAIN=12` 면 hourly 창이 하루의 절반만 덮어 **daily 오프사이트(04:00)와의 사이에 granularity 갭**이 생긴다 — 20:00 시점에 hourly 는 08:00 까지만 소급하고 daily 는 04:00 이라 **04:00~08:00 어느 시점으로도 복원 불가**. 규칙은 값이 아니라 **관계**(`RETAIN × 주기 ≥ 오프사이트 간격`). **초안은 "튜닝 값이라 보편성 없다"며 계약 승격을 반려했다가 사용자 지적으로 뒤집었다** — 실측하니 5개 프로젝트 전부 hourly + daily 라 아키텍처가 동일해 **24 는 유도값**이었고, 주기가 같은 건 우연이 아니라 계약이 균질화를 목적으로 하기 때문. 오류의 뿌리는 *"주기가 다를 것"* 이라는 **미확인 전제**. 디스크 13→26MB(무시할 만함), 배포 후 **늘어나기만 함**(무손실). → 계약 §백업 레인에 관계식을 MUST 로 승격. ⚠️ 나머지 4개는 아직 12.
- **매시 백업 무결성 게이트·배포(0.1.68)**([devlog 150](devlog/20260715_150_hourly-integrity-gate.md)): 사용자 질문("prod DB 무결성도 매시 체크할까?")에서 출발했으나 **목적은 탐지가 아니라 로테이션 오염 방지**로 판명 — `backup()` 은 소스 페이지를 **검증 없이** 복사하므로 소스가 깨지면 스냅샷도 깨진 채 채택되고, `RETAIN_COUNT=12`(매시)라 **12시간이면 성한 스냅샷이 0개**가 된다(149 의 테스트 DB 손상이 prod 였다면 정확히 이 경로, 9h 미탐지). → 규칙 두 줄: **①검사 실패 시 채택 안 함 + prune 건너뜀**(아무도 안 봐도 자동으로 성한 백업 보존) **②`db/INTEGRITY_FAIL` 센티넬 → `/healthz` degraded → smoke 실패**. 센티넬이 `db/` 인 이유 = 0.1.64 가 컨테이너 시야에서 `backup/` 을 뺐음(마운트 되돌리지 않음). **`degraded` 는 200**(btree 손상 ≠ 서빙 불능 — 재시작이 못 고치는 조건으로 트래픽에서 빼지 않는다; smoke 는 `status=="ok"` 만 통과시키므로 게이트는 그대로). `MAILTO` 미설정이라 로그 경고는 연극 → 사람이 **이미** 보는 smoke 에 물림. 자동 롤백은 **일부러 안 함**(DB 손상에 롤백은 답이 아닐 수 있음). 증거 사본 `.corrupt` 1개만 보존(디스크 누수·prune glob 회피, 테스트로 고정). **테스트가 오염을 실증**: 실제 sqlite 3번째 페이지를 훼손 → 센티넬이 뜬다 = `backup()` 이 예외 없이 손상을 복사했다. pytest **174→192**. ~~3-repo 정렬 이탈~~ → **fcmanager 0.6.24 · fsis2026 0.5.85 가 같은 날 뒤따라 3/5 적용**(paleonews·naverland 미적용). ⚠️ 남은 구멍: `rollback.sh --db=restore` 는 복원 대상을 검사하지 않음.
- **`order` 노드 + `clamp` 카테고리 제거·배포(0.1.67)**([devlog 149](devlog/20260715_149_order-node-and-clamp-category-removal.md)): devlog 135(clamp 축소)가 "order 제약 = order 엣지"로 결정하고 `graph/models.py` 에 *"replaces the order node"* 라 적어두고도 **정작 order 노드를 안 지운** 잔재 회수 — 0.1.66 노드 매뉴얼이 "미사용 타입 4개"로 표면화(**매뉴얼이 만든 당일 제 목적을 달성**). `order` 가 clamp 카테고리의 마지막 멤버라 **카테고리 자체가 소멸**(마이그레이션 `nodes/0004`, enum choices 만) → 카테고리 = **data·process·reference**. NodeType **17→16**. L1 게이트 3단→2단 폴백(중간 order-노드 단은 인스턴스 0개라 사문 → 판정 무변화). 존치(이름만 같음): `releases.Clamp`(DEMO-ONLY)·`range_clamp` 커널. 순환 breaker 는 `joint-inference` slug 하나뿐임을 확인 — **그래서 미사용이어도 존치**(유일 breaker). pytest **174**(order 테스트 9종 제거). 양 서버 배포·재시드·smoke green(node_types 16).
  - 🐛 **배포 중 발견·수정 — `scripts/sync-cdgts-db.sh` 가 테스트 DB 를 깨뜨리고 있었다**: 웹(`cdgts`)만 stop 하고 **워커(`cdgts-worker`)가 같은 WAL DB 를 연 채로** 메인 파일을 `cp` 로 덮고 `-wal`/`-shm` 을 지워 btree 손상(`graph_nodeinstance`). 오늘 2회 발생(04:00 cron · 복구용 수동 sync — **복구 도구가 재손상 원인**). **0.1.60(devlog 144) `up -d cdgts`→`up -d` 수정의 놓친 형제**. → `stop`/`up -d` 를 서비스명 없이. 전수 점검 결과 `deploy.sh`·`rollback.sh` 는 처음부터 옳았음(`down` 전 서비스 + `-wal`/`-shm` 동반). **prod 무사**(sync 의 소스이지 대상 아님, `integrity_check` = ok 전 구간 확인).
- **노드 매뉴얼 자동 생성·배포(0.1.66)**: `manage.py node_manual` → **[docs/node-manual.md](docs/node-manual.md)** — 시드(NodeType.description·`params_schema.help`·Port) × 커널(`engine.kernels.kernel_for`) × **실제 사용처**(NodeInstance) 를 조립. 손으로 쓴 매뉴얼은 낡으므로 단일 진리원에서 생성. `kernel_for` 가 `compute()` 분기 우선순위를 노출(정합성 테스트로 고정 — 어긋나면 매뉴얼이 틀린 커널을 보고). 시드 빈 `help` 10개 채움(→ `--reseed` 배포, 프론트 인스펙터 반영 확인). **바로 드러난 것: NodeType 17개 중 4개가 어떤 그래프에서도 미사용** — `order`(clamp 축소 잔재?)·`astronomical`·`magnetostratigraphic`·`joint-inference`. ⚠️ R05 는 "`joint-inference` 는 살고 `cross-section-correlation` 은 소멸"이라 했으나 **정작 미사용인 쪽이 `joint-inference`** 이고 둘은 같은 커널 — 정리 여부 미결. ⚠️ 생성기는 **갓 시드한 DB** 에 돌릴 것(운영 DB 면 사용자 fork 가 섞여 DB 마다 문서가 달라짐). pytest **183**. 양 서버 배포·재시드·smoke green.
- **R05 검토 + spline 공유성분 수정·배포(0.1.65)**([R05](devlog/20260715_R05_correlation-provenance-depth.md)): GTS2012 Ch.14(Agterberg 등, *Statistical Procedures*) 요약을 참고자료로 들이고([docs](docs/statistical_procedures_summary.md)) "여러 섹션 연대를 어떻게 합칠까"를 검토 — **결론: Ch.14 는 그 문제를 풀지 않고 전제한다**(composite x축은 Ch.3 소관). cdGTS 는 *답*을 합치고(역분산 평균) Ch.14 는 *증거*를 합친다(단일 spline). R04 자매편으로 **1급 프리미티브는 `tie-point` 하나**, 킬러 유스케이스는 **상관 가설 엣지 토글 → 원클릭 diff**(topology-diff·competing-models·P05 재사용). 아크는 **미착수**. 부수 버그만 선상환: **spline 경로 `shared_components` 유실**(`method="spline"` 이면 공분산 백본이 조용히 끊김) — 스플라인 평가가 연대에 선형임을 이용해 카디널 가중치로 해석적 전파(Cov 0→0.16, duration σ 0.58→0.13), `_blend_components` n-ary 일반화(죽은 파라미터 제거). **경계 연대 불변** — 시드·운영 DB 의 age-depth-model 12개가 전부 `method="linear"` 라 이 경로는 미실행(잠복 버그였음). pytest **182**. 양 서버 배포·smoke green(행 수 0.1.64 와 동일), 재시드·마이그레이션 없음.
- **DB 마운트 db/ 서브디렉터리 컷오버·배포(0.1.64)**([devlog 148](devlog/20260714_148_db-mount-subdir-cutover.md)): whole-/srv 마운트 → `/srv/cdGTS/db` 만 마운트로 **blast radius 축소**(컨테이너가 `.env`·`backup/`·배포 스크립트 못 봄; 양 서버 실증: `docker exec cdgts ls /app/hostdb` = db 파일만). fsis/fcmanager 동형 — cdGTS 유일 예외 해소. `deploy.sh [3/6]` 이 옛 루트 DB 를 db/ 로 **1회 자동 mv 컷오버**(멱등, 정지 후) + `/srv/cdGTS/db.sqlite3 → db/db.sqlite3` **안전망 symlink**. `.env DATABASE_PATH`·DB 게이트 prefix 무변경. one-way(rollback --db=keep 안전·이전 이미지 재배포는 symlink/smoke 방어). entrypoint gosu 드롭 시 `HOME=/tmp` 명시(fsis 동형) 동봉. 양 서버 배포·검증(PID1 uid 1001/1000·backup_db.py 새 경로 fallback·smoke green).
- **3-repo 배포 일관성 정렬 + hourly DB 백업·배포(0.1.63)**([devlog 147](devlog/20260714_147_three-repo-consistency-align.md)): 계약 정렬 3개 프로젝트(cdGTS·fcmanager·fsis) 배포 스크립트 동형화. `scripts/backup_db.py` 신설(sqlite online backup·12개 유지 — **0.1.69 에서 24 로**) → 종전 pre_deploy 스냅샷+daily pull 에 **hourly 트랙 추가**(prod cron 등록 완료). `deploy.sh` DEPLOY_SNAPSHOT 기본 1·기동 대기 `/healthz`·DB 게이트 `manage.py shell -c`. `smoke.sh` python3 JSON+버전 필수. 양 서버 배포·검증. ⚠️ backup_db.py 는 self-heal 지연으로 이번 1회 수동 부트스트랩(다음 배포부터 자동).
- **컨테이너 비-root 실행 전환·배포(0.1.62)**([devlog 146](devlog/20260714_146_nonroot-container.md)): 계약의 "디렉터리 마운트 소유권 함정"(fcmanager 0.6.16~17) 점검 계기. cdGTS 는 컨테이너가 root 라 함정을 안 걸렸으나(그래서 "안전 이유가 root"인 게 문제) 비-root 하드닝 시 prod 에서 함정에 빠질 소지 → 지금 전환. **entrypoint 가 root 로 시작 → 마운트(`/app/hostdb`) 소유 uid 감지 → `gosu` 로 드롭**(호스트 무관: prod 1001·test 1000, chown 불요). Dockerfile `gosu` 설치. `deploy.sh [5/6]` 에 **쓰기 프로브**(앱 uid CREATE/DROP) 추가 — 읽기 게이트가 못 잡는 소유권 오배치를 배포 직후 FATAL. 웹·워커 둘 다 PID1 uid=1001/1000 실검증, 쓰기 프로브·smoke green. 전제: 호스트별 `/srv/cdGTS`·`db.sqlite3*` 동일 비-root uid 소유(현재 충족).
- **배포·데이터 계약 외부 검토분 적용·배포(0.1.61)**([devlog 145](devlog/20260713_145_deploy-contract-external-review.md)): 계약(`../devdocs/wiki/deploy-data-contract.md`)에 외부 검토로 추가됐으나 cdGTS 코드엔 미반영이던 항목 4종. ⓐ **롤백 코드/DB 분리** `rollback.sh --db=keep(기본, 이미지만·운영 데이터 보존)|restore(정지 후 스냅샷 복원)` + **keep 가드**(직전 배포 migration 시 차단, 스냅샷 `.mig` 사이드카 vs 현재 비교). ⓑ 매니페스트 `contract_version=1`·`rollback_db="keep"`. ⓒ **self-heal 추출 안전망**(`_extract_and_deploy.sh` 교체 전 `bash -n` + `.previous` 보존). ⓓ `deploy.sh` 스냅샷이 `.mig` 사이드카 기록. **양 서버 실배포·검증**(prod 스냅샷 `.mig` = pre-migration 50 기록 확인, 새 rollback.sh·self-heal 추출기 landed, smoke green). 마이그레이션 없음.
- **워커 배포 버그 수정(0.1.60)**([커밋]): `deploy.sh` 재기동이 `docker compose up -d cdgts`(웹만)라, prod 스냅샷 경로의 `down`(웹+워커 제거) 뒤 **워커(cdgts-worker, P06.4a 비동기 평가)가 계속 부재**했음(사용자가 예전에 "워커가 개발서버에만" 지적). `up -d`(전 서비스)로 수정 → rollback.sh 와 정합. prod 에 워커 즉시 기동 + 0.1.60 배포로 스냅샷 down/up 경로에서도 워커 유지 검증(cdgts+cdgts-worker 둘 다 0.1.60 Up, run_worker 폴링). dev 경로의 "워커 옛 이미지 잔존"도 함께 해소.
- **전체 릴리스 플로우 Claude 구동 검증(0.1.59)**: m710q 에서 `build.sh 0.1.59 --fast`(버전만) → `deploy-dev.sh 0.1.59`(테스트) → **`ssh dolfinid '/srv/cdGTS/deploy-prod.sh 0.1.59'`(prod 원격 배포)** → 공개 healthz 확인까지 한 세션에서 완주. prod 는 self-heal + repo-free 로 무개입. (prod 배포를 Claude 가 SSH 로 직접 수행한 첫 사례 — 사용자 지시.)
- **0.1.58 부트스트랩 self-heal — prod repo-free 확립**([커밋 14f1fd8]): `_extract_and_deploy.sh` 가 매 배포마다 부트스트랩 파일도 이미지에서 갱신(래퍼=exec 후 즉시 덮어쓰기 · 자기 자신=임시파일→원자 rename, 다음 배포부터). **prod·m710q 둘 다 self-heal 활성 확인**(`deploy-{prod,dev}.sh 0.1.58` 로그에 `self-heal *` 3줄). git-free 부트스트랩(repo 없이 `docker create`+`docker cp /app/deploy/host/{_extract_and_deploy,deploy-prod,deploy-dev}.sh`) 절차 DEPLOY.md 명시. **이제 prod 에 repo 불필요 — `~/projects/cdGTS` 삭제 가능.** 앞으로 릴리스 = (빌드호스트)`build.sh X.Y.Z` → (prod SSH)`deploy-prod.sh X.Y.Z [--reseed]`. SSH 별칭 `dolfinid`(키 인증, m710q→prod 붙음).
- **0.1.56 운영·테스트 배포 완료** — P08.1~P08.6(배포·데이터 계약 retrofit) 전량. m710q·dolfinid-2 모두 git-free `deploy-{dev,prod}.sh 0.1.56` + `seed --mode=replace`(운영 데이터 보존 upsert 실동작: prod `inserted 1053·updated 797`)·`seed_demo` 재시드. `/healthz` node_types 17 확인.
- **0.1.57 운영 배포 완료 — prod 실배포에서 나온 2 갭 수정**([커밋 9f6f620]): ⓐ **smoke SSL false-fail** — prod `SECURE_SSL_REDIRECT=True` 라 평문 HTTP `/healthz` 가 301 → curl(-L 없음) 빈 본문 → status!=ok 오판. `smoke.sh`·deploy 대기 루프에 `X-Forwarded-Proto: https`(SECURE_PROXY_SSL_HEADER) 헤더. ⓑ **deploy 에 seed 단계 부재** — 시드 변경/빈 DB 최초 배포 시 smoke 가 재시드 전 실패. `deploy-{prod,dev}.sh X.Y.Z --reseed` → migrate 후 smoke 전 `seed --mode=replace`+`seed_demo`. **dolfinid-2 @ 0.1.57 배포·재시드·smoke green 검증 완료**(`deploy-prod.sh 0.1.57 --reseed`: 스냅샷→스왑→[5b] reseed inserted 1053·updated 797→[6/6] smoke ok/17). P08 배포 파이프라인 전 구간 실증. **m710q 도 `deploy-dev.sh 0.1.57` 로 맞춤(smoke green)** — prod·test 0.1.57 일치.
- **P08.1 (배포·데이터 계약 retrofit — seed 레인 경계)**([계획 P08](devlog/20260713_P08_deploy-data-contract-retrofit.md) · [devlog 140](devlog/20260713_140_seed-replace-lane-boundary.md)): cross-project 배포·데이터 계약(`../devdocs/wiki/deploy-data-contract.md`)의 핵심 불변식 — *"`seed --mode=replace` 는 시스템 정의 데이터만 건드린다"* — 을 seed 명령에 세움. 기존 `_delete_all()` 이 owner 무시하고 `graph.Graph`·`releases.Release` 를 `all().delete()` → P05 운영 데이터(학자 fork·bake·Proposal) silent 삭제 또는 PROTECT 실패였던 **잠복 footgun** 해소. 전략: **레지스트리 자연키 upsert(pk 보존 → 운영 PROTECT/CASCADE 참조 안전) + 시스템 그래프(owner NULL)만 삭제·재생성 + 파생물 시스템 스코프 재-bake + 스코프 prune**. `references.Reference` 누락(재replace 중복 INSERT) 잠복 버그 동봉 수정. pytest **175**(운영 데이터 생존 회귀 신규) · 운영 미러 dry-run(inserted 1056·updated 794·removed 1893, 무예외). 마이그레이션 없음(관리 명령만). **미배포**(코드 변경, 다음 릴리스에 포함).
- **P08.2·P08.3 (매니페스트 + 운영 델타 노트)**([devlog 141](devlog/20260713_141_deploy-manifest-and-notes.md)): `deploy/deploy.toml`(선언층 — image·db_path·has_seed·services·[verbs]·[targets.prod=dolfinid-2/test=m710q]) + 루트 `DEPLOY.md`(릴리스별 append-only 운영 델타 노트 — 상시 불변식[재시드·DATABASE_PATH 바인딩·migrate·Crossref] + 0.1.3~P08.1 소급, 🔴/🟡/🟢). 문서·설정만(코드 무관).
- **P08.4·P08.5 (동사 + /healthz)**([devlog 142](devlog/20260713_142_deploy-verbs-and-healthz.md)): `config/health.py` **`/healthz`**(버전+DB+핵심 행 수 → 200/503; 시스템 시드 부재=503; 무인증) + 동사 스크립트 `deploy/preflight.sh`(위험 표면 diff + seed 냄새 lint + DEPLOY.md)·`deploy/host/smoke.sh`(healthz 200+버전 일치+행 수)·`deploy/host/rollback.sh`(이전 이미지+pre_deploy 스냅샷). `deploy.sh` [6/6] smoke 자동, `deploy.toml health_probe`→/healthz. pytest +3(healthz).
- **P08.6 (git-free 배포)**([devlog 143](devlog/20260713_143_git-free-deploy.md)): 운영 서버 git pull 의존 제거. host 운영 파일이 이미 `COPY . .` 로 이미지 `/app/deploy/host/*` 에 실려 있음 → `deploy-{prod,dev}.sh` 를 git-free 부트스트랩으로 재작성(공유 `_extract_and_deploy.sh` 가 `docker cp` 로 이미지에서 compose·deploy.sh·smoke·rollback·maintenance 추출 → deploy.sh 위임). 호스트 상시 파일=`.env`+래퍼2+`_extract_and_deploy.sh`. `sync_to_srv.sh`=부트스트랩 전용. **P08 전체 완료**(레인 경계·매니페스트·동사·헬스·git-free). ⚠️ **0.1.56 1회 부트스트랩**: 호스트 래퍼가 옛 2줄 버전이라 이번만 `sync_to_srv.sh` 1회 필요(DEPLOY.md 명시). **다음: 0.1.56 빌드·실배포 검증**(seed replace 운영 데이터 보존·[6/6] smoke·git-free 추출 최종 확인).
- **0.1.54~0.1.55** 공유 보정 노드 + 공분산 배선 L1 vertical slice([devlog 139](devlog/20260712_139_calibration-constant-covariance-slice.md) · 근거 [R04](devlog/20260711_R04_radiometric-provenance-depth.md)): R04("방사연대 provenance 를 어느 깊이까지"—결론 = 공유 보정 파라미터 한 프리미티브만 1급으로)를 노드·커널·데모로 착지. **`calibration-constant` NodeType**(data leaf; params distribution·kind·symbol; out `value`; 커널이 불확실성 전액을 자기 자신 ref=symbol 의 `shared_component` 로 자동 태깅=L4 joint 승격) + **소비자 배선**: `radiometric-uPb` 에 `calibration` 입력 포트, 커널이 보정 σ 를 (a) 자기 marginal budget 에 제곱합 + (b) shared_component 로 태깅. **값 불변 = 재계산 아닌 공분산 배선(L1)**. 캡스톤 데모(`seed_demo` demo-cov)를 매직 스트링 → **진짜 공유 노드**로 재구성: ²³⁸U 붕괴상수는 물리적으로 하나 → `decay-238U` **딱 한 노드**가 두 연대에 갈라짐(shared→Cov 1.96→L1b **pass**) vs 공유 의존을 모델에 기록 안 함(independent=노드 없음, 순진 독립→Cov 0→L1b **warn**). marginal 값·± 는 양쪽 동일, 차이는 provenance(노드+엣지)뿐. **pytest 174**(커널 단위 5케이스 신규). 프런트 변경·마이그레이션 없음(팔레트·포트·인스펙터 동적). **남은 것(L2)**: 상수 값 변경이 연대 **값**을 재계산하는 rescale(raw invariant/민감도 노드) — 유스케이스 대기.
- **0.1.48~0.1.53**(devlog 132~138) — readonly 그룹 드릴인 · 레퍼런스 후속(Crossref 자동 메타데이터) · Tier-1 CI 플로우 시나리오 테스트 + **gateway-wipe 버그 수정** · **clamp 축소**(`pin`/`range`/`freeze-version` NodeType 제거, GSSA=`published-age` leaf, `releases.Clamp` DEMO-ONLY) · Editor.jsx 분해 1·2차(1252→966줄). 전부 운영 반영·재시드 완료. 0.1.52 에서 compose 볼륨을 디렉터리 바인드로 바꾸며 `deploy.sh` DB 바인딩 게이트 추가.
- **P07 — Base of Cambrian realistic model**([devlog 131](devlog/20260710_131_p07-base-cambrian-realistic-model.md)): provenance vertical slice 를 실제 추론 구조로 — `section`/`horizon`/`reference` 노드, 3 dated 섹션(Oman·Namibia·Siberia)의 U-Pb ash bed 가 δ13C BACE horizon bracket → age-depth interpolate → cross-section-correlation → T. pedum FAD `calibration-transfer` → base of Cambrian 538.82 Ma. example③ 23노드·example④ 279노드. 운영 반영 완료.

**배경(0.1.35~0.1.46)**: **레퍼런스 노드 + bake→bibliography**(devlog 127·128) 위에 P07 을 쌓음. 이전 P04(불변 Bake·Vault) · P05(멀티유저 CI) · P06(Science Engine: 공분산 백본·정합성 게이트 L1/L2·clamp reconcile) · P06.4a(비동기 워커) 는 그대로. **다음: R04 L2(상수 변경→연대 값 rescale 커널) · P06.4b(PyMC joint) · 아크 A(L2/L3).** (P07 운영 반영·devlog·clamp 통합→축소·Editor 분해 1·2차·Tier1/2 테스트·R04 L1 공분산 배선은 완료.)

> 과거 작업 내역은 `devlog/` 에 모두 기록됨. 본 문서는 **현재 상태 + 다음 작업**만 유지.
> 개념 지도 `docs/concept-map.md` · 앱 설계 `docs/app-architecture.md` · 개발 계획 `devlog/*_P01_*` · backlog `TODOs.md`.

## 현재 상태

- **성격**: 브레인스토밍 저장소 → **실행 가능한 코드베이스 + 실배포**(개념 코퍼스는 `docs/` 에 그대로 유지).
- **스택**: Django **5.2.12**, DB **SQLite**(공간 기능 착수 시 PostGIS), **DRF 3.17.1**, 프론트 **React 18 +
  @xyflow/react 12 + Vite**(`frontend/`, dev 는 `/api` 프록시). venv `/home/jikhanjung/venv/cdGTS`.
- **앱 7개** (의존: chrono ◁ nodes ◁ graph ◁ engine ◁ releases · accounts · references):
  - `chrono` — 정본 registry(Unit 이중명명·Boundary·Lineage·Authority·Ratification·Locality).
    ICS chart.ttl 기반, **Subperiod(아계) rank 포함**(Carboniferous Mississippian/Pennsylvanian).
  - `nodes` — 타입 시스템(NodeType + Port) + `Distribution` 값객체(충실도 L0–L5). `published-age`(공표값 leaf) ·
    **`calibration-constant`**(공유 보정 파라미터 leaf: 붕괴상수·monitor·tracer; 커널이 σ 를 shared_component 로 자동 태깅 → 공분산 백본) 포함.
  - `graph` — DAG(Graph·NodeInstance·Edge·NodeGroup·Gateway) + DAG 불변식 + DRF React Flow 왕복.
    **경계·구간 이중성 모델**(`NodeInstance.nature`=generic|boundary · `NodeGroup.kind`=container|unit·`unit`·
    `lower`/`upper` 경계 노드 FK · `Edge.kind`=data|order). **노드그룹 = 컨테이너+접기+드릴인, N단 중첩**(parent
    self-FK, 엔진은 평탄). **order 제약 = order edge**(younger→older 세로 포트, 두 경계 선후 검사).
  - `engine` — 평가(EvalRun·NodeResult 콘텐츠해시 증분·CoherenceCertificate) + 계산 커널(numpy/scipy,
    age-depth 선형보간+spline MC). **정합성 게이트: L1 = authored order edge 체인(sparse) · L2 = 게이트웨이가
    덮는 전 유닛 duration>0 자동검사**(영-길이 유닛 검출, rank 별 타일링). **merge 노드 = geometry/composition
    타일링**(구간 조립: age→period→era→chart).
  - `releases` — ModelCandidate·Release·BoundaryRecord·Clamp + bake/diff API.
    **공표 ICC 릴리스 `ICS-2024/12`**(Epoch/Age 까지 값 정식화) + `GET /api/releases/{id}/icc-chart/`.
    **narrate**: `BoundaryRecord.narrative` 를 구조화 필드에서 결정적 템플릿 렌더(LLM 창작 없음).
    **P04/P05**: `Release.kind`(published/bake/transient)·`owner`·`source_graph`(불변 Bake 아티팩트) ·
    `snapshot_graph` · **`Proposal`**(propose/ratify/reject = CI) · `verify_graph`/`publish_graph`.
  - `accounts` — **`Membership`**(User↔Authority·role) + 개인 fork Authority 시그널 + 세션 인증
    `/api/auth/{whoami,login,logout}` + 중앙 **`can_ratify`**(P05.1·.4).
  - `references` — **`Reference`**(DOI 레지스트리: slug·doi·title·authors·year·kind, `link`). 그래프의
    `reference` NodeType 이 `cite` 엣지(비-데이터)로 데이터/모델 노드를 인용 → provenance 가 그래프 1급 시민.
    `GET /api/graphs/{id}/references/`(bibliography+citations = bake→참고문헌 seam). (devlog 127)
- **프론트 — 노드 에디터(`Editor.jsx`)**: 팔레트/캔버스/인스펙터. 주요 UX:
  - 헤더에 **버전 배지**(`v0.1.x`), **auto-evaluate**(로드/저장 시 자동) + **saved/unsaved 표시**(● Unsaved / ✓ Saved).
  - **boundary 노드**: 컴팩트(반높이 ◈), 입력 age(또는 공표값)를 노드 얼굴·인스펙터에 표시, Phanerozoic 경계는
    "Base of <Period>" 명명. 팔레트 boundary/published-age 드롭 시 `nature=boundary` 기본.
  - **선택 UX**: 모든 노드/그룹/합성(gio·bound) 노드에 **선택 테두리 링**, **Shift+클릭 추가 선택**,
    좌-드래그 러버밴드 + **가장자리 auto-pan**, 다중선택 시 **전체 바운딩 사각형 숨김**(개별 링만), 선택 노드
    위 우클릭도 그룹 생성 메뉴. 파생 노드 참조 안정화로 박스 밖 강제선택 버그 해소.
  - **인스펙터**: 데스크톱에서 **접기 토글**(Properties ◂/▸ · 패널 ✕), **노드 선택 시 자동 표시**.
  - **컨텍스트 메뉴**: 노드/엣지 **삭제**, 그룹 생성·병합·해제, parent 로 돌아가기. **엣지 선택·삭제**(order edge 포함).
  - **order edge**: younger→older 연결로 생성(점선 보라), 그룹 접힘 시 order 포트 항상 노출(삭제해도 재연결 가능).
  - **그룹/합성 노드 고정 폭**(collapsed group 200px · Group I/O 200px, 긴 라벨 ellipsis).
- **프론트 — Vault 허브 + Proposals**(P04·P05; nav = Editor·**Vault**·**Proposals** + LoginBar): ICC 테이블·**차트**·서술·
  릴리스 Diff 를 **Vault**(Release 선택 → 표현 토글)로 통합. **Proposals** = CI 리뷰(제안 목록 + verify diff + ratify/reject).
  - **ICC 차트**: Eon~Age **5 컬럼 중첩**(**Subperiod 는 Epoch 컬럼에 병합** — Carboniferous 전용 컬럼 제거),
    경계 불확실성 ± 밴드·툴팁. **스케일 3종**: Log(최근 확대) · Linear(비례) · **Table(equal Age — 시간척도 무시,
    leaf 셀 균등 높이의 표 형식)**. **줌(viewBox scale) + 팬**(Ctrl/⌘+휠 커서 기준), 줌에 따라 라벨 폰트 조정
    (얇은 밴드도 확대 시 표시). **merge 노드 geometry 뷰**: 특정 column merge 의 부분 차트 조회.
  - **Science CI 버튼**: 그래프 편집 → 재bake → 공표 baseline 과 원클릭 diff(이동 경계·배선 변화 요약).
  - **모바일 대응**: 반응형 드로어 + 터치 팬 + 탭-투-추가/롱프레스 메뉴.
- **예제 그래프**: 3종 파이프라인(permian-triassic 3·cambrian-base 5·gssa-precambrian 1) + **`example-icc-partial`
  (예제④)** — 전 ICC 재구성: **261 노드 · 493 엣지(order 233) · 노드그룹 14**. period=노드그룹(span)·내부 age
  order edge 체인, merge 노드로 age→period→era→chart 조립.
- **배포/운영** (배포·데이터 계약 P08 — [DEPLOY.md](DEPLOY.md)·[deploy/README.md](deploy/README.md)·[deploy/deploy.toml](deploy/deploy.toml)):
  - Docker 이미지 `honestjung/cdgts`, `deploy/build.sh <ver>` 로 pytest→bump→build→push. 버전 `config/version.py`.
  - **운영서버** `cdgts.paleobytes.info`(GCP dolfinid-2) @ **0.1.71**(nginx + certbot). 테스트 `127.0.0.1:8011`(m710q) @ **0.1.71**.
    **양 서버 cdgts(웹) + cdgts-worker(비동기 평가) 둘 다 가동**. 테스트 DB(prod 미러)에 P05 검증용 계정: `admin`(staff·ICS chair)·`demo`(비-staff·ICS chair·개인 fork).
  - **컨테이너 비-root 실행(0.1.62~)**: entrypoint 가 root 로 시작 → 마운트(`/app/hostdb`) 소유 uid 감지 → `gosu` 로 드롭
    (prod uid 1001 · test uid 1000, chown 불요, `HOME=/tmp` 명시). 전제 = 호스트별 `/srv/cdGTS`·DB 파일이 동일 비-root uid 소유.
  - **DB 마운트(0.1.64~)**: `/srv/cdGTS` 전체가 아니라 **`/srv/cdGTS/db` 서브디렉터리만** 마운트(컨테이너가 `.env`·`backup/`·배포
    스크립트를 못 봄). `deploy.sh [3/6]` 이 옛 루트 DB 를 `db/` 로 1회 자동 mv 컷오버(멱등) + `db.sqlite3 → db/db.sqlite3` 안전망 symlink.
  - **git-free + self-heal 배포(0.1.58~)**: 운영 서버에 repo 불필요. 모든 host 파일이 이미지 `/app/deploy/host/*`(`COPY . .`)에
    실려, 진입점 `deploy-{prod,dev}.sh X.Y.Z [--reseed]` 가 `_extract_and_deploy.sh` 로 이미지에서 추출 + 부트스트랩 파일까지
    자기 치유. **배포 = 한 줄**(git pull/sync 불요). prod=스냅샷(pre_deploy) 후 스왑, dev=스냅샷 없이(DB=운영 복사본).
    `deploy.sh` 재기동은 `docker compose up -d`(웹+워커 전 서비스). m710q→prod SSH 별칭 `dolfinid`(키 인증)로 원격 배포 가능.
  - **동사·게이트**: `/healthz`(버전+DB+핵심 행 수 → 200/503) · `smoke.sh`(배포 후 healthz+버전+행 수, prod SSL `X-Forwarded-Proto`
    대응) · `rollback.sh` **코드/DB 분리**(`--db=keep` 기본 = 이미지만 되돌리고 운영 데이터 보존, 직전 배포에 migration 이 있으면
    `.mig` 사이드카 비교로 차단 / `--db=restore` = 정지 후 스냅샷 복원) · DB 바인딩 게이트([5/6], 이미지 내부 빈 DB 폴백 차단)
    + **쓰기 프로브**(앱 uid 로 CREATE/DROP — 소유권 오배치를 배포 직후 FATAL) · `preflight.sh`(위험 표면 diff).
  - **백업**: 원자적 스냅샷(WAL torn-copy 방지) + NAS 오프사이트 + 04:00 daily cron · 배포 시 pre_deploy 스냅샷 ·
    **hourly 트랙**(`scripts/backup_db.py`, sqlite online backup·**24개 유지**, prod cron 등록 완료) — 24 는 튜닝이 아니라 **유도값**: `RETAIN_COUNT × 주기 ≥ 오프사이트 간격`(hourly + daily 04:00 pull → 24). 12 였을 땐 hourly 창이 하루의 절반만 덮어 **두 트랙 사이에 granularity 갭**이 있었다(0.1.69).
  - **무결성 게이트(0.1.68~)**: hourly 스냅샷마다 `PRAGMA integrity_check` → 실패 시 **채택 안 함 + prune 중단**
    (`backup()` 은 소스 페이지를 검증 없이 복사 → 손상 시 12h 내 성한 스냅샷이 전부 prune 되는 **로테이션 오염** 차단).
    + `db/INTEGRITY_FAIL` 센티넬 → `/healthz` **degraded**(stat 1회, 200 — btree 손상 ≠ 서빙 불능) → **smoke 실패**.
    ⚠️ smoke 가 degraded 로 실패 = **배포 문제 아님, 반사적 롤백 금지**([devlog 150](devlog/20260715_150_hourly-integrity-gate.md)).
  - ⚠️ **시드/레이아웃 변경 릴리스는 재시드 필요** — 0.1.57~ 는 **`--reseed` 플래그**로 자동(migrate 후 smoke 전 `seed --mode=replace`
    + `seed_demo`). replace 는 P08.1 이후 **운영 데이터(owner-set) 보존 upsert**(자연키 멱등). add 는 그래프 원자 skip → 변경 반영 안 됨.
- **초기 데이터(seed)**: 통합 `seed/`(manifest `2026.07.0`, 자연키) — `01_chrono`~`04_releases` + **`05_icc_release`**.
  `manage.py seed --mode=replace|add`. 순환 자연키 FK(그룹↔노드)는 forward-ref 2패스로 로드. `FIXTURE_DIRS=seed/`.
- **테스트**: 백엔드 `pytest` **195 passed**(L2 게이트·seed 회귀 + P04/P05 소유·CI·가시성 + **평가/잡 API 비공개 그래프 404 회귀**(R07 §1.2) + calibration 커널 공분산 상속/비상속 + seed replace 운영 데이터 생존 + /healthz(센티넬 degraded 포함) + `scripts/test_backup_db.py` 무결성 게이트). 테스트 fixture 는 seed 파일 loaddata.
- **문서 코퍼스**: `docs/` 14주제 × 한/영 + README + app-architecture + naming(태그라인·표기 규칙) +
  evaluation-order(의존 vs 연대순, order=사후 검사) + boundary-span-duality. 진입점 `docs/concept-map.md`.
  **clamp 축소([cycles §12](docs/cycles.md#12-재검토-노트-2026-07--clamp는-별도-개념으로-필요한가))를 문서 전반에 정합화** —
  concept-map(수렴점 #2·미션)·tier-category-model·app-architecture·tutorial-science-engine·boundary-gateway-schema
  + 개념 문서 5종(idea·distribution·topology-diff·coherence-gate·evaluation-order)에 반영. GSSA=authored `published-age` leaf ·
  clamp 카테고리=`order`만 · `releases.Clamp`=DEMO-ONLY 로 일관(한/영 동기화, 앵커 검증).
- **원격**: `git@github.com:jikhanjung/cdGTS.git`, main 직접 커밋·push.

## 개념/구현 진척 한 줄 정리

> **개념 → 스키마 v0 → 앱 설계 → Phase 0~6 → 계산 커널 → 배포 인프라 → ICC 전 계층 재구성(경계·구간 이중성) →
> 공표 릴리스 대비 Science CI 검증** 완주. 미션 "사람이 authored 노드(값=leaf·선후=order), 기계가 전파·정합·diff" 가 실배포 환경에서
> **authored order(L1) + 자동 duration(L2) + 원클릭 공표 diff** 로 돎.

## 진행 중 (WIP)

- **인터페이스(Group I/O) 노드 위치 영속** — 현재 드릴인별 프론트 세션 메모리(리로드/저장 시 초기화).
  영속 필요 시 NodeGroup 에 io 좌표 필드 추가(후속).

### 완료된 큰 아크 (배포됨)

- **[P04](devlog/20260707_P04_editor-bake-vault-restructure.md)** — Editor→Bake→**Vault** 재구성(불변 Release 아티팩트·Bake 액션·Chart/Table/Narrative/Diff 허브). devlog 102~104.
- **[P05](devlog/20260707_P05_arc-c-multiuser-ci-platform.md)** — 아크 C 멀티유저 CI: 세션 인증·Graph/Release 소유·가시성·fork·propose/review/ratify·샌드박스 오버라이드. devlog 106~110. 흐름 = 로그인→fork→편집→(bake→Vault)/propose→review→ratify · sandbox→override.
- **P06** — Science Engine(공분산 백본·정합성 게이트 L1/L2·clamp reconcile) · P06.4a 비동기 워커.
- **[P08](devlog/20260713_P08_deploy-data-contract-retrofit.md)** — 배포·데이터 계약(seed 레인 경계·매니페스트·/healthz·git-free·self-heal). devlog 140~144.

### 후속 (열린 항목, 우선순위 대략순)

- [ ] **R07 — 프로젝트 전반 as-built 감사(코드 무결성·보안·거버넌스)**([R07](devlog/20260720_R07_project-wide-gts2012-review.md), R06 을 코드 축까지 확장). 구체 코드 결함을 전수 검증 — 대부분 CONFIRMED. **✅ quick win 배포됨(0.1.71)**: ⓐ 비공개 그래프가 평가 API 로 새던 IDOR(`EvaluateView`·`EvalJobView` AllowAny+직접조회) → `visible_graphs()` 경유로 수정+회귀 3종 · ⓑ 누락 마이그레이션 `graph/0011` 생성(`makemigrations --check` 클린) · ⓒ `calibration-constant` seed 설명 "every dependent age re-computes" 정정(현재 공분산 재배선, 값 rescale=R04 L2)→node-manual 재생성. pytest 192→195. **⬜ 남은 P0(무결성 — 미착수, 신뢰 경계)**: `status` 가 API 쓰기 가능 → **read-only** + proposed/ratified 그래프 직접 편집 차단 · Proposal 이 live graph 참조 → **불변 `GraphRevision`(canonical JSON+content hash)** 도입, ratify 는 검토 당시 revision 을 bake · `bake_release` destructive re-bake 차단 · Release 가 mutable `source_graph` FK → revision/hash 고정(★ 이번 세션 소개문 교정 §2와 동일 근거). **⬜ P1(계산 무결성)**: **wiring-aware content hash**(현재 `content_hash`=type+params+sorted(input) 만 → source 노드·포트·edge kind 부재로 재배선 시 stale 캐시) · `params_schema`·Distribution·포트 datatype/multiplicity **서버 검증**(현재 UI 검증만). **⬜ P3**: `.github/workflows` CI 부재(`makemigrations --check` 게이트화)·frontend lint/test 부재·concept-map clamp 카테고리 잔재.
- [ ] **R06 — GTS2012 코퍼스(32장) vs 구현 대조 리뷰**([R06](devlog/20260720_R06_gts2012-corpus-vs-implementation.md)) — 32장 전장을 as-built(v0.1.70)와 대조. **COVERED**: 아키텍처·철학(Ch1·2)·PTB Meishan·Cambrian base·**공분산 오차모델(Ch6·14, GTS2012 독립오차 MC 보다 원리적으로 우수)**·retype/거버넌스(Ch16~18·30·32). **핵심 격차 4종**: ⓐ Ch14 **전역 joint 스무딩 스플라인** ↔ cdGTS 국소 subgraph+merge(스플라인 커널 존재하나 시드 전부 linear, joint 추정기 없음) · ⓑ **CONOP 생층서 composite scaling**(Ord·Sil·Dev·Carb·Perm 숫자 백본 — biozone/occurrence/composite-scale 프리미티브 전무) · ⓒ **astronomical·magnetostratigraphic 커널 미배선**(타입은 있으나 미사용인데 중생대~신생대 백본 전부가 이것 — Neogene ATNTS·Newark·M/C-sequence) · ⓓ **상관신호/기준곡선 프리미티브 부재**(δ13C BACE 가 유일 하드코딩; Sr LOWESS·LR04 등 역함수 기준곡선 없음). **교차 격차**: 릴리스 *내* 병렬 경쟁가설(branching)·해석/보정 사슬 provenance·R04 L2 캐스케이드·게이트 과소(proxy 교차검증·fitting 내 단조성)·경계≠사건≠반응·dating 방법 semantics. **레버리지 순 권고**: ①astro/magneto 커널(어휘는 있음, 배선만) ②상관신호 tie-point 일반화(R05 확대)+기준곡선 ③생층서 composite-scale+Ch14 스플라인 노드 ④병렬 분기+R04 L2. 아래 R05·R04 L2·P06.4b·retype 데모가 이 결론을 직접 겨냥.
- [ ] **R05 — 상관 provenance**([검토 R05](devlog/20260715_R05_correlation-provenance-depth.md), GTS2012 Ch.14 요약 검토) — `tie-point`(상관 가설 = 1급 노드, rectangular σ_x) + `composite-scale`(derived, 커널은 trivial 로 시작) + `age-model`(N→M). 킬러 유스케이스 = **상관 가설 엣지 토글 → 원클릭 diff**(topology-diff·competing-models·P05 재사용). `cross-section-correlation` 소멸. **미착수.** 부수 부채 중 **spline 경로 `shared_components` 유실 버그는 선상환 완료**([R05 말미 Addendum](devlog/20260715_R05_correlation-provenance-depth.md), pytest 178→182, **미배포**) — 스플라인 평가가 연대에 선형임을 이용해 카디널 가중치로 해석적 전파(Cov 0→0.16, duration σ 0.58→0.13). 잔여: MC 가 horizon 을 독립으로 draw(marginal 과소) · loading 부호 · `fidelity` enum · `hpd95` 오칭.
- [ ] **R04 L2** — 상수 값 변경이 연대 **값**을 재계산하는 rescale 커널(raw invariant/민감도 노드). L1 공분산 배선(0.1.54~55)의 다음 단계.
- [ ] **L2/L3 확장** — L2 warn 임계(과소/과대 duration 의심) · L3 joint reconcile · 프론트 cert 뷰 L2 상세.
- [ ] **계산 커널 확장 / P06.4b** — age-depth 외 joint/베이지안(PyMC) 노드타입별 실제 커널(별도 워커). **R06 최우선 지목: `astronomical`(천문튜닝: floating 주기수 duration + anchor 절대위치 2부분 σ → shared_components 매핑)·`magnetostratigraphic`(polarity order-edge 사슬 + 이상거리→확장속도→연대, age-depth 와 동형) 커널 — 타입은 있으나 미사용, 중생대~신생대 백본 전부가 이것.**
- [ ] **PostGIS** — chrono.Locality lat/lon → PointField(공간 차원 착수 시).
- [ ] **retype diff 실데모** — Ediacaran/Cryogenian 경계 추가로 GSSA→GSSP retype 시나리오. **R06: Cryogenian base 는 2024/25 실제 비준 — 데모가 실사건 retrodiction**(cdGTS 최적합 도메인). 단 실 retype 은 증거 substrate(빙성퇴적·δ13C·proposal-status lattice·geochronologic-role 타이핑) 필요.
- [ ] **미해결 열린 질문** — 각 설계 문서 말미. → `TODOs.md` §2.
