# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_loader import load_and_process_data
from src.simulation_engine import JobShop, summarize_results

data_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "native_data", "csv", "Data1.3.csv")
jobs = load_and_process_data(data_file)
print("Loaded %d jobs" % len(jobs))

print("\nPhase 1 Results:")
print("=" * 60)

for strategy in ["FCFS", "EDD", "MinSLK"]:
    shop = JobShop([dict(j) for j in jobs], strategy)
    results = shop.run()
    m = summarize_results(results)
    print("%s -> H: %.2f min, N: %.2f min" % (strategy, m['mean_tardiness_h'], m['mean_tardiness_n']))

print("\nPhase 2 Results:")
print("=" * 60)

for strategy in ["FCFS", "Cost_Based_Composite"]:
    shop = JobShop([dict(j) for j in jobs], strategy)
    results = shop.run()
    m = summarize_results(results)
    print("%s -> H: %.2f min, N: %.2f min" % (strategy, m['mean_tardiness_h'], m['mean_tardiness_n']))
