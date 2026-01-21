from __future__ import annotations

# 全局配置参数（严格按照题目要求，不可随意修改）

# 机器数量（题目规定）
A_MACHINES = 3  # A型机（慢机），仅加工 N 类订单
B_MACHINES = 2  # B型机（快机），加工 H 类（必须）及 N 类（可选）

# 三角分布参数 [a, c, b] = (min, mode, max)，单位：分钟（题目规定）
# H on B
TRIANGULAR_B_H = (300, 400, 800)
# N on B
TRIANGULAR_B_N = (200, 280, 600)
# N on A
TRIANGULAR_A_N = (360, 480, 840)

# 优化策略参数
A_BUSY_THRESHOLD = 5  # A 队列长度阈值（每台 A 机后排 5 个以上视为堵死）
B_RESERVATION_WINDOW = 200.0  # 预留窗口（分钟）
A_QUEUE_STRICT_LIMIT = 15  # A 队列总长度严格限制（3台 * 5 = 15）

# 交货期设置（与期望加工时间相关）
DUE_DATE_FACTOR = 1.5  # 交货期 = 到达时间 + 1.5 * 期望加工时间

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
