# SafePLC-Assist Box 西门子杯答辩 PPT 大纲

本文档提供 SafePLC-Assist Box 西门子杯答辩展示的大纲，重点说明产品定位、技术贡献、安全边界、证据流程、本地图文证据显示、评测和实体原型设计。

---

## 第 1 页：标题

SafePLC-Assist Box

工业知识安全问答终端原型

关键词：

```text
工业知识问答
安全边界
Evidence Confidence
Answer-Evidence Check
结构化证据卡片
本地图文证据显示
实体终端原型
```

---

## 第 2 页：项目背景

工业手册篇幅大、内容复杂、人工查找效率低。PLC 相关知识问题常涉及模块型号、参数、接线、网络连接、安全说明和维护信息。

普通搜索引擎或通用聊天机器人不足以满足工业问答对安全、证据和可追溯性的要求。

---

## 第 3 页：痛点

| 痛点 | 说明 |
|---|---|
| 手册庞大 | 用户需要查找大量技术文档 |
| 问题不完整 | 用户可能遗漏型号、模块或参数 |
| 存在危险请求 | PLC 问题可能涉及高风险操作 |
| 回答缺少依据 | 普通回答可能没有证据支持 |
| 可追溯性弱 | 纯文本回答难以审计 |
| 产品形态不足 | 纯网页演示不够像完整产品 |

---

## 第 4 页：项目目标

构建安全感知的工业知识问答终端原型，提供：

- 安全风险判断
- Evidence Confidence
- Answer-Evidence Check
- 结构化证据卡片
- 本地图文证据显示
- 离线 / 只读边界
- 实体终端原型设计

---

## 第 5 页：产品定位

SafePLC-Assist Box 不是：

- 普通聊天机器人
- 普通搜索引擎
- PLC 控制器
- 西门子官方手册或工程师的替代品

SafePLC-Assist Box 是：

```text
离线工业知识问答
+
安全风险判断
+
证据复核
+
本地图文证据显示
+
产品化终端形态
```

---

## 第 6 页：系统边界

系统不连接真实 PLC，不接入 TIA Portal，不执行 PLC 通信、写入、下载、启停或控制动作，不采集真实 IT / OT 网络数据。

关键边界标签：

```text
OFFLINE / READ-ONLY
PLC CONTROL DISABLED
KNOWLEDGE QA ONLY
```

---

## 第 7 页：总体架构

```text
用户问题
->
Streamlit 产品界面
->
问题分类
->
安全风险判断
->
工业知识回答
->
Evidence Confidence
->
Answer-Evidence Check
->
结构化证据卡片
->
本地图文证据显示
->
人工复核 / 学习 / 演示
```

---

## 第 8 页：核心模块

| 模块 | 作用 |
|---|---|
| `app_assist_box.py` | 产品界面和证据面板 |
| `question_classifier_v11.py` | 问题分类 |
| `safety_risk_guard_v11.py` | 安全风险判断 |
| `evidence_confidence_v11.py` | Evidence Confidence |
| `answer_evidence_checker_v11.py` | Answer-Evidence Check |
| `evidence_card_formatter.py` | 证据卡片格式化 |
| `run_v12_extended_eval.py` | V1.2 评测运行 |

---

## 第 9 页：安全问答

| 用户问题类型 | 系统行为 |
|---|---|
| 普通知识问题 | 提供证据化回答 |
| 上下文不足 | 触发澄清或复核 |
| 安全相关问题 | 提供安全提醒和证据 |
| 高风险控制请求 | 不提供可执行控制指令 |

---

## 第 10 页：证据流程

展示 Evidence Confidence、Answer-Evidence Check 和结构化证据卡片如何帮助评审者判断回答是否可信、是否需要复核、是否有证据支撑。

---

## 第 11 页：本地图文证据显示

当证据卡片包含页码或 `figure_id` 时，前端尝试查找本地图文证据文件。

示例：

```text
page: 641
figure_id: page_0641_visual
```

对应文件示例：

```text
page_0641.jpg
```

完整图文证据资产只在本地演示环境使用，不放入公开仓库。

---

## 第 12 页：硬件原型方案

项目采用方案 B：

```text
外置计算主机 + 产品化实体终端外壳
```

实体外壳仍在进行中，计划包含显示区域、SAFE / CAUTION / HIGH_RISK / CHECK 指示、Query / Demo / Export Log 按钮、产品铭牌和安全边界标签。

---

## 第 13 页：前面板设计

```text
+-------------------------------------------------------+
| SafePLC-Assist Box V1.2                               |
| 工业知识安全问答终端                                  |
|                                                       |
| +---------------------------------------------------+ |
| |              Streamlit 界面显示区                 | |
| | - 问题输入                                        | |
| | - Evidence Confidence                             | |
| | - Answer-Evidence Check                           | |
| | - 图文证据卡片                                    | |
| +---------------------------------------------------+ |
|                                                       |
| [SAFE]      [CAUTION]      [HIGH_RISK]      [CHECK]   |
| [Query]               [Demo]              [Export Log] |
| OFFLINE / READ-ONLY                                   |
| PLC CONTROL DISABLED                                  |
| KNOWLEDGE QA ONLY                                     |
+-------------------------------------------------------+
```

---

## 第 14 页：当前进展

| 内容 | 状态 |
|---|---|
| 核心软件原型 | 已完成 |
| Streamlit 产品界面 | 已完成 |
| 问题分类 | 已完成 |
| 安全风险判断 | 已完成 |
| Evidence Confidence | 已完成 |
| Answer-Evidence Check | 已完成 |
| 结构化证据卡片 | 已完成 |
| 本地图文证据显示逻辑 | 已完成 |
| V1.1 / V1.2 评测文件 | 已完成 |
| 硬件设计文档 | 已完成 |
| 实体外壳 | 进行中 |
| 最终照片和演示视频 | 后续补充 |

---

## 第 15 页：公开仓库边界

公开仓库不包含完整西门子手册、完整 OCR 输出、向量库、模型权重、完整图文证据资产、压缩交付包、私钥、token 或环境文件。

原因包括仓库体积、版权、隐私和安全边界。

---

## 第 16 页：创新点

1. 工业知识问答与安全边界结合。
2. Evidence Confidence 支持回答可信度判断。
3. Answer-Evidence Check 支持回答与证据一致性复核。
4. 结构化证据卡片提升可追溯性。
5. 本地图文证据显示增强证据链。
6. 实体终端原型提升竞赛产品形态。

---

## 第 17 页：总结

SafePLC-Assist Box 将工业手册知识问答、安全风险判断、Evidence Confidence、Answer-Evidence Check、结构化证据卡片、本地图文证据显示和实体终端原型设计结合起来。

当前版本适合软件级和文档级评审，实体外壳、最终照片和演示视频将在后续完善阶段补充。
