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
            # 优化策略：严格的 A 机优先 / B 机锁死 (Strict Reservation)
            # =============================================================
            # 核心思想：B 机对于 N 类订单"几乎不可见"
            # 只有当 A 机全部彻底堵死时，才允许 N 去 B
            # =============================================================
            a_total_load = a_queue_len + a_in_service
            b_total_load = b_queue_len + b_in_service
            
            # 严格条件：A 机队列总长度 >= 15（即每台 A 机平均排 5 个以上）
            # 且 B 机完全空闲（无排队、无在制）
            # 且 B 队列中无 H 等待
            if (a_total_load >= config.A_QUEUE_STRICT_LIMIT and 
                b_total_load == 0 and 
                h_in_b_system == 0):
                # 额外检查：近期是否有 H 到达
                if next_h_arrival is None:
                    return "B"  # 后续无 H，可以去 B
                if (next_h_arrival - now) >= config.B_RESERVATION_WINDOW:
                    return "B"  # H 还很远，可以去 B
            # 默认：N 类必须去 A 机
            return "A"

        # =============================================================
        # FCFS / EDD / MinSLK 基准策略：正常负载均衡
        # =============================================================
        # N 类订单选择"预期完成时间最早"的机器
        # 简化实现：谁空闲去谁，都空闲优先去 A（因为 A 是 N 的默认机器）
        # =============================================================
        a_load = a_queue_len + a_in_service
        b_load = b_queue_len + b_in_service
        
        # 如果 B 机完全空闲且 A 机有负载，N 可以去 B（正常负载均衡）
        if b_load == 0 and a_load > 0:
            return "B"
        # 否则去 A 机
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
