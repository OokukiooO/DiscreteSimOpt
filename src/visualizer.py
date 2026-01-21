from __future__ import annotations

import csv
from pathlib import Path
from typing import List, Dict

import matplotlib.pyplot as plt
from matplotlib import font_manager


def _setup_chinese_font() -> None:
    candidates = [
        "Microsoft YaHei",
        "SimHei",
        "SimSun",
        "Noto Sans CJK SC",
        "WenQuanYi Micro Hei",
    ]
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in available:
            plt.rcParams["font.sans-serif"] = [name]
            break
    plt.rcParams["axes.unicode_minus"] = False


def plot_comparison(summary_records: List[Dict], output_dir: str | Path, filename: str | None = None) -> None:
    """
    生成柱状图对比不同策略的 H/N 平均拖期。
    summary_records: [{dataset, strategy, mean_tardiness_h, mean_tardiness_n}]
    """
    _setup_chinese_font()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    datasets = sorted({r["dataset"] for r in summary_records})
    strategies = sorted({r["strategy"] for r in summary_records})

    for dataset in datasets:
        data = [r for r in summary_records if r["dataset"] == dataset]
        h_vals = [next(r["mean_tardiness_h"] for r in data if r["strategy"] == s) for s in strategies]
        n_vals = [next(r["mean_tardiness_n"] for r in data if r["strategy"] == s) for s in strategies]

        x = list(range(len(strategies)))
        width = 0.35

        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.bar([i - width / 2 for i in x], h_vals, width, label="H")
        ax.bar([i + width / 2 for i in x], n_vals, width, label="N")
        ax.set_xticks(x)
        ax.set_xticklabels(strategies)
        ax.set_ylabel("平均拖期 (分钟)")
        ax.set_title(f"{dataset} 策略对比")
        ax.legend()
        fig.tight_layout()

        if filename:
            fig_path = output_dir / filename
        else:
            fig_path = output_dir / f"comparison_{dataset}.png"
        fig.savefig(fig_path, dpi=200)
        plt.close(fig)


def plot_gantt(
    results: List[Dict],
    output_dir: str | Path | None = None,
    output_path: str | Path | None = None,
    filename: str | None = None,
    max_jobs: int = 50,
) -> None:
    """
    绘制甘特图，区分机器（A/B）和订单类型颜色。
    results: list of dicts with start_time, end_time, machine, job_type, job_id
    """
    _setup_chinese_font()
    if output_path is None:
        if output_dir is None:
            raise ValueError("plot_gantt 需要 output_dir 或 output_path")
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / (filename or "gantt_chart.png")
    output_path = Path(output_path)
    rows = sorted(results, key=lambda x: x["start_time"])[:max_jobs]

    y_map = {"A": 10, "B": 30}
    colors = {"H": "#d62728", "N": "#1f77b4"}

    fig, ax = plt.subplots(figsize=(10, 5))
    for r in rows:
        y = y_map.get(r["machine"], 10)
        ax.broken_barh([(r["start_time"], r["end_time"] - r["start_time"])], (y, 8),
                       facecolors=colors.get(r["job_type"], "#7f7f7f"))
        ax.text(r["start_time"], y + 9, str(r["job_id"]), fontsize=6, alpha=0.6)

    ax.set_yticks([10, 30])
    ax.set_yticklabels(["A 机", "B 机"])
    ax.set_xlabel("时间 (分钟)")
    ax.set_title("前 50 个订单甘特图")
    ax.grid(True, axis="x", linestyle="--", alpha=0.3)
    fig.tight_layout()

    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def export_results_csv(results: List[Dict], output_path: str | Path) -> None:
    output_path = Path(output_path)
    if not results:
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)
