"""四种教学竞价机制；输出固定展示周期内的期望点击与收益。"""

from dataclasses import dataclass
from math import isfinite
from typing import Literal


Mechanism = Literal["first_price", "second_price", "gsp", "quality_gsp"]
MECHANISMS: tuple[Mechanism, ...] = (
    "first_price",
    "second_price",
    "gsp",
    "quality_gsp",
)
MIN_POSITIVE_INPUT = 1e-12
MAX_NUMERIC_INPUT = 1e12
MAX_IMPRESSIONS = 1_000_000_000_000


@dataclass(frozen=True)
class Bidder:
    bidder_id: str
    bid: float
    quality: float
    value_per_click: float
    budget: float


@dataclass(frozen=True)
class AuctionRequest:
    bidders: tuple[Bidder, ...]
    slot_ctrs: tuple[float, ...]
    impressions: int


@dataclass(frozen=True)
class Allocation:
    bidder_id: str
    slot: int
    rank: int
    ranking_score: float
    bid: float
    quality: float
    value_per_click: float
    budget: float
    cpc: float
    ctr: float
    expected_clicks: float
    delivered_clicks: float
    fill_rate: float
    spend: float
    gross_value: float
    surplus: float


@dataclass(frozen=True)
class AuctionOutcome:
    mechanism: Mechanism
    ranking: tuple[str, ...]
    allocations: tuple[Allocation, ...]
    inventory_slots: int
    platform_revenue: float
    advertiser_surplus: float


def _validate_request(request: AuctionRequest) -> None:
    if not request.bidders:
        raise ValueError("至少需要一位广告主")
    ids: set[str] = set()
    for bidder in request.bidders:
        if not isinstance(bidder.bidder_id, str) or not bidder.bidder_id.strip():
            raise ValueError("广告主 ID 不能为空")
        if bidder.bidder_id in ids:
            raise ValueError("广告主 ID 必须唯一")
        ids.add(bidder.bidder_id)
        for name, value, allow_zero in (
            ("出价", bidder.bid, True),
            ("质量分", bidder.quality, False),
            ("每次点击价值", bidder.value_per_click, True),
            ("预算", bidder.budget, True),
        ):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
                raise ValueError(f"{name} 必须是有限数字")
            if value < 0 or (not allow_zero and value == 0):
                raise ValueError(f"{name} 超出允许范围")
            if value > MAX_NUMERIC_INPUT or (0 < value < MIN_POSITIVE_INPUT):
                raise ValueError(f"{name} 超出教学模型的安全数值范围（正值需在 1e-12 至 1e12 之间）")

    if not request.slot_ctrs:
        raise ValueError("至少需要一个广告位")
    previous = 1.0
    for ctr in request.slot_ctrs:
        if isinstance(ctr, bool) or not isinstance(ctr, (int, float)) or not isfinite(ctr):
            raise ValueError("广告位 CTR 必须是有限数字")
        if not 0 <= ctr <= previous:
            raise ValueError("广告位 CTR 必须介于 0 和 1，且按广告位非递增")
        if 0 < ctr < MIN_POSITIVE_INPUT:
            raise ValueError("广告位 CTR 超出教学模型的安全数值范围（正值至少为 1e-12）")
        previous = ctr
    if isinstance(request.impressions, bool) or not isinstance(request.impressions, int) or request.impressions <= 0:
        raise ValueError("展示周期内的曝光次数必须是正整数")
    if request.impressions > MAX_IMPRESSIONS:
        raise ValueError("展示周期内的曝光次数超出教学模型的安全数值范围（最多 1e12）")


def simulate_auction(request: AuctionRequest, mechanism: Mechanism) -> AuctionOutcome:
    """模拟一个周期；余额不足只缩短获胜广告主的投放，不重排广告位。"""
    _validate_request(request)
    if mechanism not in MECHANISMS:
        raise ValueError("未知竞价机制")

    eligible = [bidder for bidder in request.bidders if bidder.budget > 0]
    def score(bidder: Bidder) -> float:
        return bidder.bid * bidder.quality if mechanism == "quality_gsp" else bidder.bid

    ranked = sorted(eligible, key=lambda bidder: (-score(bidder), bidder.bidder_id))
    inventory_slots = 1 if mechanism in ("first_price", "second_price") else len(request.slot_ctrs)
    allocations: list[Allocation] = []

    for index, bidder in enumerate(ranked[:inventory_slots]):
        next_bidder = ranked[index + 1] if index + 1 < len(ranked) else None
        if mechanism == "first_price":
            cpc = bidder.bid
        elif mechanism in ("second_price", "gsp"):
            cpc = next_bidder.bid if next_bidder else 0.0
        else:
            cpc = score(next_bidder) / bidder.quality if next_bidder else 0.0

        ctr = request.slot_ctrs[index]
        expected_clicks = request.impressions * ctr
        delivered_clicks = min(expected_clicks, bidder.budget / cpc) if cpc > 0 else expected_clicks
        spend = delivered_clicks * cpc
        gross_value = delivered_clicks * bidder.value_per_click
        allocations.append(
            Allocation(
                bidder_id=bidder.bidder_id,
                slot=index + 1,
                rank=index + 1,
                ranking_score=score(bidder),
                bid=bidder.bid,
                quality=bidder.quality,
                value_per_click=bidder.value_per_click,
                budget=bidder.budget,
                cpc=cpc,
                ctr=ctr,
                expected_clicks=expected_clicks,
                delivered_clicks=delivered_clicks,
                fill_rate=delivered_clicks / expected_clicks if expected_clicks else 1.0,
                spend=spend,
                gross_value=gross_value,
                surplus=gross_value - spend,
            )
        )

    return AuctionOutcome(
        mechanism=mechanism,
        ranking=tuple(bidder.bidder_id for bidder in ranked),
        allocations=tuple(allocations),
        inventory_slots=inventory_slots,
        platform_revenue=sum(allocation.spend for allocation in allocations),
        advertiser_surplus=sum(allocation.surplus for allocation in allocations),
    )


def compare_auctions(request: AuctionRequest) -> dict[Mechanism, AuctionOutcome]:
    """以同一组输入依次运行全部四种机制。"""
    return {mechanism: simulate_auction(request, mechanism) for mechanism in MECHANISMS}
