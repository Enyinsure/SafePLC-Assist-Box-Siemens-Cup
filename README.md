# SafePLC-Assist Box

## 面向西门子 PLC 手册的离线安全问答终端原型

SafePLC-Assist Box 是一个面向 Siemens S7-1500 / ET 200MP 工业手册的离线安全问答终端原型，主要用于高校 PLC 实训教学、新人工程师培训、设备维护辅助和工业安全教育展示。

它不是普通聊天机器人，也不是 PLC 控制器，而是一个帮助用户快速查询 PLC 手册内容、识别危险问题、追溯答案依据的工业知识辅助系统。

本项目解决的核心问题是：PLC 手册页数多、图表多、参数分散，新人很难快速查到正确内容；普通 AI 容易在型号不清、接口不明或证据不足时直接回答；工业场景中还存在短接安全回路、绕过急停、带电接线、强制输出等高风险问题，系统不能乱答。因此，本项目设计了一个“离线只读、安全可控、结果可复核、带实体终端形态”的工业知识问答原型。

---

## 一、项目定位

SafePLC-Assist Box 当前定位为：

```text
工业手册知识查询工具
+ 工业安全风险提醒工具
+ 可信证据追溯工具
+ PLC 实训教学辅助工具
+ 实体问答终端原型机
```

本项目不连接真实 PLC，不接入 TIA Portal，不执行任何 PLC 下载、写入、启动、停止或控制动作，不采集真实 IT / OT 网络数据，不替代 Siemens 官方手册、现场安全规程和具备资质人员判断。

---

## 二、给评委的三句话说明

1. 本项目不是简单聊天机器人，而是面向西门子 PLC 手册的工业知识问答终端。  
2. 系统不仅能回答参数、接口、接线、拓扑和 EMC 等问题，还能在信息不完整时主动追问，在危险问题出现时拒绝危险操作步骤。  
3. 项目包含软件系统和实体 SafePLC-Assist Box 终端原型，具备屏幕、状态灯、按钮、铭牌和安全边界标识，不是单纯网页演示。

---

## 三、项目要解决的问题

在 PLC 教学、实训、调试学习和设备维护辅助场景中，经常存在以下问题：

1. 西门子 S7-1500 / ET 200MP 手册内容多，参数、接口图、接线图、端子分配图和拓扑说明分散，人工查找效率低。
2. 新人提问经常不完整，例如“这个模块电压是多少”“这个接口在哪里”，如果系统直接猜测型号，容易误答。
3. 工业场景中存在高风险问题，例如短接安全回路、绕过急停、屏蔽安全门、带电接线、强制输出等，AI 不能提供危险操作步骤。
4. 普通问答系统即使给出答案，也很难说明答案依据来自哪里，用户无法快速复核。
5. 纯软件网页形态在比赛展示中产品感不足，因此本项目加入实体终端原型设计。

---

## 四、系统主要功能

### 1. 工业知识问答

系统支持围绕西门子 S7-1500 / ET 200MP 手册进行工业知识问答，包括：

- 电源模块参数查询
- CPU 接口查询
- 接线相关问题查询
- 端子分配图查询
- PROFINET / HMI 拓扑查询
- EMC 与安装规范查询
- 故障排查辅助
- 运维记录生成

示例：

```text
用户问题：
PS 60W 24/48/60VDC HF 的电源电压允许范围是多少？

系统行为：
识别为参数查询
检索相关手册证据
生成结构化回答
展示页码、证据类型和证据卡片
进行答案-证据一致性检查
```

### 2. 主动澄清

当用户问题缺少模块型号、订货号、接口名或报警信息时，系统不会直接猜测，而是先提醒用户补充关键信息。

示例：

```text
用户问题：
这个模块的电源电压是多少？

系统行为：
系统不会直接回答，而是提示用户补充模块型号、订货号或相关上下文。
```

这样可以降低因为型号不清导致的错误检索和错误回答。

### 3. 工业安全风险判断

系统会对用户问题进行安全风险分级：

| 风险等级 | 含义 | 系统处理方式 |
|---|---|---|
| SAFE | 普通知识查询 | 正常回答并给出证据 |
| CAUTION | 接线、调试、故障排查等谨慎场景 | 回答时附带安全提醒 |
| HIGH_RISK | 短接安全回路、绕过急停、屏蔽安全门、带电接线、强制输出等 | 拒绝提供危险操作步骤 |
| EMERGENCY | 触电、火灾、人员伤害、设备紧急事故等 | 提示立即遵守现场应急流程并联系专业人员 |

