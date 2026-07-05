# 20260705_070 — 버그픽스: 대형 그래프 선택 박스 얼어붙음(재렌더 폭풍)

> [068](20260705_068_fix-selection-autopan.md)(auto-pan) 이후 잔여 증상: example 4(icc-partial, 42노드)처럼
> 밀집한 그래프에서 좌-드래그 선택 시 좌표가 특정 값에 얼어붙음(간헐적, 큰 네트워크에서 뚜렷).

## 원인
컨트롤드 모드 + 무거운 파생 뷰의 조합. rubber-band 선택 중 React Flow 는 겹치는 노드·연결 엣지에
`select` 변경을 매 pointermove 마다 쏟아낸다 → `onNodesChange`/`onEdgesChange` 가 `setNodes`/`setEdges` →
`buildView` 전체 재실행 → **모든 viewEdges 가 매번 새 객체(`{...e}`)** 로 만들어져 40여 엣지가 매 프레임
bezier 재계산·재렌더. 메인스레드가 밀리며 `onPointerMove` 가 지연/합쳐져 선택 박스가 얼어붙는다.
(auto-pan 은 068 에서 껐으므로 별개.)

## 고침 (`Editor.jsx`)
`buildView` 를 **구조**(nodeRep·그룹·스텁·엣지 라우팅)만 반환하도록 바꾸고, selection·위치를 분리:
- `topoSig`/`edgeSig` — selection·좌표를 제외한 토폴로지 시그니처(노드 존재·그룹 소속·라벨 / 엣지 배선).
- `struct = useMemo(buildView, [topoSig, edgeSig, groups, activeGroup])` — 구조 변화 때만 재빌드.
  선택/드래그 중엔 캐시 → `struct.viewEdges` identity 안정.
- 가벼운 오버레이: `viewNodes` 는 현재 실노드(선택 반영, identity 보존) + 그룹/스텁, `viewEdges` 는
  `struct.viewEdges` 에 **selected 만** 덧입힘(토글된 것만 새 객체).
- 결과: 선택 틱마다 **실제로 선택이 바뀐 노드·엣지만** 재렌더. 노드 드래그도 엣지 객체를 안 갈아끼워 가벼워짐.

## 검증
- 프론트 빌드 클린. 백엔드 무관. (068 auto-pan 픽스와 함께 동작.)
