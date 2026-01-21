# -*- coding: utf-8 -*-
"""深度分析 B 机队列情况"""
import sys
sys.path.insert(0, 'd:/personal/大四上课件/系统仿真课设/DiscreteSimOpt')

from src.data_loader import load_and_process_data
from src.simulation_engine import JobShop, summarize_results

data_file = 'd:/personal/大四上课件/系统仿真课设/DiscreteSimOpt/native_data/csv/Data1.3.csv'
jobs = load_and_process_data(data_file)

print("="*70)
print("深度分析：B 机队列等待情况")
print("="*70)

for strategy in ['FCFS', 'Cost_Based_Composite']:
    shop = JobShop([dict(j) for j in jobs], strategy)
    
    # 记录每次 B 机队列的 H 数量
    h_queue_lengths = []
    n_in_b_count = [0]
    
    orig_add_b = shop.b_queue.add
    def make_tracker(q, h_lengths, n_count, orig):
        def track_add(job):
            orig(job)
            h_count = sum(1 for j in q.peek_jobs() if j['job_type'] == 'H')
            h_lengths.append(h_count)
            if job['job_type'] == 'N':
                n_count[0] += 1
        return track_add
    
    shop.b_queue.add = make_tracker(shop.b_queue, h_queue_lengths, n_in_b_count, orig_add_b)
    
    results = shop.run()
    m = summarize_results(results)
    
    # 分析 H 的等待时间
    h_results = [r for r in results if r.job_type == 'H']
    h_wait_times = [r.start_time - r.arrival_time for r in h_results]
    h_tardiness = [r.tardiness for r in h_results]
    
    print("\n%s:" % strategy)
    print("  H 平均拖期: %.2f min" % m['mean_tardiness_h'])
    print("  H 平均等待时间: %.2f min" % (sum(h_wait_times)/len(h_wait_times) if h_wait_times else 0))
    print("  H 最大等待时间: %.2f min" % (max(h_wait_times) if h_wait_times else 0))
    print("  有拖期的 H 数量: %d / %d" % (sum(1 for t in h_tardiness if t > 0), len(h_tardiness)))
    print("  N 进入 B 机数量: %d" % n_in_b_count[0])
    if h_queue_lengths:
        print("  B 队列中 H 的平均数量: %.2f" % (sum(h_queue_lengths)/len(h_queue_lengths)))
        print("  B 队列中 H 的最大数量: %d" % max(h_queue_lengths))

print("\n" + "="*70)
print("结论分析")
print("="*70)
