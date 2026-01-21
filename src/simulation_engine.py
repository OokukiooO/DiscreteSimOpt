from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Dict, Optional

from . import config
from .scheduler import Scheduler, STRATEGY_FCFS, STRATEGY_EDD, STRATEGY_MINSLK, STRATEGY_COST_COMPOSITE

# 调试开关：设为 True 打印队列排序信息
DEBUG_QUEUE = False


@dataclass
class SimulationResult:
    job_id: int
    job_type: str
    arrival_time: float
    start_time: float
    end_time: float
    due_date: float
    tardiness: float
    machine: str


class ManualQueue:
    """手动管理的作业队列，支持按策略显式排序。"""
    def __init__(self, name: str):
        self.name = name
        self._queue: List[Dict] = []
    
    def add(self, job: Dict):
        self._queue.append(job)
    
    def is_empty(self) -> bool:
        return len(self._queue) == 0
    
    def __len__(self) -> int:
        return len(self._queue)
    
    def sort_and_pop(self, strategy: str, now: float, machine: str) -> Optional[Dict]:
        """根据策略排序队列并弹出最高优先级的作业。"""
        if not self._queue:
            return None
        
        # 对于 B 机 + Cost_Based_Composite：H 类绝对优先
        if machine == "B" and strategy == STRATEGY_COST_COMPOSITE:
            h_jobs = [j for j in self._queue if j["job_type"] == "H"]
            n_jobs = [j for j in self._queue if j["job_type"] == "N"]
            if h_jobs:
                # H 类按 EDD 排序
                h_jobs.sort(key=lambda x: x["due_date"])
                selected = h_jobs[0]
            elif n_jobs:
                # N 类按 MinSLK 排序
                n_jobs.sort(key=lambda x: x["due_date"] - x["expected_duration"] - now)
                selected = n_jobs[0]
            else:
                return None
            self._queue.remove(selected)
            if DEBUG_QUEUE:
                top3 = [j["job_id"] for j in (h_jobs if h_jobs else n_jobs)[:3]]
                print(f"[DEBUG] {self.name} Strategy: {strategy}, Queue Top 3 IDs: {top3}, Selected: {selected['job_id']}")
            return selected
        
        # 通用排序逻辑
        if strategy == STRATEGY_FCFS:
            self._queue.sort(key=lambda x: x["arrival_time"])
        elif strategy == STRATEGY_EDD:
            self._queue.sort(key=lambda x: x["due_date"])
        elif strategy == STRATEGY_MINSLK:
            self._queue.sort(key=lambda x: x["due_date"] - x["expected_duration"] - now)
        elif strategy == STRATEGY_COST_COMPOSITE:
            # A 机使用 MinSLK
            self._queue.sort(key=lambda x: x["due_date"] - x["expected_duration"] - now)
        else:
            # OPT 等其他策略默认 EDD
            self._queue.sort(key=lambda x: x["due_date"])
        
        if DEBUG_QUEUE:
            top3 = [j["job_id"] for j in self._queue[:3]]
            print(f"[DEBUG] {self.name} Strategy: {strategy}, Queue Top 3 IDs: {top3}")
        
        return self._queue.pop(0)
    
    def peek_jobs(self) -> List[Dict]:
        """查看队列中的所有作业（不修改）。"""
        return list(self._queue)


