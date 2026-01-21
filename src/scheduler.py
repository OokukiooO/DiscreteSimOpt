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
            a_load = a_queue_len + a_in_service
            b_load = b_queue_len + b_in_service
            if h_in_b_system > 0:
                return "A"
            if a_load > 5 and b_load == 0:
                return "B"
            return "A"

        # FCFS / EDD：选择相对更空闲的机器
        a_score = (a_queue_len + a_in_service) / max(1, config.A_MACHINES)
        b_score = (b_queue_len + b_in_service) / max(1, config.B_MACHINES)
        return "A" if a_score <= b_score else "B"

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
