from __future__ import annotations

# 全局配置参数（可根据课题设定调整）

# 机器数量
A_MACHINES = 3  # 慢机，仅加工 N
B_MACHINES = 2  # 快机，加工 H（必须）及 N（可选）

# 三角分布参数 [a, c, b] = (min, mode, max)，单位：分钟
# H on B
TRIANGULAR_B_H = (300, 400, 800)
# N on B
TRIANGULAR_B_N = (200, 280, 600)
# N on A
TRIANGULAR_A_N = (360, 480, 840)

# 优化策略参数
# 仅当 A 机“很忙”且 B 机未来一段时间无 H 到达时，N 才可去 B
A_BUSY_THRESHOLD = 4  # A 队列长度阈值（含在制）
B_RESERVATION_WINDOW = 60.0  # 预留窗口（分钟）

# 统一随机种子（保证可复现）
RANDOM_SEED = 42

# 调度规则名称（阶段一）
STRATEGY_MINSLK = "MinSLK"


def expected_triangular(a: float, c: float, b: float) -> float:
    """三角分布期望值 E = (a + b + c) / 3。"""
    return (a + b + c) / 3.0


def expected_processing_time(job_type: str) -> float:
    """用于交货期计算的期望加工时间。"""
    if job_type.upper() == "H":
        a, c, b = TRIANGULAR_B_H
    else:
        a, c, b = TRIANGULAR_A_N
    return expected_triangular(a, c, b)
