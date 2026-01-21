from __future__ import annotations

from dataclasses import dataclass

from . import config


STRATEGY_FCFS = "FCFS"
STRATEGY_EDD = "EDD"
STRATEGY_MINSLK = "MinSLK"
STRATEGY_OPT = "OPT"
STRATEGY_COST_COMPOSITE = "Cost_Based_Composite"


@dataclass
class Scheduler:
    strategy: str

    def decide_machine(self, job: dict, now: float, a_queue_len: int, a_in_service: int,
                       b_queue_len: int, b_in_service: int, next_h_arrival: float | None,
                       h_in_b_system: int) -> str:
        """决定 N 类订单去 A 或 B；H 类必须去 B。"""
        if job["job_type"] == "H":
            return "B"

        # N 类订单
        if self.strategy == STRATEGY_OPT:
            a_load = a_queue_len + a_in_service
            b_load = b_queue_len + b_in_service
            if a_load >= config.A_BUSY_THRESHOLD and b_load == 0:
                if next_h_arrival is None:
                    return "B"
                if (next_h_arrival - now) >= config.B_RESERVATION_WINDOW:
                    return "B"
            return "A"

        if self.strategy == STRATEGY_COST_COMPOSITE:
            # =============================================================
            # 优化策略：A/B 严格分流 (Strict Partitioning with Overflow Protection)
            # =============================================================
            # 核心思想：B 机是 H 类的"专属资源"，N 类几乎不可见
            # 
            # 规则：
            # 1. N 类默认禁止进入 B 机
            # 2. 只有当 A 机严重拥堵（队列 > 10）且 B 机完全空闲且无 H 等待时
            #    才允许 N "捡漏"
            # =============================================================
            a_total_load = a_queue_len + a_in_service
            b_total_load = b_queue_len + b_in_service
            
            # 溢出条件（非常严格）：
            # 1. A 机队列长度 > 10（严重拥堵）
            # 2. B 机完全空闲（无排队、无在制）
            # 3. B 队列中无 H 等待
            # 4. 近期无 H 到达（预留窗口内）
            if a_total_load > 10 and b_total_load == 0 and h_in_b_system == 0:
                if next_h_arrival is None:
                    return "B"  # 后续无 H，可以去 B 捡漏
                if (next_h_arrival - now) >= config.B_RESERVATION_WINDOW:
                    return "B"  # H 还很远，可以去 B 捡漏
            
            # 默认：N 类必须强制去 A 机（即使 A 机很忙）
            return "A"

        # =============================================================
        # FCFS / EDD / MinSLK 基准策略：简单负载均衡（不为 H 预留）
        # =============================================================
        # 基准逻辑：N 类订单根据当前负载选择机器
        # 关键：不考虑 H 的需求，只做简单的负载均衡
        # 这会导致 N 在 A 忙时占用 B，从而阻塞 H
        # =============================================================
        a_load = a_queue_len + a_in_service
        b_load = b_queue_len + b_in_service
        
        # 简单负载均衡：谁的负载低就去谁那里
        # 当 A 负载 >= B 负载时，N 去 B（这会阻塞 H）
        if a_load >= b_load:
            return "B"
        # 否则去 A
        return "A"

    def priority(self, job: dict, machine: str, now: float) -> float:
        """生成 SimPy PriorityResource 的优先级，数值越小优先级越高。"""
        if self.strategy == STRATEGY_FCFS:
            return float(job["arrival_time"])
        if self.strategy == STRATEGY_EDD:
            return float(job["due_date"])
        if self.strategy == STRATEGY_MINSLK:
            slack = job["due_date"] - job["expected_duration"] - now
            return float(slack)

        if self.strategy == STRATEGY_COST_COMPOSITE:
            if machine == "B":
                if job["job_type"] == "H":
                    return float(job["due_date"])
                return 1_000_000.0 + float(job["due_date"])
            slack = job["due_date"] - job["expected_duration"] - now
            return float(slack)

        # 优化策略：B 机对 H 绝对优先（同类内用 EDD）
        if machine == "B":
            base = 0.0 if job["job_type"] == "H" else 1.0
            return base * 1_000_000.0 + float(job["due_date"])
        return float(job["due_date"])


def available_strategies() -> list[str]:
    return [STRATEGY_FCFS, STRATEGY_EDD, STRATEGY_MINSLK, STRATEGY_OPT, STRATEGY_COST_COMPOSITE]
