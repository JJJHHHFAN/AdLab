"""合成数据 CTR 预测的交互式教学页面。"""

from dataclasses import asdict

import streamlit as st

from adlab.algorithms.ctr import CTRDataSplit, CTRExperimentResult, run_ctr_experiment, split_ctr_data
from adlab.charts.ctr import calibration_figure, probability_figure, roc_figure
from adlab.data.ctr_synthetic import generate_ctr_data
from adlab.data.records import DEFAULT_DB_PATH, save_ctr_run


METRIC_LABELS = (
    ("auc_roc", "AUC-ROC"),
    ("log_loss", "Log Loss"),
    ("precision", "Precision"),
    ("recall", "Recall"),
    ("brier_score", "Brier Score"),
)


def render_ctr() -> None:
    st.caption("阶段 4  /  CLICK-THROUGH RATE PREDICTION")
    st.title("CTR 预测 · Click-Through Rate")
    st.write("用合成曝光数据训练概率模型，比较验证集表现，再检查选中模型在未参与选择的测试集上的表现。")

    st.subheader("1 · 实验原理")
    st.write(
        "CTR 模型估计一次展示被点击的概率。Logistic Regression 提供可解释的线性基准；"
        "Random Forest 可表达非线性关系。两者都输出概率，而不是直接决定是否投放。"
    )
    st.latex(r"P(Y=1\mid x)=\sigma(\beta_0+\beta^\top x),\qquad \sigma(z)=\frac{1}{1+e^{-z}}")
    st.caption("数据、用户 ID 和历史记录均为合成；历史计数固定来自模拟期之前，当前点击不会回填到特征中。")

    st.subheader("2 · 参数设置与运行实验")
    previous_config = st.session_state["ctr_run"][3] if "ctr_run" in st.session_state else {}
    with st.form("ctr_inputs"):
        left, right = st.columns(2)
        n_exposures = left.number_input(
            "合成曝光数量", min_value=1000, max_value=20_000,
            value=previous_config.get("n_exposures", 5000), step=1000,
        )
        seed = right.number_input(
            "随机种子", min_value=0, max_value=2**32 - 1,
            value=previous_config.get("seed", 42), step=1,
        )
        mode = st.radio(
            "数据划分", options=("time", "random"),
            format_func=lambda value: "按时间顺序（推荐）" if value == "time" else "随机分层",
            index=0 if previous_config.get("split_mode", "time") == "time" else 1,
            horizontal=True,
        )
        threshold = st.number_input(
            "分类阈值（仅用于 Precision / Recall）", min_value=0.01, max_value=0.99,
            value=previous_config.get("threshold", 0.10), step=0.01,
        )
        st.caption("固定比例：训练 60% · 验证 20% · 测试 20%。类别编码与数值标准化只在训练集拟合。")
        submitted = st.form_submit_button("运行 CTR 实验", type="primary")

    if submitted:
        st.session_state.pop("ctr_run", None)
        st.session_state.pop("ctr_saved_id", None)
        try:
            frame = generate_ctr_data(int(n_exposures), int(seed))
            split = split_ctr_data(frame, mode=mode, seed=int(seed))
            result = run_ctr_experiment(split, seed=int(seed), threshold=float(threshold))
        except ValueError as error:
            st.error(str(error))
        else:
            config = {
                "n_exposures": int(n_exposures), "seed": int(seed),
                "split_mode": mode, "threshold": float(threshold),
                "data_source": "synthetic",
            }
            st.session_state["ctr_run"] = (frame, split, result, config)

    if "ctr_run" in st.session_state:
        frame, split, result, config = st.session_state["ctr_run"]
        _render_results(frame, split, result, config)

    st.subheader("现实业务应用")
    st.write("可作为离线建模流程的练习：先定义曝光时可用的特征，再用验证集选择模型，并检查概率是否可靠。真实投放还需要线上实验、延迟标签处理和持续监控。")
    st.subheader("模型局限性")
    st.write(
        "本实验使用人为生成的点击机制，只有少量类别和固定的前期历史快照；没有真实用户隐私、竞价反馈、概念漂移治理或因果效应估计。"
        "测试集指标只说明模型在这组合成样本上的表现，不能推断真实广告效果。"
    )