class JobShop:
    """使用手动队列管理的作业车间仿真。"""
    
    def __init__(self, jobs: List[Dict], strategy: str):
        self.jobs = sorted(jobs, key=lambda x: x["arrival_time"])
        self.strategy = strategy
        self.scheduler = Scheduler(strategy=strategy)
        
        # 机器状态：每台机器的剩余加工时间（0 表示空闲）
        self.a_machines_busy_until: List[float] = [0.0] * config.A_MACHINES
        self.b_machines_busy_until: List[float] = [0.0] * config.B_MACHINES
        
        # 手动管理的队列
        self.a_queue = ManualQueue("A_Queue")
        self.b_queue = ManualQueue("B_Queue")
        
        # 结果
        self.results: List[SimulationResult] = []
        
        # 预计算所有 H 类到达时间
        self.h_arrivals = sorted([j["arrival_time"] for j in self.jobs if j["job_type"] == "H"])
        
        # 当前 B 机系统中的 H 数量（队列 + 在制）
        self.h_in_b_system = 0

    def _next_h_arrival(self, now: float) -> Optional[float]:
        """获取下一个 H 类订单的到达时间。"""
        for t in self.h_arrivals:
            if t > now:
                return t
        return None

    def _sample_process_time(self, job: Dict, machine: str) -> float:
        """采样加工时间。使用作业 ID 作为随机种子，确保同一作业在不同策略下加工时间一致。"""
        job_type = job["job_type"]
        job_id = job["job_id"]
        
        if machine == "A":
            a, c, b = config.TRIANGULAR_A_N
        else:
            if job_type == "H":
                a, c, b = config.TRIANGULAR_B_H
            else:
                a, c, b = config.TRIANGULAR_B_N
        
        # 使用作业 ID 和机器类型生成确定性随机数
        rng = random.Random(config.RANDOM_SEED + job_id * 1000 + (0 if machine == "A" else 1))
        return rng.triangular(a, b, c)

    def _get_idle_machine(self, machine_type: str, now: float) -> Optional[int]:
        """获取一台空闲机器的索引，如果没有空闲返回 None。"""
        busy_list = self.a_machines_busy_until if machine_type == "A" else self.b_machines_busy_until
        for i, busy_until in enumerate(busy_list):
            if busy_until <= now:
                return i
        return None

    def _count_in_service(self, machine_type: str, now: float) -> int:
        """统计正在加工的机器数量。"""
        busy_list = self.a_machines_busy_until if machine_type == "A" else self.b_machines_busy_until
        return sum(1 for t in busy_list if t > now)

    def _should_b_wait_for_h(self, now: float) -> bool:
        """判断 B 机是否应该空闲等待 H 类订单（前瞻预留）。"""
        if self.strategy != STRATEGY_COST_COMPOSITE:
            return False
        
        next_h = self._next_h_arrival(now)
        if next_h is None:
            return False  # 没有未来 H 到达，B 机可以处理 N
        
        time_until_h = next_h - now
        # 如果 H 将在预留窗口内到达，B 机应该等待
        if time_until_h <= config.B_RESERVATION_WINDOW:
            return True
        
        return False

    def _dispatch_job(self, job: Dict, now: float):
        """决定作业去哪个队列。"""
        next_h = self._next_h_arrival(now)
        a_queue_len = len(self.a_queue)
        b_queue_len = len(self.b_queue)
        a_in_service = self._count_in_service("A", now)
        b_in_service = self._count_in_service("B", now)
        
        machine = self.scheduler.decide_machine(
            job=job,
            now=now,
            a_queue_len=a_queue_len,
            a_in_service=a_in_service,
            b_queue_len=b_queue_len,
            b_in_service=b_in_service,
            next_h_arrival=next_h,
            h_in_b_system=self.h_in_b_system,
        )
        
        if machine == "A":
            self.a_queue.add(job)
        else:
            self.b_queue.add(job)
            if job["job_type"] == "H":
                self.h_in_b_system += 1

    def _try_start_jobs(self, now: float):
        """尝试在空闲机器上启动作业。"""
        # 处理 A 机队列
        while True:
            idle_a = self._get_idle_machine("A", now)
            if idle_a is None or self.a_queue.is_empty():
                break
            job = self.a_queue.sort_and_pop(self.strategy, now, "A")
            if job:
                duration = self._sample_process_time(job, "A")
                end_time = now + duration
                self.a_machines_busy_until[idle_a] = end_time
                tardiness = max(0.0, end_time - job["due_date"])
                self.results.append(SimulationResult(
                    job_id=job["job_id"],
                    job_type=job["job_type"],
                    arrival_time=job["arrival_time"],
                    start_time=now,
                    end_time=end_time,
                    due_date=job["due_date"],
                    tardiness=tardiness,
                    machine="A",
                ))
        
        # 处理 B 机队列
        while True:
            idle_b = self._get_idle_machine("B", now)
            if idle_b is None or self.b_queue.is_empty():
                break
            
            # 前瞻预留：检查是否应该等待 H
            b_has_h = any(j["job_type"] == "H" for j in self.b_queue.peek_jobs())
            if not b_has_h and self._should_b_wait_for_h(now):
                # B 机队列只有 N，但 H 即将到达，保持空闲
                break
            
            job = self.b_queue.sort_and_pop(self.strategy, now, "B")
            if job:
                if job["job_type"] == "H":
                    self.h_in_b_system -= 1
                duration = self._sample_process_time(job, "B")
                end_time = now + duration
                self.b_machines_busy_until[idle_b] = end_time
                tardiness = max(0.0, end_time - job["due_date"])
                self.results.append(SimulationResult(
                    job_id=job["job_id"],
                    job_type=job["job_type"],
                    arrival_time=job["arrival_time"],
                    start_time=now,
                    end_time=end_time,
                    due_date=job["due_date"],
                    tardiness=tardiness,
                    machine="B",
                ))

    def run(self) -> List[SimulationResult]:
        """运行仿真。"""
        random.seed(config.RANDOM_SEED)
        
        job_idx = 0
        n_jobs = len(self.jobs)
        now = 0.0
        
        # 事件驱动循环
        while True:
            # 处理当前时刻的到达
            while job_idx < n_jobs and self.jobs[job_idx]["arrival_time"] <= now:
                self._dispatch_job(self.jobs[job_idx], now)
                job_idx += 1
            
            # 尝试启动作业
            self._try_start_jobs(now)
            
            # 计算下一个事件时间
            next_arrival = self.jobs[job_idx]["arrival_time"] if job_idx < n_jobs else float('inf')
            
            # 下一个机器完成时间（只考虑 > now 的）
            next_machine_free = float('inf')
            for t in self.a_machines_busy_until + self.b_machines_busy_until:
                if t > now:
                    next_machine_free = min(next_machine_free, t)
            
            next_event = min(next_arrival, next_machine_free)
            
            # 检查是否还有未处理的作业
            queues_empty = self.a_queue.is_empty() and self.b_queue.is_empty()
            all_done = len(self.results) >= n_jobs
            
            if next_event == float('inf'):
                if queues_empty or all_done:
                    break
                # 队列非空但没有未来事件，说明有机器空闲，再试一次
                # 找到最近的机器空闲时间
                min_busy = min(self.a_machines_busy_until + self.b_machines_busy_until)
                if min_busy <= now:
                    # 机器已经空闲，但 _try_start_jobs 没处理（可能因为预留逻辑）
                    # 等待下一个到达事件
                    if next_arrival < float('inf'):
                        now = next_arrival
                        continue
                    else:
                        # 没有更多到达，强制处理剩余队列
                        self._force_process_remaining(now)
                        break
                else:
                    now = min_busy
                    continue
            
            now = next_event
        
        return self.results
    
    def _force_process_remaining(self, now: float):
        """强制处理队列中剩余的作业（用于仿真结束时）。"""
        # 处理 A 机队列
        while not self.a_queue.is_empty():
            idle_a = self._get_idle_machine("A", now)
            if idle_a is None:
                # 找到最早空闲的机器
                now = min(self.a_machines_busy_until)
                idle_a = self._get_idle_machine("A", now)
            
            job = self.a_queue.sort_and_pop(self.strategy, now, "A")
            if job:
                duration = self._sample_process_time(job, "A")
                end_time = now + duration
                self.a_machines_busy_until[idle_a] = end_time
                tardiness = max(0.0, end_time - job["due_date"])
                self.results.append(SimulationResult(
                    job_id=job["job_id"],
                    job_type=job["job_type"],
                    arrival_time=job["arrival_time"],
                    start_time=now,
                    end_time=end_time,
                    due_date=job["due_date"],
                    tardiness=tardiness,
                    machine="A",
                ))
                now = end_time
        
        # 处理 B 机队列（忽略预留逻辑）
        while not self.b_queue.is_empty():
            idle_b = self._get_idle_machine("B", now)
            if idle_b is None:
                now = min(self.b_machines_busy_until)
                idle_b = self._get_idle_machine("B", now)
            
            job = self.b_queue.sort_and_pop(self.strategy, now, "B")
            if job:
                if job["job_type"] == "H":
                    self.h_in_b_system -= 1
                duration = self._sample_process_time(job, "B")
                end_time = now + duration
                self.b_machines_busy_until[idle_b] = end_time
                tardiness = max(0.0, end_time - job["due_date"])
                self.results.append(SimulationResult(
                    job_id=job["job_id"],
                    job_type=job["job_type"],
                    arrival_time=job["arrival_time"],
                    start_time=now,
                    end_time=end_time,
                    due_date=job["due_date"],
                    tardiness=tardiness,
                    machine="B",
                ))
                now = end_time


def summarize_results(results: List[SimulationResult]) -> Dict[str, float]:
    h_tardiness = [r.tardiness for r in results if r.job_type == "H"]
    n_tardiness = [r.tardiness for r in results if r.job_type == "N"]
    h_mean = sum(h_tardiness) / max(1, len(h_tardiness))
    n_mean = sum(n_tardiness) / max(1, len(n_tardiness))
    return {
        "mean_tardiness_h": h_mean,
        "mean_tardiness_n": n_mean,
    }
