import math

import pytest

from adlab.algorithms.auctions import (
    AuctionRequest,
    Bidder,
    compare_auctions,
    simulate_auction,
)


@pytest.fixture
def auction_request():
    return AuctionRequest(
        bidders=(
            Bidder("A", bid=5, quality=1, value_per_click=8, budget=1000),
            Bidder("B", bid=4, quality=2, value_per_click=6, budget=1000),
            Bidder("C", bid=2, quality=1, value_per_click=3, budget=1000),
        ),
        slot_ctrs=(0.10, 0.05),
        impressions=1000,
    )


def test_first_and_second_price_are_single_slot(auction_request):
    first = simulate_auction(auction_request, "first_price")
    second = simulate_auction(auction_request, "second_price")
    assert first.ranking == ("A", "B", "C")
    assert len(first.allocations) == len(second.allocations) == 1
    assert first.allocations[0].slot == second.allocations[0].slot == 1
    assert first.allocations[0].cpc == pytest.approx(5)
    assert second.allocations[0].cpc == pytest.approx(4)
    assert first.platform_revenue == pytest.approx(500)
    assert second.platform_revenue == pytest.approx(400)
    assert first.allocations[0].surplus == pytest.approx(300)
    assert second.allocations[0].surplus == pytest.approx(400)


def test_gsp_uses_next_ranked_bid_for_each_slot(auction_request):
    result = simulate_auction(auction_request, "gsp")
    assert result.ranking == ("A", "B", "C")
    assert [allocation.bidder_id for allocation in result.allocations] == ["A", "B"]
    assert [allocation.cpc for allocation in result.allocations] == pytest.approx([4, 2])
    assert [allocation.expected_clicks for allocation in result.allocations] == pytest.approx([100, 50])
    assert result.platform_revenue == pytest.approx(500)


def test_quality_adjusted_gsp_changes_rank_and_scales_cpc(auction_request):
    result = simulate_auction(auction_request, "quality_gsp")
    assert result.ranking == ("B", "A", "C")
    assert [allocation.cpc for allocation in result.allocations] == pytest.approx([2.5, 2])
    assert result.platform_revenue == pytest.approx(350)
    assert [allocation.surplus for allocation in result.allocations] == pytest.approx([350, 300])


def test_budget_caps_spend_without_reallocating_slot(auction_request):
    capped = AuctionRequest(
        bidders=(Bidder("A", 5, 1, 8, 250),) + auction_request.bidders[1:],
        slot_ctrs=auction_request.slot_ctrs,
        impressions=auction_request.impressions,
    )
    result = simulate_auction(capped, "first_price")
    allocation = result.allocations[0]
    assert allocation.bidder_id == "A"
    assert allocation.expected_clicks == pytest.approx(100)
    assert allocation.delivered_clicks == pytest.approx(50)
    assert allocation.fill_rate == pytest.approx(0.5)
    assert allocation.spend == pytest.approx(250)
    assert allocation.surplus == pytest.approx(150)


def test_zero_budget_bidder_is_ineligible(auction_request):
    no_budget = AuctionRequest(
        bidders=(Bidder("A", 5, 1, 8, 0),) + auction_request.bidders[1:],
        slot_ctrs=auction_request.slot_ctrs,
        impressions=auction_request.impressions,
    )
    result = simulate_auction(no_budget, "second_price")
    assert result.ranking == ("B", "C")
    assert result.allocations[0].bidder_id == "B"
    assert result.allocations[0].cpc == pytest.approx(2)


def test_last_allocated_bidder_pays_zero_without_reserve():
    auction_request = AuctionRequest(
        bidders=(Bidder("A", 5, 1, 8, 100), Bidder("B", 4, 1, 6, 100)),
        slot_ctrs=(0.10, 0.05),
        impressions=1000,
    )
    result = simulate_auction(auction_request, "gsp")
    assert result.allocations[1].cpc == 0
    assert result.allocations[1].delivered_clicks == pytest.approx(50)
    assert result.allocations[1].spend == 0


def test_equal_scores_have_deterministic_id_tiebreak():
    auction_request = AuctionRequest(
        bidders=(Bidder("B", 5, 1, 8, 100), Bidder("A", 5, 1, 8, 100)),
        slot_ctrs=(0.1,),
        impressions=100,
    )
    assert simulate_auction(auction_request, "gsp").ranking == ("A", "B")


def test_compare_returns_all_four_mechanisms(auction_request):
    results = compare_auctions(auction_request)
    assert set(results) == {"first_price", "second_price", "gsp", "quality_gsp"}


@pytest.mark.parametrize(
    "bad_request",
    [
        AuctionRequest((Bidder("A", -1, 1, 2, 100),), (0.1,), 100),
        AuctionRequest((Bidder("A", 1, 0, 2, 100),), (0.1,), 100),
        AuctionRequest((Bidder("A", 1, 1, 2, math.nan),), (0.1,), 100),
        AuctionRequest((Bidder("A", 1, 1, 2, 100), Bidder("A", 2, 1, 3, 100)), (0.1,), 100),
        AuctionRequest((Bidder("A", 1, 1, 2, 100),), (0.05, 0.1), 100),
        AuctionRequest((Bidder("A", 1, 1, 2, 100),), (0.1,), 0),
    ],
)
def test_invalid_inputs_are_rejected(bad_request):
    with pytest.raises(ValueError):
        simulate_auction(bad_request, "gsp")


def test_unknown_mechanism_is_rejected(auction_request):
    with pytest.raises(ValueError):
        simulate_auction(auction_request, "vcg")
