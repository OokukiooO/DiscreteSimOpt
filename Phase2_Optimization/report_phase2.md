# 阶段二：优化方法研究与实现（Data1.3）

| 策略 | H 平均拖期 (min) | N 平均拖期 (min) |
|---|---:|---:|
| FCFS | 36.83 | 7.08 |
| MinSLK | 36.83 | 7.08 |
| Cost_Based_Composite | 33.97 | 12.19 |

## 结论
对比基线 FCFS 与 MinSLK，Cost_Based_Composite 通过 H 类优先 + A 机 MinSLK 选单的组合策略，重点保障 H 类订单拖期，同时控制 N 类拖期恶化。
甘特图已保存至：D:\personal\大四上课件\系统仿真课设\sub1_simu_model\Phase2_Optimization\results\gantt_Data1.3_Cost_Based_Composite.png
