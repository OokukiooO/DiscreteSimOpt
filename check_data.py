"""检查数据排序"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.data_loader import load_and_process_data

jobs = load_and_process_data(ROOT / "native_data/csv/Data1.3.csv")
h_jobs = [j for j in jobs if j["job_type"] == "H"][:20]

print("H jobs - checking if arrival order == due date order:")
print("-" * 60)

# 按到达时间排序
by_arrival = sorted(h_jobs, key=lambda x: x["arrival_time"])
# 按交货期排序  
by_due = sorted(h_jobs, key=lambda x: x["due_date"])
# 按 slack 排序 (due - expected - now)，假设 now=0
by_slack = sorted(h_jobs, key=lambda x: x["due_date"] - x["expected_duration"])

print("By Arrival Time:")
for j in by_arrival[:10]:
    print(f"  ID={j['job_id']:3d}, arr={j['arrival_time']:8.0f}, due={j['due_date']:8.0f}, slack={j['due_date']-j['expected_duration']:8.0f}")

print("\nBy Due Date:")
for j in by_due[:10]:
    print(f"  ID={j['job_id']:3d}, arr={j['arrival_time']:8.0f}, due={j['due_date']:8.0f}, slack={j['due_date']-j['expected_duration']:8.0f}")

print("\nBy Slack:")
for j in by_slack[:10]:
    print(f"  ID={j['job_id']:3d}, arr={j['arrival_time']:8.0f}, due={j['due_date']:8.0f}, slack={j['due_date']-j['expected_duration']:8.0f}")

# 检查顺序是否相同
arrival_order = [j['job_id'] for j in by_arrival]
due_order = [j['job_id'] for j in by_due]
slack_order = [j['job_id'] for j in by_slack]

print(f"\nOrders are identical: arrival==due: {arrival_order == due_order}, arrival==slack: {arrival_order == slack_order}")