def _metric_row(name: str, metrics) -> dict:
    values = asdict(metrics)
    return {
        "模型": name,
        **{label: "N/A" if values[key] is None else round(values[key], 4) for key, label in METRIC_LABELS},
    }


def _render_results(frame, split: CTRDataSplit, result: CTRExperimentResult, config: dict) -> None:
    st.subheader("3 · 数据与划分")
    st.info(
        f"本次数据为合成曝光 {len(frame):,} 条，整体模拟点击率 {frame.clicked.mean():.2%}；"
        f"划分方式：{'时间顺序' if split.mode == 'time' else '随机分层'}。"
    )
    st.caption(f"以下结果对应上次运行参数：曝光 {config['n_exposures']:,} 条 · 种子 {config['seed']} · 分类阈值 {config['threshold']:.2f}。")
    counts = {"train": len(split.train), "validation": len(split.validation), "test": len(split.test)}
    st.write(f"训练集 {counts['train']:,} 条 · 验证集 {counts['validation']:,} 条 · 测试集 {counts['test']:,} 条")
    if split.mode == "time":
        st.caption(
            f"时间范围：训练至 {split.train.event_time.max()}；验证至 {split.validation.event_time.max()}；"
            f"测试从 {split.test.event_time.min()} 开始。"
        )
    st.caption("字段预览：匿名用户与广告、类别、展示时段、设备、广告位、前期历史互动、当前点击标签。")
    with st.expander("查看前 12 条合成曝光"):
        st.dataframe(frame.head(12), hide_index=True, width="stretch")

    st.subheader("4 · 模型比较与测试结果")
    st.write("Logistic Regression 与 Random Forest 的下表指标都来自验证集。按较低的 Log Loss 选模型，然后评估一次测试集。")
    st.dataframe(
        [_metric_row(name, metrics) for name, metrics in result.validation_metrics.items()],
        hide_index=True, width="stretch",
    )
    st.success(f"验证集选中：{result.selected_name}。以下测试集指标仅针对该模型。")
    st.dataframe([_metric_row(result.selected_name, result.test_metrics)], hide_index=True, width="stretch")
    st.caption(f"Precision 与 Recall 的概率阈值为 {result.threshold:.2f}；AUC、Log Loss 与 Brier Score 使用原始预测概率。")
    if result.test_metrics.precision is None:
        st.warning("此阈值下测试集没有预测点击：Precision 未定义，显示 N/A；真实点击仍存在，因此 Recall 为 0。")

    st.subheader("5 · 结果可视化")
    st.plotly_chart(roc_figure(result.test_labels, result.test_probabilities), width="stretch")
    st.plotly_chart(probability_figure(result.test_labels, result.test_probabilities), width="stretch")
    st.plotly_chart(calibration_figure(result.test_labels, result.test_probabilities), width="stretch")

    st.subheader("6 · 结果解释")
    st.write(
        "AUC 描述排序能力；Log Loss 对过于自信的错误预测惩罚更大；Brier Score 衡量概率与 0/1 结果的均方差。"
        "校准图接近对角线表示预测概率与分组实际点击比例更一致。"
    )
    st.markdown("**计算示例：** 若四次展示的预测概率是 0.1、0.7、0.2、0.6，真实点击是 0、1、0、1，Brier Score = (0.01 + 0.09 + 0.04 + 0.16) / 4 = **0.075**。")
    st.button(
        "保存本次 CTR 实验", disabled="ctr_saved_id" in st.session_state,
        on_click=_save_current_run, args=(config, result, counts),
    )
    if "ctr_saved_id" in st.session_state:
        st.success(f"已保存为本地 CTR 记录 #{st.session_state['ctr_saved_id']}。")


def _save_current_run(config: dict, result: CTRExperimentResult, counts: dict[str, int]) -> None:
    if "ctr_saved_id" not in st.session_state:
        st.session_state["ctr_saved_id"] = save_ctr_run(DEFAULT_DB_PATH, config, result, counts)
