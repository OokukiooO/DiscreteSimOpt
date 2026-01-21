# src 目录说明

- config.py：全局参数（机器数量、三角分布参数、交货期系数、策略参数）。
- data_loader.py：读取 CSV、转换相对时间、计算期望加工时间与交货期。
- scheduler.py：调度策略选择器（FCFS、EDD、优化策略）。
- simulation_engine.py：封装 SimPy 事件仿真、JobShop 与统计汇总。
- visualizer.py：生成对比柱状图、甘特图、导出 CSV。
