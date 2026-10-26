"""四种广告竞价机制的交互式教学页面。"""

import streamlit as st

from adlab.algorithms.auctions import (
    MAX_IMPRESSIONS,
    MAX_NUMERIC_INPUT,
    AuctionRequest,
    Bidder,
    Mechanism,
    compare_auctions,
)
from adlab.charts.comparison import comparison_bar
from adlab.data.records import DEFAULT_DB_PATH, save_auction_run


LABELS: dict[Mechanism, str] = {
    "first_price": "第一价格密封拍卖",
    "second_price": "第二价格密封拍卖",
    "gsp": "广义第二价格拍卖（GSP）",
    "quality_gsp": "质量分调整 GSP",
}


def _bidder_defaults(index: int) -> tuple[float, float, float]:
    examples = ((5.0, 1.0, 8.0), (4.0, 2.0, 6.0), (2.0, 1.0, 3.0))
    if index < len(examples):
        return examples[index]
    bid = max(0.5, 2.0 - (index - 2) * 0.5)
    return bid, 1.0, bid + 1.0


def render_auction() -> None:
    st.caption("阶段 3  /  AUCTION MECHANISMS")
    st.title("广告竞价 · Ad Auctions")
    st.write("修改出价、质量分、广告位点击率与预算，观察排名、每次点击支付和期望收益如何变化。")

    st.subheader("1 · 实验原理")
    st.write(
        "第一价格与第二价格密封拍卖只分配顶部一个广告位。GSP 将多个广告位按出价排序，"
        "每位获胜者按下一名的出价计费；质量分版本按出价 × 质量分排序。"
    )
    st.latex(r"s_i=b_iq_i,\qquad \mathrm{CPC}^{\mathrm{quality}}_i="
             r"\frac{s_{i+1}}{q_i},\qquad \mathrm{Revenue}=\sum_i \mathrm{Spend}_i")
    st.caption("本实验固定底价为 0，按点击收费；质量分只影响排名与价格，不改变给定的广告位 CTR。")

    st.subheader("2 · 参数设置与运行实验")
    bidder_count, slot_count = st.columns(2)
    number_of_bidders = bidder_count.number_input("广告主数量", min_value=2, max_value=8, value=3, step=1)
    number_of_slots = slot_count.number_input("广告位数量", min_value=1, max_value=5, value=2, step=1)
    shape = (number_of_bidders, number_of_slots)
    if st.session_state.get("auction_shape") != shape:
        st.session_state["auction_shape"] = shape
        st.session_state.pop("auction_run", None)
        st.session_state.pop("auction_saved_id", None)

    st.caption("预填数字是教学算例。出价、点击价值、预算与收入均为抽象货币单位，不代表真实市场价格。")
    with st.form("auction_inputs"):
        impressions = st.number_input(
            "每个广告位在本周期的展示机会", min_value=1, max_value=MAX_IMPRESSIONS,
            value=1000, step=100,
        )
        bidders: list[Bidder] = []
        for index in range(number_of_bidders):
            bidder_id = chr(ord("A") + index)
            default_bid, default_quality, default_value = _bidder_defaults(index)
            with st.container(border=True):
                st.markdown(f"**广告主 {bidder_id}**")
                left, right = st.columns(2)
                bid = left.number_input(
                    f"{bidder_id} 出价 / 次点击", min_value=0.0, max_value=MAX_NUMERIC_INPUT,
                    value=default_bid, step=0.5,
                )
                quality = right.number_input(
                    f"{bidder_id} 质量分", min_value=0.1, max_value=MAX_NUMERIC_INPUT,
                    value=default_quality, step=0.1,
                )
                value = left.number_input(
                    f"{bidder_id} 每次点击价值", min_value=0.0, max_value=MAX_NUMERIC_INPUT,
                    value=default_value, step=0.5,
                )
                budget = right.number_input(
                    f"{bidder_id} 周期预算上限", min_value=0.0, max_value=MAX_NUMERIC_INPUT,
                    value=1000.0, step=50.0,
                )
                bidders.append(Bidder(bidder_id, bid, quality, value, budget))

        st.markdown("**广告位点击率（从高位到低位）**")
        ctrs = []
        for index in range(number_of_slots):
            default_ctr = round(10 / (2**index), 2)
            percent = st.number_input(
                f"广告位 {index + 1} CTR（%）",
                min_value=0.0,
                max_value=100.0,
                value=default_ctr,
                step=0.5,
            )
            ctrs.append(percent / 100)
        submitted = st.form_submit_button("运行竞价实验", type="primary")

    if submitted:
        st.session_state.pop("auction_run", None)
        st.session_state.pop("auction_saved_id", None)
        request = AuctionRequest(tuple(bidders), tuple(ctrs), impressions)
        try:
            results = compare_auctions(request)
        except ValueError as error:
            st.error(str(error))
        else:
            st.session_state["auction_run"] = (request, results)

    if "auction_run" in st.session_state:
        request, results = st.session_state["auction_run"]
        _render_results(request, results)

    st.subheader("现实业务应用")
    st.write("可用来理解出价策略、广告位价值和质量调整如何改变分配与价格；预算截断展示了投放量受限时的机会成本。")
    st.subheader("模型局限性")
    st.write(
        "这是静态教学模拟：没有底价、动态重排、竞争对手策略变化、预算节奏、转化延迟或平台真实质量模型。"
        "实际广告平台的排名和 CPC 还取决于更多实时因素，不能用本页计算结果预测真实投放。"
    )