示例：

```text
用户问题：
怎么短接安全回路让设备继续运行？

系统行为：
系统判断为 HIGH_RISK，拒绝提供短接步骤，并提示应按照现场安全规程排查。
```

### 4. 证据追溯

系统回答时会尽量给出可复核的证据来源，包括：

- 手册页码
- 证据类型
- 图表编号
- 相关模块名称
- 证据片段
- 证据卡片
- 置信度判断
- 答案-证据一致性检查结果

这样可以避免系统只给出一个“看起来正确”的答案，而无法说明依据。

### 5. 答案-证据一致性检查

系统会检查回答中的关键声明是否能被检索到的证据支持，例如：

- 模块型号
- 电压
- 电流
- 功率
- 接口号
- 端口名称
- 页码
- 图号
- 接线相关描述

检查结果包括：

| 结果 | 含义 |
|---|---|
| PASS | 关键结论能够被证据支持 |
| REVIEW | 部分内容需要人工复核 |
| FAIL | 答案可能存在证据不足或冲突 |

### 6. 证据置信度判断

系统会对当前证据是否足够支撑回答进行分级：

| 等级 | 含义 |
|---|---|
| High | 证据较充分，可以较好支撑回答 |
| Medium | 证据有参考价值，但建议继续复核 |
| Low | 证据不足，不建议直接采信 |
| Conflict | 证据可能存在冲突或不匹配 |

### 7. 实体终端原型

本项目不是单纯软件系统，而是设计了 SafePLC-Assist Box 实体终端原型。

当前采用方案：

```text
外置计算主机 + 产品化实体终端外壳
```

当前阶段由笔记本作为外置计算主机运行软件系统，实体终端负责展示和交互。实体终端计划包括：

- 显示屏
- SAFE 状态灯
- CAUTION 状态灯
- HIGH_RISK 状态灯
- CHECK 状态灯
- Query 按钮
- Demo 按钮
- Export Log 按钮
- SafePLC-Assist Box 铭牌
- OFFLINE / READ-ONLY 标签
- PLC CONTROL DISABLED 标签
- USB-C / HDMI / 网口等接口标识
- 外壳结构
- 硬件 BOM
- 装配说明
- 演示视频

实体终端的作用是将软件系统产品化为可展示、可交互、可测试的工业知识安全问答终端原型。

---

## 五、系统工作流程

```text
用户输入问题
↓
问题类型识别
↓
安全风险判断
↓
关键信息完整性检查
↓
如果信息不足：主动追问
↓
如果问题危险：安全拒答
↓
如果问题安全且信息完整：检索手册证据
↓
生成结构化回答
↓
输出证据卡片
↓
进行证据置信度判断
↓
进行答案-证据一致性检查
↓
支持日志导出和结果复核
```

---

## 六、技术架构

```text
SafePLC-Assist Box
├── Streamlit 产品化前端
├── 工业问题类型分类模块
├── 动作路由模块
├── 关键信息完整性检查模块
├── 工业安全风险判断模块
├── 多模态手册证据检索模块
├── 证据卡片格式化模块
├── Evidence Confidence 证据置信度模块
├── Answer-Evidence Check 答案-证据一致性检查模块
├── 运维记录生成模块
├── 典型案例演示模块
├── 自动测试与评估脚本
└── 实体终端原型设计文档
```

---

## 七、核心技术模块

### 1. Question Classifier

用于判断用户问题类型，例如参数查询、接口图查询、接线查询、拓扑查询、故障排查、安全风险问题、运维记录生成或超出系统边界的问题。

### 2. Action Router

根据问题类型和风险等级决定系统动作：

| 动作 | 含义 |
|---|---|
| RETRIEVE | 检索证据并回答 |
| CLARIFY | 主动追问缺失信息 |
| SAFETY_GUARD | 安全护栏处理 |
| BOUNDARY_REPLY | 输出系统边界说明 |

### 3. Slot Completeness Checker

检查问题中是否缺少关键条件，例如模块型号、订货号、接口名、报警信息等。

### 4. Safety Guard

识别短接、绕过、带电操作、强制输出等危险请求，并拒绝输出危险步骤。

### 5. Multimodal Evidence Retrieval

面向工业手册中的文本、表格、接口图、端子图、接线图和拓扑图进行证据检索。

### 6. Evidence Confidence

判断当前证据是否足以支撑回答。

### 7. Answer-Evidence Consistency Checker

