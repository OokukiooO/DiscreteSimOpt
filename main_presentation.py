from __future__ import annotations

import os
import sys
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

PHASE1_DIR = ROOT / "Phase1_Baseline"
PHASE2_DIR = ROOT / "Phase2_Optimization"

if str(PHASE1_DIR) not in sys.path:
    sys.path.append(str(PHASE1_DIR))
if str(PHASE2_DIR) not in sys.path:
    sys.path.append(str(PHASE2_DIR))

from Phase1_Baseline.run_phase1_status import run_phase1
from Phase2_Optimization.run_phase2_opt import run_phase2


def _reset_output_dir(output_dir: Path) -> None:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)


def _merge_reports(output_dir: Path, phase1_report: Path, phase2_report: Path) -> Path:
    final_report = output_dir / "FINAL_PROJECT_SUMMARY.md"
    with final_report.open("w", encoding="utf-8") as f:
        f.write("# 项目最终汇总\n\n")
        f.write("## 阶段一分析\n\n")
        f.write(phase1_report.read_text(encoding="utf-8"))
        f.write("\n\n---\n\n")
        f.write("## 阶段二优化\n\n")
        f.write(phase2_report.read_text(encoding="utf-8"))
    return final_report


def main() -> None:
    output_dir = ROOT / "simulation_results"
    _reset_output_dir(output_dir)

    print("=== 开始阶段一：基准现状分析 (Data1.3) ===")
    phase1_result = run_phase1(output_dir=output_dir)
    print("=== 阶段一完成。结果已保存。===")

    print("=== 开始阶段二：优化策略研究 (Data1.3) ===")
    phase2_result = run_phase2(output_dir=output_dir)
    print("=== 阶段二完成。正在生成最终汇总... ===")

    final_report = _merge_reports(
        output_dir,
        phase1_result["report_path"],
        phase2_result["report_path"],
    )

    for src, name in [
        (phase2_result["comparison_chart"], "comparison_bar_chart.png"),
        (phase2_result["gantt_chart"], "gantt_chart.png"),
    ]:
        if src.exists():
            shutil.copyfile(src, output_dir / name)

    try:
        os.startfile(output_dir)  # type: ignore[attr-defined]
    except Exception:
        print(f"所有结果已保存至：{output_dir}")


if __name__ == "__main__":
    main()
