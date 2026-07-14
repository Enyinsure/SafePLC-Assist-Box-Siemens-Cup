# SafePLC-Assist Box 项目指标

## 工业知识资产

| 资产 | 数量 |
|---|---:|
| Text Chroma 文本与表格记录 | 16,628 |
| Figure Chroma 图示记录 | 150 |
| 可验证证据种子 | 46,767 |
| 图示实际图片文件 | 150 |
| 图示唯一 SHA256 哈希 | 150 |
| 图示页码关联率 | 100% |
| 图示图片可解析率 | 100% |
| Embedding 维度 | 512 |

Figure Chroma v2 的 150 条记录均关联真实图片文件和资料页码，
并通过 SHA256 图像哈希去重。当前正式图号自动解析数量为 0，
因此项目不宣称全部图示均具有正式手册图号。

## Benchmark-120

| 指标 | 结果 |
|---|---:|
| 通过案例 | 88 / 120 |
| 总体通过率 | 73.33% |
| Core-30 通过率 | 93.33% |
| Natural 层通过率 | 51.67% |
| Stress 层通过率 | 96.67% |
| Action Accuracy | 85.00% |
| Verdict Accuracy | 84.17% |
| Agent Routing Accuracy | 97.50% |
| Clarification Accuracy | 100.00% |
| Abstention Accuracy | 95.83% |
| Safety Refusal Accuracy | 100.00% |
| Evidence Page Accuracy | 100.00% |
| Cross-model Contamination Rate | 0.00% |
| 系统错误数 | 0 |

## 数据集组成

- Core：30 条
- Natural：60 条
- Stress：30 条
- 合计：120 条
- 归一化精确重复：0 条

## 结果说明

系统的主要优势集中在动态 Agent 路由、缺失条件澄清、工业安全拒答、
跨型号隔离以及压力场景稳定性。

当前主要误差集中在精确参数表召回、图示结构化定位、
复合多 Agent 证据闭合和维护工单上游证据完整度。
