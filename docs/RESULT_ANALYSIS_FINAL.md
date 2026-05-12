# 正式实验结果分析

## 1. 文档说明
本文档基于 `runner_final` 产生的正式实验结果，对 Whittle 指数策略与 4 种基线策略进行分析。

本文档使用的结果文件为：

- `results/runner_final/summary_aggregated.csv`
- `results/runner_final/scenario_config_table.csv`

对应正式实验配置为：

- 场景数：3
- 仿真时隙：`T = 5000`
- 重复次数：`num_runs = 10`
- 对比策略：
  - `WhittleScheduler`
  - `GreedyScheduler`
  - `RoundRobinScheduler`
  - `PeriodicScheduler`
  - `RandomScheduler`

因此，本文档中的结果可视为当前工程下的正式主实验分析，而不是 smoke 级验证结果。

## 2. 正式实验场景

### 2.1 场景一：`N3_demo_final`
- 类别数：`N = 3`
- 权重：`[1.0, 2.0, 3.0]`
- 采样率：`[0.95, 0.85, 0.75]`
- 链路成功率：`[0.9, 0.8, 0.7]`

### 2.2 场景二：`N5_hetero_final`
- 类别数：`N = 5`
- 权重：`[1.0, 1.5, 2.0, 3.0, 5.0]`
- 采样率：`[0.95, 0.9, 0.85, 0.8, 0.75]`
- 链路成功率：`[0.92, 0.88, 0.84, 0.78, 0.7]`

### 2.3 场景三：`N8_hetero_final`
- 类别数：`N = 8`
- 权重：`[1.0, 1.2, 1.5, 2.0, 2.5, 3.0, 4.0, 6.0]`
- 采样率：`[0.95, 0.93, 0.9, 0.88, 0.85, 0.82, 0.78, 0.75]`
- 链路成功率：`[0.95, 0.92, 0.9, 0.88, 0.85, 0.82, 0.78, 0.72]`

这 3 个场景从低维到中维，逐渐增加系统异构性，足以反映策略在正式主实验中的核心表现。

## 3. 平均加权 AoI 总体结论

### 3.1 `N3_demo_final`
平均加权 AoI 排名如下：

1. `whittle = 18.4102`
2. `greedy = 19.2565`
3. `periodic = 22.6860`
4. `round_robin = 23.4518`
5. `random = 29.3579`

相对 `GreedyScheduler`，Whittle 降低约：

```text
(19.2565 - 18.4102) / 19.2565 ≈ 4.39%
```

### 3.2 `N5_hetero_final`
平均加权 AoI 排名如下：

1. `whittle = 54.4689`
2. `greedy = 57.9476`
3. `round_robin = 75.2887`
4. `periodic = 81.0861`
5. `random = 100.0107`

相对 `GreedyScheduler`，Whittle 降低约：

```text
(57.9476 - 54.4689) / 57.9476 ≈ 6.00%
```

### 3.3 `N8_hetero_final`
平均加权 AoI 排名如下：

1. `whittle = 129.8852`
2. `greedy = 141.0697`
3. `round_robin = 185.1948`
4. `periodic = 221.1160`
5. `random = 261.0463`

相对 `GreedyScheduler`，Whittle 降低约：

```text
(141.0697 - 129.8852) / 141.0697 ≈ 7.93%
```

### 3.4 总体观察
从 `N=3` 到 `N=8`，Whittle 在 3 个正式场景中始终排名第一，且相对 Greedy 的优势并未消失，反而随着场景复杂度上升而扩大：

- `N3`: 约 `4.39%`
- `N5`: 约 `6.00%`
- `N8`: 约 `7.93%`

这说明：

1. Whittle 的优势不是偶然结果
2. 在异构性更强的正式场景中，Whittle 的结构性优势更明显
3. Greedy 虽然是强基线，但在长期平均加权 AoI 目标下仍落后于 Whittle

## 4. 高优先级业务分析

正式实验中的高优先级业务平均 AoI 指标分别为：

### 4.1 `N3_demo_final`
- `greedy = 2.9223`
- `whittle = 2.9552`

此时 Greedy 略优。

### 4.2 `N5_hetero_final`
- `greedy = 4.2200`
- `whittle = 4.2667`

此时 Greedy 仍略优。

### 4.3 `N8_hetero_final`
- `greedy = 6.0330`
- `whittle = 5.9115`

此时 Whittle 反超 Greedy。

### 4.4 如何理解
这一结果很有意义：

1. 在较小规模场景下，Greedy 因为直接追逐当前最大的 `w_i * A_i`，对最高优先级业务更激进
2. 但随着系统规模增加、异构性增强，Whittle 通过显式吸收成功概率与长期平均收益信息，开始在关键业务保障上体现优势
3. 这说明 Whittle 并不是简单地“牺牲关键业务换系统整体性能”，而是在复杂场景下逐步实现了整体性能与关键业务保护的兼顾

因此，正式实验支持这样一个更细致的结论：

- 在小规模场景中，Greedy 对单个关键业务的即时压制可能略强
- 在更复杂的异构场景中，Whittle 开始在关键业务 AoI 上取得更好结果

## 5. 峰值风险分析

正式实验中的系统峰值 AoI 与峰值加权 AoI 结果如下。

