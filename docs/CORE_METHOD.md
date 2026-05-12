# 核心方法说明

## 1. 问题背景

本项目研究高速铁路移动边缘监测系统中的状态更新调度问题。系统目标不是最小化传输时延，而是最小化加权信息年龄（Weighted AoI）。

当前建模假设如下：

1. 单台移动边缘节点
2. 多类监控量
3. 单跳状态更新
4. 离散时隙系统
5. 每个时隙最多调度一个监控量

在该场景中，系统既要保证整体信息新鲜度，也要优先保护高权重、关键业务。

## 2. 基础 AoI 仿真模型

环境层实现位于：

- `env/source.py`
- `env/channel.py`
- `env/aoi_env.py`

### 2.1 状态定义

对每个监控量 `i`，用 `A_i(t)` 表示时隙 `t` 的 AoI。

若当前时隙调度 source `i`：

- 当采样成功且传输成功时，AoI 重置为 `1`
- 否则 AoI 增加 `1`

未被调度的其他源 AoI 同样增加 `1`

### 2.2 状态转移

当前工程采用如下离散时隙转移规则：

```Markdown
若 source i 在时隙 t 被调度且更新成功：
    A_i(t+1) = 1
否则：
    A_i(t+1) = A_i(t) + 1
```

对应实现见 `AoIEnv.step()`。

### 2.3 系统目标函数

系统的即时加权 AoI 成本为：

```Markdown
C(t) = sum_i w_i * A_i(t)
```

其中：

- `w_i` 为监控量 `i` 的业务权重
- `A_i(t)` 为其当前 AoI

该指标贯穿整个工程，是后续 MDP、Whittle 指数和实验对比的统一优化目标。

## 3. 基线调度策略

当前工程实现了 5 种在线调度策略：

1. `RoundRobinScheduler`
2. `PeriodicScheduler`
3. `GreedyScheduler`
4. `RandomScheduler`
5. `WhittleScheduler`

统一接口定义在 `algorithms/base.py` 中：

```python
class SchedulerBase(ABC):
    def reset(self) -> None:
        ...

    @abstractmethod
    def select_action(self, env) -> Optional[int]:
        ...
```

### 3.1 Round Robin

按固定顺序轮询所有监控量，适合作为最简单的公平基线。

### 3.2 Periodic

按预设周期模式选择 source，适合表示工程上固定配额或周期性服务。

### 3.3 Greedy

每个时隙选择当前 `w_i * A_i` 最大的 source：

```text
a_t = arg max_i (w_i * A_i(t))
```

它是一个短视策略，只利用当前状态，不显式考虑未来收益。

### 3.4 Random

每个时隙均匀随机选择一个 source，作为最弱基线。

### 3.5 Whittle

通过单类松弛子问题构造指数，再在线选择当前指数最大的 source，是本项目的核心方法。

## 4. 单类 MDP 建模

单类问题求解位于：

- `solver/dp_solver.py`
- `solver/threshold_solver.py`

### 4.1 单类状态与动作

对单个 source，定义：

- 状态：当前 AoI `a`
- 动作：
  - `passive`：本时隙不调度
  - `active`：本时隙调度

状态空间被截断为：

```text
a in {1, 2, ..., A_max}
```

### 4.2 单类 Bellman 方程

在平均成本 MDP 下，单类子问题满足：

```text
g + h(a) = min {
    c(a, passive) + h(min(a+1, A_max)),
    c(a, active) + p * h(1) + (1-p) * h(min(a+1, A_max))
}
```

其中：

- `g` 是平均成本
- `h(a)` 是相对价值函数
- `p` 是更新成功概率

### 4.3 相对值迭代

当前实现通过相对值迭代求解最优策略：

1. 初始化偏置函数 `h(a)=0`
2. 计算每个状态下 `Q_passive` 和 `Q_active`
3. 取较小值作为新价值
4. 用参考状态归一化，消去常数漂移
5. 直到收敛

这样可得到：

- 每个状态下的最优动作
- 相对价值函数
- 阈值结构是否存在

## 5. 阈值结构验证

在 `solver/threshold_solver.py` 中，阈值结构定义为：

```text
存在阈值 theta，使得：
当 a < theta 时，最优动作为 passive
当 a >= theta 时，最优动作为 active
```

当前实现通过检查最优动作序列是否满足单调二值结构来验证这一点。

阈值结构的重要性在于：

1. 它说明单类问题存在可解释策略结构
2. 它为 Whittle 指数构造提供数值基础
3. 它支持后续论文中的结构性分析

## 6. 拉格朗日松弛

原始多类问题存在耦合约束：

```text
sum_i u_i(t) <= 1
```

表示每个时隙最多调度一个 source。

为解除耦合，当前工程使用拉格朗日松弛，将多类问题分解为多个单类问题。

### 6.1 被动补贴定义

在 `solver/lagrangian.py` 中，单类松弛子问题采用被动补贴 `lambda`，定义即时成本为：

```text
c_lambda(a, passive) = w * a - lambda
c_lambda(a, active)  = w * a
```

解释如下：

- 若选择 `passive`，获得一个补贴 `lambda`
- 若选择 `active`，则不获得该补贴

这样就可以把单类最优策略写成 `lambda` 的函数。

## 7. Whittle 指数构造

Whittle 指数实现位于 `algorithms/whittle.py`。

### 7.1 无差异条件

对固定状态 `a`，定义：

```text
gap(lambda; a) = Q_active(a; lambda) - Q_passive(a; lambda)
```

则：

- `gap < 0`：active 更优
- `gap > 0`：passive 更优
- `gap = 0`：二者无差异

Whittle 指数就是使该状态下主动与被动无差异的补贴值：

```text
W(a) = { lambda | Q_active(a; lambda) = Q_passive(a; lambda) }
```

### 7.2 数值计算方法

当前实现采用数值二分法：

1. 先找到一个包含根的补贴区间
2. 重复计算中点处的 `gap(lambda; a)`
3. 根据符号缩小区间
4. 直到满足误差阈值

这样得到每个 AoI 状态对应的 Whittle 指数。

### 7.3 在线查表调度

为了保证工程上可运行，`WhittleScheduler` 在初始化时会为每个 source 预计算：

```text
AoI = 1, 2, ..., A_max
```

对应的指数表。

在线调度时只需要：

1. 读取当前所有 source 的 AoI
2. 查出对应 Whittle 指数
3. 选择指数最大的 source

因此在线复杂度约为 `O(N)`。

## 8. 有效成功概率

在当前仿真环境中，更新成功需要两个条件同时成立：

1. 当前时隙采样成功
2. 当前时隙传输成功

因此 Whittle 单类问题中使用的有效成功概率为：

```text
p_eff = sampling_rate * channel_success_prob
```

这一定义见 `effective_update_success_prob()`。

## 9. 指标体系

当前工程统一指标包括：

1. 系统平均加权 AoI
2. 各类监控量平均 AoI
3. 高优先级业务平均 AoI
4. 系统峰值 AoI
5. 峰值加权 AoI
6. 平均决策耗时
7. 总运行时间

其中：

- 平均指标用于反映长期性能
- 峰值指标用于反映最坏情况下的信息陈旧风险
- 时间复杂度指标用于支撑工程可实现性

## 10. 方法链路总结

本项目当前方法链路可概括为：

```text
AoI 环境建模
-> 基线策略实现
-> 单类平均成本 MDP
-> 阈值结构验证
-> 拉格朗日松弛
-> Whittle 指数计算
-> 在线 Whittle 调度
-> 标准/扩展实验验证
```

这条链路已经形成一个可复现、可扩展、适合论文支撑的完整工程基础。
