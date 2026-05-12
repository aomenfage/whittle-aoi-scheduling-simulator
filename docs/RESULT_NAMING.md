# 图表与表格命名规范

## 目标

统一实验结果文件命名，便于论文插图、表格引用、脚本批量处理与版本管理。

## &#x20;统一前缀：`fig_`

- 命名格式：`fig_<experiment>_<metric>_<variant>.png`

示例：

- `fig_standard_avg_weighted_aoi_mean_std.png`
- `fig_scalability_runtime_vs_N.png`
- `fig_weight_sensitivity_high_priority_aoi_vs_weight.png`
- `fig_peak_aoi_system_peak_aoi_by_scenario.png`

## 表格命名

- 统一前缀：`table_`
- 命名格式：`table_<experiment>_<content>.csv`

示例：

- `table_standard_run_metrics.csv`
- `table_standard_summary_aggregated.csv`
- `table_scalability_summary_with_N.csv`
- `table_channel_sensitivity_summary_aggregated.csv`

## 轨迹文件命名

- 统一前缀：`trajectory_`
- 命名格式：`trajectory_<scenario>_<strategy>_<run>.csv`

示例：

- `trajectory_N5_hetero_whittle_run0.csv`
- `trajectory_N3_demo_greedy_run2.csv`

## 报告模板命名

- 统一前缀：`template_`
- 命名格式：`template_<topic>.md` 或 `template_<topic>.txt`

示例：

- `template_paper_results_summary.md`
- `template_scalability_conclusion.txt`

