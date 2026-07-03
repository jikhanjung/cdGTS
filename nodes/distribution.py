"""
Distribution — 불확실성 충실도 사다리 값 객체 (L0–L5).

엣지가 흘리는 것은 스칼라가 아니라 이 분포(node-graph §블렌더와 다른 지점).
DB 테이블이 아니라 *값 객체* — JSONField 에 임베드되어 NodeResult·BoundaryRecord 가 나른다.
스키마 boundary-gateway-schema.md `age.uncertainty` / 상세 distribution-representation.md.

충실도 사다리 (오름차순 = 정보 풍부):
  L0 exact       점질량 δ (GSSA). value 만, budget 없음.
  L1 sym         대칭 ± (단일 σ).
  L2 decomposed  분해 예산(analytical/systematic/model) — 계통 공유 = 공분산 열쇠.
  L3 shape       비대칭/왜곡 (median + hpd95).
  L4 joint       공유 성분 태그 (다경계 공분산 재구성).
  L5 full        사후 샘플/재실행 모델 참조.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

FIDELITY_LADDER = ["exact", "sym", "decomposed", "shape", "joint", "full"]


class DistributionError(ValueError):
    pass


@dataclass
class Distribution:
    fidelity: str
    value_ma: float | None = None          # 중앙값/점 추정
    sigma: int | None = None               # budget 신뢰수준 (1|2)
    budget: dict[str, float] = field(default_factory=dict)   # {analytical, systematic, model}
    shape: dict[str, Any] | None = None    # {median, hpd95: [lo, hi]}
    shared_components: list[str] = field(default_factory=list)  # 공유 계통 노드 참조
    posterior_ref: str | None = None       # L5 샘플/모델 참조
    note: str = ""

    def __post_init__(self):
        if self.fidelity not in FIDELITY_LADDER:
            raise DistributionError(
                f"unknown fidelity {self.fidelity!r}; expected one of {FIDELITY_LADDER}"
            )
        if self.fidelity == "exact":
            if self.value_ma is None:
                raise DistributionError("exact(점질량)은 value_ma 필수")
            if self.budget:
                raise DistributionError("exact(점질량)은 budget 을 가질 수 없음")

    @property
    def level(self) -> int:
        """사다리 층 (0–5)."""
        return FIDELITY_LADDER.index(self.fidelity)

    # --- 직렬화 (빈 값은 생략해 JSON 을 깔끔하게; 왕복은 default 로 복원) ---
    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"fidelity": self.fidelity}
        if self.value_ma is not None:
            out["value_ma"] = self.value_ma
        if self.sigma is not None:
            out["sigma"] = self.sigma
        if self.budget:
            out["budget"] = dict(self.budget)
        if self.shape is not None:
            out["shape"] = self.shape
        if self.shared_components:
            out["shared_components"] = list(self.shared_components)
        if self.posterior_ref is not None:
            out["posterior_ref"] = self.posterior_ref
        if self.note:
            out["note"] = self.note
        return out

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Distribution":
        return cls(
            fidelity=data["fidelity"],
            value_ma=data.get("value_ma"),
            sigma=data.get("sigma"),
            budget=dict(data.get("budget", {})),
            shape=data.get("shape"),
            shared_components=list(data.get("shared_components", [])),
            posterior_ref=data.get("posterior_ref"),
            note=data.get("note", ""),
        )

    # --- 편의 생성자 ---
    @classmethod
    def exact(cls, value_ma: float, note: str = "") -> "Distribution":
        """GSSA 점질량 δ(value). Clamp{pin} 의 값 모양."""
        return cls(fidelity="exact", value_ma=value_ma, note=note)

    @classmethod
    def symmetric(cls, value_ma: float, pm: float, sigma: int = 2) -> "Distribution":
        """대칭 ± (레거시 ±2σ)."""
        return cls(fidelity="sym", value_ma=value_ma, sigma=sigma, budget={"analytical": pm})
