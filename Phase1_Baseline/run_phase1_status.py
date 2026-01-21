from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List, Dict

from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src import config
from src.data_loader import load_and_process_data
from src.scheduler import STRATEGY_FCFS, STRATEGY_EDD, STRATEGY_MINSLK
from src.simulation_engine import JobShop, summarize_results
from src.visualizer import plot_comparison, plot_gantt, export_results_csv


def _to_dict_results(results) -> List[Dict]:
    return [
        {
            "job_id": r.job_id,
            "job_type": r.job_type,
            "arrival_time": r.arrival_time,
            "start_time": r.start_time,
            "end_time": r.end_time,
            "due_date": r.due_date,
            "tardiness": r.tardiness,
            "machine": r.machine,
        }
        for r in results
    ]


def generate_markdown_report(metrics_dict: Dict, output_path: Path) -> None:
    dataset = metrics_dict["dataset"]
    strategies = metrics_dict["strategies"]
    best_strategy = metrics_dict["best_strategy"]

    def _improve(base: float, new: float) -> float:
        if base == 0:
            return 0.0
        return (base - new) / base * 100.0

    fcfs_h = strategies[STRATEGY_FCFS]["mean_tardiness_h"]
    fcfs_n = strategies[STRATEGY_FCFS]["mean_tardiness_n"]
    best_h = strategies[best_strategy]["mean_tardiness_h"]
    best_n = strategies[best_strategy]["mean_tardiness_n"]

    improve_h = _improve(fcfs_h, best_h)
    improve_n = _improve(fcfs_n, best_n)

    if best_h == 0 and best_n == 0:
        status_text = "产能充裕，整体拖期为 0，规则差异不明显。"
    elif best_h > 0 and best_n > 0:
        status_text = "系统存在拥堵，调度规则对拖期有明显影响。"
    else:
        status_text = "部分订单出现拖期，规则差异对目标有一定影响。"

    with output_path.open("w", encoding="utf-8") as f:
        f.write("# 阶段一：现状分析（Data1.3）\n\n")
        f.write("## 参数摘要\n")
        f.write(f"- 数据集：{dataset}\n")
        f.write(f"- A机数量：{config.A_MACHINES}\n")
        f.write(f"- B机数量：{config.B_MACHINES}\n\n")

        f.write("## 关键指标表\n")
        f.write("| 策略 | H 平均拖期 (min) | N 平均拖期 (min) |\n")
        f.write("|---|---:|---:|\n")
        for name, metrics in strategies.items():
            f.write(
                f"| {name} | {metrics['mean_tardiness_h']:.2f} | {metrics['mean_tardiness_n']:.2f} |\n"
            )

        f.write("\n## 结论分析\n")
        f.write(f"最佳规则：{best_strategy}\n\n")
        f.write(
            f"相较 FCFS，H 类平均拖期改善 {improve_h:.2f}% ，"
            f"N 类平均拖期改善 {improve_n:.2f}%。\n\n"
        )
        f.write(f"状态判断：{status_text}\n")


def run_phase1(output_dir: str | Path) -> Dict:
    data_file = ROOT / "native_data" / "csv" / "Data1.3.csv"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    strategies = [STRATEGY_FCFS, STRATEGY_EDD, STRATEGY_MINSLK]
    dataset_name = "Data1.3"

    jobs = load_and_process_data(data_file)

    summary_records: List[Dict] = []
    all_results: Dict[str, List[Dict]] = {}

    with tqdm(total=len(strategies), desc="阶段一进度") as pbar:
        for strategy in strategies:
            print(f"阶段一分析 {dataset_name} - 策略 {strategy} ...")
            shop = JobShop(jobs=jobs, strategy=strategy)
            results = shop.run()
            metrics = summarize_results(results)
            print(
                f"完成。H类平均拖期: {metrics['mean_tardiness_h']:.2f}m，"
                f"N类平均拖期: {metrics['mean_tardiness_n']:.2f}m"
            )

            result_dicts = _to_dict_results(results)
            all_results[strategy] = result_dicts

            csv_path = output_dir / f"results_{dataset_name}_{strategy}.csv"
            export_results_csv(result_dicts, csv_path)

            summary_records.append({
                "dataset": dataset_name,
                "strategy": strategy,
                **metrics,
            })
            pbar.update(1)

    plot_comparison(summary_records, output_dir, filename="Phase1_comparison_bar_chart.png")

    best_record = min(summary_records, key=lambda x: x["mean_tardiness_h"])
    gantt_path = output_dir / "Phase1_gantt_chart.png"
    plot_gantt(all_results[best_record["strategy"]], output_dir=output_dir, filename="Phase1_gantt_chart.png")

    metrics_dict = {
        "dataset": dataset_name,
        "strategies": {r["strategy"]: {
            "mean_tardiness_h": r["mean_tardiness_h"],
            "mean_tardiness_n": r["mean_tardiness_n"],
        } for r in summary_records},
        "best_strategy": best_record["strategy"],
    }
    report_path = output_dir / "Phase1_Analysis.md"
    generate_markdown_report(metrics_dict, report_path)

    try:
        os.startfile(output_dir)  # type: ignore[attr-defined]
    except Exception:
        print(f"结果已保存至：{output_dir}")

    return {
        "summary_records": summary_records,
        "report_path": report_path,
        "comparison_chart": output_dir / "Phase1_comparison_bar_chart.png",
        "gantt_chart": gantt_path,
    }


def main() -> None:
    run_phase1(Path(__file__).resolve().parent / "results")


if __name__ == "__main__":
    main()
