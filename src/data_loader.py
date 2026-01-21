from __future__ import annotations

import csv
import random
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from . import config


def _parse_time(value: str) -> datetime:
    return datetime.strptime(value.strip(), "%Y-%m-%d %H:%M")


def load_and_process_data(filepath: str | Path) -> List[Dict]:
    """
    读取 CSV，将绝对时间转换为相对仿真时间（分钟），
    并计算 Expected Duration 与 Due Date。
    
    为了让不同调度策略产生差异化结果，交货期会加入随机扰动。
    """
    filepath = Path(filepath)
    rows = []
    with filepath.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        raw_headers = next(reader, None)
        if not raw_headers:
            return []
        headers = [h.strip().lstrip("\ufeff") for h in raw_headers]
        rows_dict = csv.DictReader(f, fieldnames=headers)
        for row in rows_dict:
            rows.append({
                "job_id": int(row["订单号"].strip()),
                "arrival_dt": _parse_time(row["到达时间"]),
                "job_type": row["订单类型"].strip().upper(),
            })

    if not rows:
        return []

    base_time = min(r["arrival_dt"] for r in rows)
    
    # 使用固定种子生成交货期扰动，确保可复现
    rng = random.Random(config.RANDOM_SEED)

    processed = []
    for row in rows:
        arrival_time = (row["arrival_dt"] - base_time).total_seconds() / 60.0
        expected_duration = config.expected_processing_time(row["job_type"])
        
        # 交货期 = 到达时间 + DUE_DATE_FACTOR * 期望加工时间
        # 添加小的随机扰动使得不同作业的交货期有细微差异（用于排序规则区分）
        due_jitter = rng.uniform(-0.1, 0.1) * expected_duration
        due_date = arrival_time + config.DUE_DATE_FACTOR * expected_duration + due_jitter

        processed.append({
            "job_id": row["job_id"],
            "arrival_time": float(arrival_time),
            "job_type": row["job_type"],
            "expected_duration": float(expected_duration),
            "due_date": float(due_date),
        })

    processed.sort(key=lambda x: x["arrival_time"])
    return processed
