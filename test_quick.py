# -*- coding: utf-8 -*-
"""快速测试脚本"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.data_loader import load_and_process_data
from src.simulation_engine import JobShop, summarize_results
import src.simulation_engine as sim_eng
from src import config

def main():
    data_file = ROOT / "native_data" / "csv" / "Data1.3.csv"
    jobs = load_and_process_data(data_file)
    print(f"Loaded {len(jobs)} jobs (H: {sum(1 for j in jobs if j['job_type']=='H')}, N: {sum(1 for j in jobs if j['job_type']=='N')})")
    print(f"Config: A_MACHINES={config.A_MACHINES}, B_MACHINES={config.B_MACHINES}")
    
    sim_eng.DEBUG_QUEUE = False
    
    # 追踪 B 机队列长度
    max_b_queue = [0]
    b_queue_samples = []
    
    shop = JobShop([dict(j) for j in jobs], "FCFS")
    orig_add = shop.b_queue.add
    def track_add(job):
        orig_add(job)
        qlen = len(shop.b_queue)
        max_b_queue[0] = max(max_b_queue[0], qlen)
        if len(b_queue_samples) < 100:
            b_queue_samples.append(qlen)
    shop.b_queue.add = track_add
    
    results = shop.run()
    
    print(f"\nB Queue Analysis:")
    print(f"  Max queue length: {max_b_queue[0]}")
    print(f"  Queue samples (first 100 additions): {b_queue_samples[:20]}...")
    
    # 如果 B 队列很短，说明 H 到达后很快就被处理
    avg_queue = sum(b_queue_samples) / len(b_queue_samples) if b_queue_samples else 0
    print(f"  Avg queue length at addition time: {avg_queue:.2f}")
    
    print("\n" + "="*70)
    print("Phase 1 Results:")
    print("="*70)
    
    for strategy in ["FCFS", "EDD", "MinSLK"]:
        shop = JobShop([dict(j) for j in jobs], strategy)
        results = shop.run()
        m = summarize_results(results)
        print(f"{strategy:10s} -> H: {m['mean_tardiness_h']:8.2f} min, N: {m['mean_tardiness_n']:8.2f} min")
    
    print("\n" + "="*70)
    print("Phase 2 Results:")
    print("="*70)
    
    for strategy in ["FCFS", "Cost_Based_Composite"]:
        shop = JobShop([dict(j) for j in jobs], strategy)
        results = shop.run()
        m = summarize_results(results)
        print(f"{strategy:25s} -> H: {m['mean_tardiness_h']:8.2f} min, N: {m['mean_tardiness_n']:8.2f} min")

if __name__ == "__main__":
    main()