检查答案中的关键声明是否能被证据支持。

### 8. Streamlit Product Interface

提供产品化前端，包括首页、工业知识问答、典型案例、证据面板、技术边界、日志导出等功能。

---

## 八、问题类型

系统支持的问题类型包括：

| 类型 | 说明 |
|---|---|
| PARAM_QUERY | 参数查询 |
| FIGURE_QUERY | 接口图或图文证据查询 |
| WIRING_QUERY | 接线相关查询 |
| TOPOLOGY_QUERY | PROFINET / HMI / 网络拓扑查询 |
| TROUBLESHOOTING | 故障排查 |
| SAFETY_RISK | 安全风险问题 |
| WORK_ORDER | 运维记录生成 |
| EMC_ENV | EMC、安装环境与规范查询 |
| OUT_OF_SCOPE | 超出系统边界的问题 |

---

## 九、测试与评估

项目包含 basic 回归测试集和 extended 扩展测试集。

### V1.1 Basic Test

```text
测试文件：testset_v11_basic.json
测试数量：12 条

question_type_accuracy: 1.0
action_route_accuracy: 1.0
risk_level_accuracy: 1.0
clarify_trigger_accuracy: 1.0
```

### V1.2 Extended Test

```text
测试文件：testset_v12_extended.json
测试数量：50 条

question_type_accuracy: 1.0
action_route_accuracy: 1.0
risk_level_accuracy: 1.0
clarify_trigger_accuracy: 1.0
```

测试覆盖场景包括：

- 参数查询
- 接口图查询
- 端子分配图查询
- PROFINET / HMI 拓扑查询
- 接线谨慎提示
- EMC 与安装规范
- 高风险拒答
- 应急提示
- 故障排查
- 运维记录生成
- 超出边界问题

说明：

```text
当前测试主要验证问题分类、动作路由、安全风险分级和主动澄清逻辑。
测试结果不代表系统可以替代完整工业验证，也不代表可以替代专业工程师判断。
```

---

## 十、仓库结构

```text
.
├── README.md
├── PROJECT_FINAL_STATUS_SIEMENS_CUP_V12.txt
├── SAFEPLC_ASSIST_BOX_SIEMENS_CUP_V12_FINAL_CLEAN_manifest.txt
├── SAFEPLC_ASSIST_BOX_SIEMENS_CUP_V12_FINAL_CLEAN.sha256
├── run_streamlit_safeplc_assist_box.sh
├── docs/
├── hardware/
├── screenshots/
└── safeplc_assist_box/
```

主要目录说明：

| 路径 | 说明 |
|---|---|
| safeplc_assist_box/ | 核心软件系统、前端、分类器、安全护栏、证据检查、测试集 |
| docs/ | 项目文档、评审说明、技术状态说明 |
| hardware/ | 实体 Box 原型设计、BOM、装配说明 |
| screenshots/ | 系统截图 |
| PROJECT_FINAL_STATUS_SIEMENS_CUP_V12.txt | 项目最终技术状态说明 |
| SAFEPLC_ASSIST_BOX_SIEMENS_CUP_V12_FINAL_CLEAN_manifest.txt | clean 交付包文件清单 |
| SAFEPLC_ASSIST_BOX_SIEMENS_CUP_V12_FINAL_CLEAN.sha256 | sha256 校验文件 |

---

## 十一、核心文件

```text
safeplc_assist_box/
├── app_assist_box.py
├── question_classifier_v11.py
├── safety_risk_guard_v11.py
├── evidence_confidence_v11.py
├── answer_evidence_checker_v11.py
├── evidence_card_formatter.py
├── product_demo_mode.py
├── work_order_demo.py
├── demo_cases.json
├── testset_v11_basic.json
├── testset_v12_extended.json
├── run_v11_eval.py
├── run_v12_extended_eval.py
├── eval_report_v11.json
└── eval_report_v12_extended.json
```

文件说明：

| 文件 | 作用 |
|---|---|
| app_assist_box.py | Streamlit 产品化前端 |
| question_classifier_v11.py | 问题类型识别与动作路由 |
| safety_risk_guard_v11.py | 工业安全风险识别与高风险拒答 |
| evidence_confidence_v11.py | 证据置信度判断 |
| answer_evidence_checker_v11.py | 答案-证据一致性检查 |
| evidence_card_formatter.py | 证据卡片格式化 |
| product_demo_mode.py | 产品演示模式 |
| work_order_demo.py | 运维记录生成演示 |
| demo_cases.json | 典型演示案例 |
| testset_v11_basic.json | basic 回归测试集 |
| testset_v12_extended.json | extended 扩展测试集 |
| run_v11_eval.py | V1.1 自动评测脚本 |
| run_v12_extended_eval.py | V1.2 自动评测脚本 |

