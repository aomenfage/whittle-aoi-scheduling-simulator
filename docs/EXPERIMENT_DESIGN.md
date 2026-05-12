# 实验方案说明

## 1. 实验目标
当前工程中的实验分为两大类：

1. 标准主实验
2. 扩展敏感性实验

实验目标包括：

- 比较 Whittle 与多个基线策略的整体性能
- 验证单类子问题的阈值结构
- 检验 Whittle 在规模扩展、权重变化、链路异构和峰值 AoI 场景下的鲁棒性
- 统计运行复杂度，支撑工程可实现性

## 2. 对比算法
当前统一对比的在线调度算法包括：

1. `WhittleScheduler`
2. `RoundRobinScheduler`
3. `PeriodicScheduler`
4. `GreedyScheduler`
5. `RandomScheduler`

各算法已通过统一接口 `SchedulerBase` 接入，因此可在同一实验框架下公平比较。

## 3. 标准主实验
标准主实验入口为：

- `runner.py --suite standard`

默认配置文件：

- `config/runner_default.json`

### 3.1 标准主实验参数
主实验中每个场景至少包含：

- 监控量类别数 `N`
- 权重向量 `w`
- 链路成功概率向量 `p`
- 采样成功概率向量 `sampling_rates`
- 仿真时隙数 `T`
- 重复次数 `num_runs`

### 3.2 标准主实验输出
主实验输出包括：

1. `run_metrics.csv`
2. `summary_aggregated.csv`
3. 场景配置表
4. 平均加权 AoI 对比图
5. 高优先级业务平均 AoI 对比图
6. 各类业务平均 AoI 图

### 3.3 主实验核心指标
主实验建议优先报告：

1. `average_weighted_aoi_mean`
2. `high_weight_avg_aoi_mean`
3. `average_weighted_aoi_std`
4. `high_weight_avg_aoi_std`

如果篇幅允许，也可以补充：

- `system_peak_aoi_mean`
- `peak_weighted_aoi_mean`

## 4. 扩展实验总览
扩展实验总入口为：

- `runner.py --suite extended`

当前包含 4 组实验：

1. 规模扩展实验
2. 权重敏感性实验
3. 链路异构性实验
4. 峰值 AoI 实验

## 5. 规模扩展实验
实验脚本：

- `experiments/exp_scalability.py`

### 5.1 实验目的
验证所提 Whittle 策略在监控量数量增大时是否仍具有性能优势和可接受复杂度。

### 5.2 实验设置
当前默认测试：

```text
N = 5, 10, 20, 50
```

每个 `N` 对应一组异构权重、采样率和信道成功率。

### 5.3 输出指标
主要关注：

1. 平均加权 AoI
2. 平均决策时间
3. 总运行时间

### 5.4 输出文件
典型输出包括：

- `summary_with_N.csv`
- `avg_weighted_aoi_vs_N.png`
- `decision_time_vs_N.png`
- `runtime_vs_N.png`

### 5.5 建议结论角度
建议在论文中强调：

- 性能是否随规模增长而平稳退化
- Whittle 是否仍优于基线
- 决策时间是否仍满足在线调度要求

## 6. 权重敏感性实验
实验脚本：

- `experiments/exp_weight_sensitivity.py`

### 6.1 实验目的
验证在高优先级业务权重提升时，Whittle 是否能更好地保护关键业务。

### 6.2 实验设置
当前默认将最后一个 source 视为高优先级业务，并逐步提高其权重，例如：

```text
high_priority_weight = 2, 4, 6, 8, 10
```

### 6.3 输出指标
建议重点报告：

1. 高优先级业务平均 AoI
2. 平均加权 AoI

### 6.4 输出文件
包括：

- `summary_with_weight.csv`
- `high_priority_aoi_vs_weight.png`
- `avg_weighted_aoi_vs_weight.png`

### 6.5 建议结论角度
建议强调：

- 高优先级业务是否被有效保护
- Whittle 相比 Greedy 是否更稳定
- 权重极端不均衡时系统整体性能如何变化

## 7. 链路异构性实验
实验脚本：

- `experiments/exp_channel_sensitivity.py`

### 7.1 实验目的
验证不同链路异构程度下，Whittle 是否能有效利用源间传输可靠性差异。

### 7.2 实验设置
当前默认配置：

1. `uniform`
2. `mild_hetero`
3. `strong_hetero`

即从均匀链路逐渐过渡到强异构链路。

### 7.3 输出指标
建议重点报告：

1. 平均加权 AoI
2. 高优先级业务平均 AoI

### 7.4 输出文件
包括：

- `avg_weighted_aoi_by_channel_profile.png`
- `high_priority_aoi_by_channel_profile.png`

### 7.5 建议结论角度
建议强调：

- 链路差异变大时是否所有策略都明显退化
- Whittle 是否仍保持相对优势
- 该优势是否来源于其显式利用源间成功概率差异

## 8. 峰值 AoI 实验
实验脚本：

- `experiments/exp_peak_aoi.py`

### 8.1 实验目的
验证 Whittle 在极端老化场景下是否能更好地抑制最坏情况 AoI。

### 8.2 实验设置
当前默认包含：

1. `baseline`
2. `poor_links`
3. `extreme_aging`

通过降低采样率和链路成功率构造更恶劣场景。

### 8.3 输出指标
重点报告：

1. `system_peak_aoi`
2. `peak_weighted_aoi`

### 8.4 输出文件
包括：

- `system_peak_aoi_by_scenario.png`
- `peak_weighted_aoi_by_scenario.png`

### 8.5 建议结论角度
建议突出：

- Whittle 是否不仅优化平均性能，也改善最坏情况
- 峰值指标是否能反映高铁监测中“极端过期信息”风险

## 9. 复杂度统计方案
复杂度统计在 `experiments/experiment_utils.py` 中通过 `TimedSchedulerWrapper` 完成。

### 9.1 记录方式
每个时隙都记录一次调度器 `select_action()` 调用耗时：

```text
decision_time_t = end_time - start_time
```

### 9.2 输出指标
实验中统一报告：

1. `avg_decision_time_ms`
2. `total_runtime_s`

### 9.3 论文建议
建议在论文中把复杂度结果放在扩展实验或附录中，用于说明：

- Whittle 的计算开销高于简单基线
- 但仍在可接受在线范围内

## 10. 复现入口
当前工程建议使用以下命令复现实验：

### 10.1 标准主实验
```bash
python runner.py --suite standard --config config/runner_default.json
```

### 10.2 扩展实验
```bash
python runner.py --suite extended
```

### 10.3 一键复现全部核心内容
```bash
python run_all.py --config config/run_all_default.json
```

### 10.4 轻量烟雾验证
```bash
python run_all.py --config config/run_all_smoke.json
```

## 11. 图表与表格命名建议
推荐命名规范见：

- `docs/RESULT_NAMING.md`

建议论文写作时统一采用：

- 图：`fig_<experiment>_<metric>_<variant>.png`
- 表：`table_<experiment>_<content>.csv`

这样便于：

1. 在论文正文中直接引用
2. 自动整理结果目录
3. 避免不同实验输出文件重名

## 12. 论文写作建议
可按以下顺序组织论文实验部分：

1. 先给出主实验，对比 Whittle 与基线的整体性能
2. 再给出单类 MDP 和阈值结构验证，说明方法基础
3. 然后给出扩展实验，说明方法的鲁棒性和可扩展性
4. 最后给出复杂度结果，说明工程可实现性

其中：

- 主指标建议为平均加权 AoI
- 关键业务保护建议用高优先级业务平均 AoI
- 风险控制建议用系统峰值 AoI

