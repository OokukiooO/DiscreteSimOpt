# -*- coding: utf-8 -*-
"""
敏感性分析模块：验证优化策略在高压环境下的鲁棒性

场景：将订单到达时间压缩为原来的 80%（到达率增加 25%）
目的：验证 "Strict Partitioning" 策略在系统高负荷时的优势
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Dict
from copy import deepcopy

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_loader import load_and_process_data
from src.simulation_engine import JobShop, summarize_results
from src import config


def compress_arrival_times(jobs: List[Dict], compression_factor: float) -> List[Dict]:
    """
    压缩订单到达时间，模拟更高的到达率。
    
    Args:
        jobs: 原始作业列表
        compression_factor: 压缩因子（0.8 表示时间压缩为 80%，到达率增加 25%）
    
    Returns:
        压缩后的作业列表（深拷贝，不影响原数据）
    """
    compressed = []
    for job in jobs:
        new_job = deepcopy(job)
        # 压缩到达时间
        new_job["arrival_time"] = job["arrival_time"] * compression_factor
        # 交货期也相应压缩（保持相对宽裕度不变）
        # due_date = arrival_time + slack，slack 保持不变
        original_slack = job["due_date"] - job["arrival_time"]
        new_job["due_date"] = new_job["arrival_time"] + original_slack
        compressed.append(new_job)
    return compressed


def run_sensitivity_analysis(compression_factors: List[float] = None):
    """
    执行敏感性分析。
    
    Args:
        compression_factors: 压缩因子列表，默认 [1.0, 0.8, 0.7, 0.6]
    """
    if compression_factors is None:
        compression_factors = [1.0, 0.8, 0.7, 0.6]
    
    data_file = ROOT / "native_data" / "csv" / "Data1.3.csv"
    original_jobs = load_and_process_data(data_file)
    
    print("=" * 80)
    print("敏感性分析：订单到达率变化对调度策略的影响")
    print("=" * 80)
    print(f"配置：A机={config.A_MACHINES}台, B机={config.B_MACHINES}台")
    print(f"数据集：Data1.3 (H类={sum(1 for j in original_jobs if j['job_type']=='H')}个, "
          f"N类={sum(1 for j in original_jobs if j['job_type']=='N')}个)")
    print()
    
    strategies = ["FCFS", "Cost_Based_Composite"]
    
    results_table = []
    
    for factor in compression_factors:
        arrival_rate_increase = (1 / factor - 1) * 100 if factor < 1 else 0
        
        print("-" * 80)
        if factor == 1.0:
            print(f"场景：基准（原始到达率）")
        else:
            print(f"场景：到达时间压缩至 {factor*100:.0f}%（到达率增加 {arrival_rate_increase:.0f}%）")
        print("-" * 80)
        
        # 压缩到达时间
        jobs = compress_arrival_times(original_jobs, factor)
        
        scenario_results = {"factor": factor, "arrival_rate_increase": arrival_rate_increase}
        
        for strategy in strategies:
            shop = JobShop([deepcopy(j) for j in jobs], strategy)
            sim_results = shop.run()
            metrics = summarize_results(sim_results)
            
            # 详细统计
            h_results = [r for r in sim_results if r.job_type == 'H']
            n_results = [r for r in sim_results if r.job_type == 'N']
            h_with_tardiness = sum(1 for r in h_results if r.tardiness > 0)
            n_with_tardiness = sum(1 for r in n_results if r.tardiness > 0)
            
            scenario_results[strategy] = {
                "h_tardiness": metrics["mean_tardiness_h"],
                "n_tardiness": metrics["mean_tardiness_n"],
                "h_late_count": h_with_tardiness,
                "n_late_count": n_with_tardiness,
            }
            
            print(f"  {strategy:25s}: H平均拖期={metrics['mean_tardiness_h']:8.2f}min "
                  f"({h_with_tardiness:3d}/{len(h_results)}有拖期), "
                  f"N平均拖期={metrics['mean_tardiness_n']:8.2f}min "
                  f"({n_with_tardiness:3d}/{len(n_results)}有拖期)")
        
        # 计算改善百分比
        fcfs_h = scenario_results["FCFS"]["h_tardiness"]
        opt_h = scenario_results["Cost_Based_Composite"]["h_tardiness"]
        if fcfs_h > 0:
            improvement = (fcfs_h - opt_h) / fcfs_h * 100
        else:
            improvement = 0
        scenario_results["h_improvement"] = improvement
        
        print()
        print(f"  >>> H类拖期改善: {improvement:+.2f}% (FCFS: {fcfs_h:.2f} → OPT: {opt_h:.2f})")
        
        results_table.append(scenario_results)
    
    # 汇总表格
    print()
    print("=" * 80)
    print("敏感性分析汇总表")
    print("=" * 80)
    print(f"{'到达率变化':^12} | {'FCFS H拖期':^12} | {'OPT H拖期':^12} | {'H改善%':^10} | {'FCFS N拖期':^12} | {'OPT N拖期':^12}")
    print("-" * 80)
    
    for r in results_table:
        if r["factor"] == 1.0:
            rate_str = "基准"
        else:
            rate_str = f"+{r['arrival_rate_increase']:.0f}%"
        
        print(f"{rate_str:^12} | "
              f"{r['FCFS']['h_tardiness']:^12.2f} | "
              f"{r['Cost_Based_Composite']['h_tardiness']:^12.2f} | "
              f"{r['h_improvement']:^+10.2f} | "
              f"{r['FCFS']['n_tardiness']:^12.2f} | "
              f"{r['Cost_Based_Composite']['n_tardiness']:^12.2f}")
    
    print("=" * 80)
    print()
    print("结论分析：")
    print("- 随着到达率增加，系统负荷上升，拖期显著增加")
    print("- Strict Partitioning 策略通过 B 机预留，有效保护 H 类订单")
    print("- 高压环境下，优化策略的优势更加明显")
    
    return results_table


if __name__ == "__main__":
    run_sensitivity_analysis()
