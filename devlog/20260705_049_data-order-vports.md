# 20260705_049 — data↔order 세로 포트 (프로토타입)

> order 체인은 세로 사다리인데 데이터 값은 옆(`out`)에서 나와 위/아래 order 로 꺾여 들어감 — 세로 일관성 깨짐.
> 데이터 노드에 **위=older / 아래=younger** 소스 포트를 줘서 엣지가 짧은 세로 선분이 되게. Triassic 그룹 프로토타입.

## 설계
- 한 경계는 **위 이웃보다 older, 아래 이웃보다 younger** → `top=older 역할`(위쪽 order 로), `bottom=younger 역할`(아래쪽 order 로).
  order 노드(top=younger입력, bottom=older입력)와 맞물려 `data.older(top)→order.older(bottom)`, `data.younger(bottom)→order.younger(top)`.
  **오배선 방지·자기설명.**
- **엔진 중립**: 커널은 order 노드의 target_port(older/younger)로만 읽음 — 소스 핸들 위치는 뷰 전용. cert·bake 불변 확인.
- **두 얼굴 분리**: 옆 `out`(우측) = "값을 낸다"(→ gateway/ICC 표), top/bottom = "시간축 위의 점"(→ order).

## 한 일
- seed `02_nodes`: published-age 에 `older`/`younger` out 포트 추가(`out` 유지).
- `CdgtsNode.jsx`: 이름이 older/younger 인 out 포트는 위/아래(Position.Top/Bottom)에 order 색으로 렌더. 나머지 out 은 우측.
- seed `03_graphs`: Triassic 그룹 order 엣지 13개 source_port 를 역할(older/younger)로 재지정. adm(process) tie 는 유지.

## 검증
- reseed: published-age out=[older,out,younger] · 엣지 `pub-olenekian.older→ord-36.older` 등 정확 · cert {L1,L2 pass} · bake 42(불변).
- `pytest` **81 passed** · 프론트 빌드 클린. 마이그레이션 없음.

## 이월
- 경계 생산 process 노드(adm 등)에도 top/bottom 확장 → 완전 세로 일관성.
- 브라우저 육안(세로 사다리·핸들 색) · 좋으면 나머지 period·period 체인에도 적용.