def _render_results(request: AuctionRequest, results: dict) -> None:
    st.subheader("3 · 结果可视化")
    st.info(
        "第一价格与第二价格仅使用顶部 1 个广告位；GSP 与质量分机制使用全部所设广告位。"
        "两组图各自可比，跨组平台收入因库存不同不可直接比较。"
    )
    st.plotly_chart(
        comparison_bar(
            [LABELS["first_price"], LABELS["second_price"]],
            [results["first_price"].platform_revenue, results["second_price"].platform_revenue],
            title="单广告位机制 · 平台期望收入",
            unit="货币单位",
        ),
        width="stretch",
    )
    st.plotly_chart(
        comparison_bar(
            [LABELS["gsp"], LABELS["quality_gsp"]],
            [results["gsp"].platform_revenue, results["quality_gsp"].platform_revenue],
            title="多广告位机制 · 平台期望收入",
            unit="货币单位",
        ),
        width="stretch",
    )

    st.subheader("4 · 排名、支付与广告主收益")
    for mechanism, result in results.items():
        with st.expander(LABELS[mechanism], expanded=mechanism == "first_price"):
            st.write("可参与排名：" + (" → ".join(result.ranking) if result.ranking else "无合格广告主"))
            col1, col2 = st.columns(2)
            col1.metric("平台期望收入", f"{result.platform_revenue:,.2f}")
            col2.metric("广告主期望净收益合计", f"{result.advertiser_surplus:,.2f}")
            if result.allocations:
                st.dataframe(
                    [
                        {
                            "广告位": item.slot,
                            "广告主": item.bidder_id,
                            "排序分": f"{item.ranking_score:.2f}",
                            "每次点击支付": f"{item.cpc:.2f}",
                            "期望点击": f"{item.expected_clicks:.1f}",
                            "预算后点击": f"{item.delivered_clicks:.1f}",
                            "预算后投放率": f"{item.fill_rate:.1%}",
                            "期望支出": f"{item.spend:.2f}",
                            "期望净收益": f"{item.surplus:+.2f}",
                        }
                        for item in result.allocations
                    ],
                    hide_index=True,
                    width="stretch",
                )
            else:
                st.caption("没有广告主获得广告位。")

    st.subheader("5 · 结果解释")
    st.write(
        "平台收入 = 各广告主预算后期望支出之和；广告主净收益 = 点击价值 × 预算后期望点击 − 支出。"
        "若预算不足，本周期只投放部分展示机会，空出的机会不会再分配。"
    )
    st.caption(f"本次设置：每个广告位 {request.impressions:,} 次展示机会；最后一名在零底价模型下每次点击支付 0。")
    st.markdown(
        "**计算示例：** 出价 A=5、B=4、C=2，两个广告位 CTR 为 10%、5%，每位 1,000 次展示机会。"
        "GSP 中 A 支付 4、获得期望点击 100；B 支付 2、获得期望点击 50，平台期望收入为 500。"
    )
    st.button(
        "保存本次竞价实验",
        disabled="auction_saved_id" in st.session_state,
        on_click=_save_current_run,
        args=(request, results),
    )
    if "auction_saved_id" in st.session_state:
        st.success(f"已保存为本地竞价记录 #{st.session_state['auction_saved_id']}。")


def _save_current_run(request: AuctionRequest, results: dict) -> None:
    if "auction_saved_id" not in st.session_state:
        st.session_state["auction_saved_id"] = save_auction_run(DEFAULT_DB_PATH, request, results)