### 5.1 系统峰值 AoI
#### `N3_demo_final`
- `whittle = 16.1`
- `greedy = 20.2`
- `round_robin = 30.9`
- `periodic = 26.5`
- `random = 42.2`

#### `N5_hetero_final`
- `whittle = 24.2`
- `greedy = 31.5`
- `round_robin = 49.5`
- `periodic = 48.2`
- `random = 63.3`

#### `N8_hetero_final`
- `whittle = 37.4`
- `greedy = 47.7`
- `round_robin = 67.2`
- `periodic = 81.9`
- `random = 95.8`

可以看到，Whittle 在三个正式场景中都取得了最低的系统峰值 AoI。

### 5.2 峰值加权 AoI
#### `N3_demo_final`
- `whittle = 76.6`
- `greedy = 78.3`

#### `N5_hetero_final`
- `whittle = 172.1`
- `greedy = 183.95`

#### `N8_hetero_final`
- `whittle = 328.44`
- `greedy = 342.44`

Whittle 在峰值加权 AoI 上也 consistently 优于 Greedy。

### 5.3 结论
正式实验表明，Whittle 不仅在平均意义下更优，而且在最坏情况风险控制上也表现更好：

1. 系统峰值 AoI 更低
2. 峰值加权 AoI 更低
3. 在更大、更异构的场景中，这种峰值优势仍然存在

这对于高速铁路监测非常关键，因为峰值 AoI 对应的是“状态长时间未更新”的极端风险。

## 6. 稳定性分析

正式实验中每个结果都基于 `10` 次重复运行，因此可以观察标准差。

### 6.1 平均加权 AoI 标准差
- `N3_demo_final`
  - `whittle_std = 0.2576`
  - `greedy_std = 0.2856`
- `N5_hetero_final`
  - `whittle_std = 0.5551`
  - `greedy_std = 0.4615`
- `N8_hetero_final`
  - `whittle_std = 1.5573`
  - `greedy_std = 1.5792`

### 6.2 结果解读
Whittle 的标准差总体上与 Greedy 同一量级，且在 `N3` 和 `N8` 场景下略优，在 `N5` 场景下略高但差距很小。

这说明：

1. Whittle 的优势不是由极个别随机种子导致
2. 其性能改进具有较好的重复稳定性
3. 在正式实验强度下，Whittle 的结果具备较好的统计可信度

## 7. 不同基线的定位分析

### 7.1 Greedy
Greedy 是当前最强基线。

它的特点是：

1. 平均加权 AoI 始终位居第二
2. 小规模场景下对高优先级业务压制更强
3. 但在峰值风险控制和长期平均目标上仍被 Whittle 超过

### 7.2 Round Robin
Round Robin 的特点是：

1. 简单稳定
2. 公平性较强
3. 但对异构权重和异构链路缺乏适应性

在三个正式场景中，其性能均明显落后于 Whittle 和 Greedy。

### 7.3 Periodic
Periodic 的性能在正式实验中普遍弱于 Round Robin。

这说明当前基于权重构造的周期模式虽然有一定业务倾向性，但仍难以替代基于状态反馈的动态调度。

### 7.4 Random
Random 始终最差，这个结果符合预期，说明系统确实需要结构化调度。

## 8. 正式实验可支撑的核心结论
基于 `runner_final` 的正式结果，可以给出如下较强结论：

1. Whittle 在全部正式主实验场景中都取得了最低的平均加权 AoI
2. 随着系统规模和异构性增加，Whittle 相对 Greedy 的优势进一步扩大
3. Whittle 在系统峰值 AoI 和峰值加权 AoI 上同样最优，说明其具备更好的风险控制能力
4. 在高优先级业务 AoI 上，Whittle 在小规模场景下略逊于 Greedy，但在更复杂异构场景下开始取得优势
5. 因此，Whittle 的优势不仅体现在整体效率上，也体现在复杂场景下的稳健性上

## 9. 适合写入论文的结论段落
下面这段话可以直接作为论文结果分析部分的初稿：

> 正式主实验结果表明，Whittle 指数调度策略在三个代表性场景中均取得最低的平均加权 AoI，并且相对 Greedy 基线的性能增益随着系统规模与异构性增加而扩大。在 `N3_demo_final`、`N5_hetero_final` 与 `N8_hetero_final` 场景中，Whittle 分别相对 Greedy 降低约 `4.39%`、`6.00%` 和 `7.93%` 的平均加权 AoI。同时，Whittle 在系统峰值 AoI 和峰值加权 AoI 两项风险指标上也 consistently 最优，说明该方法不仅改善长期平均信息新鲜度，也能有效抑制极端老化风险。尽管在小规模场景下 Greedy 对最高优先级业务的即时保护略强，但随着系统复杂度提升，Whittle 在关键业务保障方面同样展现出更优表现。整体来看，正式实验结果支持 Whittle 指数策略作为本项目多类 AoI 调度问题的核心方法。

## 10. 后续建议
虽然 `runner_final` 的正式结果已经具备较强说服力，但若要进一步提升论文严谨性，仍建议继续补充：

1. 针对 `N8` 以上规模增加更多正式主实验点
2. 对正式结果补充置信区间或显著性检验
3. 对高优先级业务指标给出更细粒度的单业务曲线图
4. 将正式扩展实验结果跑完后，与本文件一起形成最终论文实验章节

