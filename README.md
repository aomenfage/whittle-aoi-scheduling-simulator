# 基于Whittle指数策略的 AoI 状态更新仿真系统

## 项目介绍
本项目面向网络监测场景，研究目标不是最小化传输时延，而是最小化加权信息年龄（Weighted AoI）。
系统采用单台节点、多类监控量、单跳状态更新、离散时隙建模，并逐步实现：

1. 基础 AoI 仿真环境
2. 多种基线调度策略
3. 单类平均成本 MDP
4. 阈值结构验证
5. 拉格朗日松弛与 Whittle 指数调度
6. 标准对比实验与扩展敏感性实验

## 目录说明
```text
AOITest/
├─ algorithms/              # 调度策略：RoundRobin / Periodic / Greedy / Random / Whittle
├─ config/                  # JSON/YAML 配置文件
├─ env/                     # 仿真环境：Source / Channel / AoIEnv
├─ experiments/             # 单项实验脚本与实验辅助模块
├─ results/                 # 实验结果、CSV、图表
├─ solver/                  # 单类 MDP、阈值分析、拉格朗日松弛
├─ tests/                   # 基础单元测试
├─ tools/                   # README 生成等工程脚本
├─ utils/                   # 指标统计、绘图、日志
├─ main.py                  # 单场景快速运行入口
├─ runner.py                # 标准对比实验入口
└─ run_all.py               # 一键复现全部核心实验
```

## 环境依赖
推荐 Python 3.11+。核心依赖如下：

```text
numpy
pandas
matplotlib
```

若使用虚拟环境，可执行：

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## 运行方式
### 1. 单场景策略运行
```bash
python main.py --strategy all
python main.py --strategy whittle
```

### 2. 标准论文主实验
```bash
python runner.py --suite standard --config config/runner_default.json
```

### 3. 扩展敏感性实验
```bash
python runner.py --suite extended
```

### 4. 一键复现全部核心实验
```bash
python run_all.py --config config/run_all_default.json
```

### 5. 单类 MDP 与阈值验证
```bash
python experiments/exp_single_arm_mdp.py --lambda-value 8.0
```

### 6. Whittle 与 Greedy 决策差异示例
```bash
python experiments/exp_whittle_demo.py
```

### 7. 运行基础测试
```bash
python -m unittest discover -s tests -v
```

## 实验复现步骤
1. 创建并激活 Python 虚拟环境
2. 安装依赖 `pip install -r requirements.txt`
3. 执行 `python run_all.py --config config/run_all_default.json`
4. 查看 `results/` 下自动生成的图表与 CSV
5. 若只复现实验主表，可执行 `python runner.py --suite standard`
6. 若复现扩展实验，可执行 `python runner.py --suite extended`

## 结果文件命名规范
图表与表格命名遵循以下原则：

- 图：`fig_<experiment>_<metric>_<suffix>.png`
- 表：`table_<experiment>_<content>.csv`
- 轨迹：`trajectory_<scenario>_<strategy>_<run>.csv`

示例：
- `fig_scalability_avg_weighted_aoi_vs_N.png`
- `table_standard_summary_aggregated.csv`
- `trajectory_N5_hetero_whittle_run0.csv`

## 工程说明
- 所有实验均优先通过配置文件管理参数
- 所有策略均实现统一调度接口
- 所有指标计算统一走 `utils/metrics.py`
- 所有图表输出统一走 `utils/plotter.py`
- 所有扩展实验可通过 `runner.py --suite extended` 串行运行
