# 仿真结果汇总

| 数据集 | 策略 | H 平均拖期 (min) | N 平均拖期 (min) |
|---|---|---:|---:|
| Data1.1 | FCFS | 2042.84 | 152.84 |
| Data1.1 | EDD | 2042.84 | 152.84 |
| Data1.1 | MinSLK | 1915.45 | 178.78 |
| Data1.3 | FCFS | 36.83 | 7.08 |
| Data1.3 | EDD | 36.83 | 7.08 |
| Data1.3 | MinSLK | 36.83 | 7.08 |

**最佳策略**：FCFS（基于 H 平均拖期最小）

甘特图已保存至：D:\personal\大四上课件\系统仿真课设\sub1_simu_model\simulation_results\gantt_Data1.3_FCFS.png

## MinSLK 分析
MinSLK 使用优先级 $DueDate - ExpectedProcessingTime - CurrentTime$，对剩余裕量最小的订单优先处理。

高负载样本：Data1.1
- FCFS：H 平均拖期 2042.84，N 平均拖期 152.84
- EDD：H 平均拖期 2042.84，N 平均拖期 152.84
- MinSLK：H 平均拖期 1915.45，N 平均拖期 178.78
