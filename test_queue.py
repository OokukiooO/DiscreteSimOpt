# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'd:/personal/大四上课件/系统仿真课设/DiscreteSimOpt')

from src.data_loader import load_and_process_data
from src.simulation_engine import JobShop, summarize_results

data_file = 'd:/personal/大四上课件/系统仿真课设/DiscreteSimOpt/native_data/csv/Data1.3.csv'
jobs = load_and_process_data(data_file)

# 追踪队列长度
for strategy in ['FCFS', 'EDD', 'MinSLK', 'Cost_Based_Composite']:
    shop = JobShop([dict(j) for j in jobs], strategy)
    
    max_a_queue = [0]
    max_b_queue = [0]
    
    orig_add_a = shop.a_queue.add
    orig_add_b = shop.b_queue.add
    
    def make_tracker(max_q, q, orig):
        def track_add(job):
            orig(job)
            max_q[0] = max(max_q[0], len(q))
        return track_add
    
    shop.a_queue.add = make_tracker(max_a_queue, shop.a_queue, orig_add_a)
    shop.b_queue.add = make_tracker(max_b_queue, shop.b_queue, orig_add_b)
    
    results = shop.run()
    m = summarize_results(results)
    
    # 统计去各机器的 N 数量
    n_to_a = sum(1 for r in results if r.job_type == 'N' and r.machine == 'A')
    n_to_b = sum(1 for r in results if r.job_type == 'N' and r.machine == 'B')
    
    print('%s:' % strategy)
    print('  H: %.2f min, N: %.2f min' % (m['mean_tardiness_h'], m['mean_tardiness_n']))
    print('  Max A queue: %d, Max B queue: %d' % (max_a_queue[0], max_b_queue[0]))
    print('  N -> A: %d, N -> B: %d' % (n_to_a, n_to_b))
    print()