---

## 十二、运行方式

激活本地环境：

```bash
conda activate s7rag_ui
```

运行系统：

```bash
bash run_streamlit_safeplc_assist_box.sh
```

打开浏览器：

```text
http://localhost:8501
```

---

## 十三、演示案例

推荐演示顺序：

1. 展示 SafePLC-Assist Box 首页和技术边界。
2. 展示 OFFLINE / READ-ONLY / PLC CONTROL DISABLED 标识。
3. 输入缺少型号的问题，展示主动澄清。
4. 输入明确型号的问题，展示参数查询和证据卡片。
5. 输入接口图或拓扑问题，展示图文证据。
6. 输入短接安全回路等危险问题，展示 HIGH_RISK 拒答。
7. 展示运维记录生成。
8. 展示单次问答日志导出。
9. 展示 basic 和 extended 测试结果。
10. 展示实体 Box 外观、状态灯、按钮、铭牌和安全边界标签。

---

## 十四、实体 Box 方案

当前实体终端采用方案 B：

```text
笔记本作为外置计算主机
+
实体终端作为产品化展示与交互外壳
```

选择该方案的原因：

1. 保证当前软件系统稳定运行，避免迁移到树莓派或嵌入式设备造成依赖问题。
2. 保留完整实体产品形态，避免作品被认为是纯软件网页。
3. 方便在线上评审视频中展示系统外观、交互流程和安全边界。
4. 后续可以升级为树莓派、工业平板或边缘计算盒。

实体终端计划包含：

```text
外壳
显示屏
SAFE 状态灯
CAUTION 状态灯
HIGH_RISK 状态灯
CHECK 状态灯
Query 按钮
Demo 按钮
Export Log 按钮
项目铭牌
OFFLINE / READ-ONLY 标签
PLC CONTROL DISABLED 标签
接口标识
BOM
装配说明
实物照片
演示视频
```

---

## 十五、技术边界与安全声明

本项目当前是工业知识问答与安全运维辅助原型，不是现场控制系统。

系统明确不做以下事项：

- 不连接真实 PLC
- 不接入 TIA Portal
- 不执行真实 PLC 通信
- 不执行程序下载
- 不执行程序写入
- 不执行启动、停止或控制动作
- 不采集真实 IT / OT 网络数据
- 不作为现场安全控制系统
- 不替代 Siemens 官方手册
- 不替代现场电气安全规程
- 不替代具备资质人员判断
- 不对现场操作结果承担控制系统职责

---

## 十六、提交材料建议

比赛提交时建议同时准备：

- 项目书 PDF
- 演示视频 MP4
- 系统截图集 PDF
- 测试报告 PDF
- GitHub 仓库链接
- README 说明
- clean 交付包
- manifest 清单
- sha256 校验文件
- 实体终端 BOM
- 实体终端装配说明
- 前面板布局图
- 实体原型照片
- 典型问答日志样例 JSON

---

## 十七、项目版本

当前版本：

```text
SafePLC-Assist Box V1.2
```

当前主要能力：

- 工业知识问答
- 主动澄清
- 工业安全风险判断
- 高风险问题拒答
- 证据卡片
- 证据置信度判断
- 答案-证据一致性检查
- 图文证据展示
- Streamlit 产品化前端
- 运维记录生成
- 单次问答日志导出
- basic 回归测试集
- extended 扩展测试集
- 实体终端原型设计
- clean 交付包、manifest 和 sha256 校验

---

## 十八、项目总结

SafePLC-Assist Box 面向西门子 S7-1500 / ET 200MP 工业手册，构建了一个离线、安全、可复核、带实体终端形态的工业知识问答原型。

它重点解决 PLC 手册查询中“难查、问不清、易误答、危险问题不能乱答、答案不好复核、纯软件展示不足”的问题。

本项目的价值不在于直接控制 PLC，而在于为 PLC 实训教学、新人工程师培训、设备维护辅助和工业安全教育提供一个安全可信的知识问答终端原型。

一句话概括：

```text
SafePLC-Assist Box 是一个面向西门子 PLC 手册的离线安全问答终端原型，
让 PLC 知识查询更快，让危险问题不乱答，让答案依据可复核，让比赛作品具备实体产品形态。
```
