# SafePLC-Assist Box

SafePLC-Assist Box 是面向西门子杯自由探索赛道的工业知识安全问答终端原型。

项目围绕西门子 S7-1500 / ET 200MP 等工业手册知识，构建一个具备安全边界、证据追溯、图文证据展示和答案一致性检查能力的产品化原型系统。

English summary:  
SafePLC-Assist Box is a safety-aware industrial knowledge QA terminal prototype for Siemens Cup, featuring evidence confidence, answer-evidence checking, visual evidence rendering, and a physical terminal design.

---

## Project Positioning

本项目不是普通搜索引擎，也不是简单 RAG 问答页面。

它的目标是构建一个面向工业知识辅助的安全问答终端，重点包括：

- 工业手册知识检索
- 工业安全风险分级
- 问题类型分类与路由
- Evidence Confidence 证据置信度评估
- Answer-Evidence Check 答案-证据一致性检查
- V1.1 证据卡片面板
- 图文证据图片展示
- OFFLINE / READ-ONLY 安全边界
- Streamlit 产品化前端
- 外置计算主机 + 实体终端盒子方案

---

## Technical Boundary

This system does not:

- Connect to real PLC devices
- Connect to TIA Portal
- Execute PLC communication, download, write, start, stop, or control actions
- Collect real IT / OT network data
- Replace Siemens official manuals, site safety rules, or certified engineers

中文说明：

本系统不连接真实 PLC，不接入 TIA Portal，不执行任何 PLC 下载、写入、启停或控制动作，不采集真实 IT / OT 网络数据。  
系统定位为工业知识问答、证据追溯、安全提示和教学演示辅助工具。

---

## Main Capabilities

### 1. Safety-aware Industrial QA

系统会对问题进行工业安全风险判断，区分普通知识问题、配置类问题、维护类问题和潜在高风险操作问题。

### 2. Evidence Confidence

系统会判断当前回答是否具备足够证据支撑，并输出证据置信度，例如：

- High
- Medium
- Low
- Conflict

### 3. Answer-Evidence Check

系统会检查答案中的关键声明是否能够被当前证据支持，并给出：

- PASS
- REVIEW
- FAIL

### 4. V1.1 Evidence Card Panel

系统会生成结构化证据卡片，包括：

- page
- figure_id
- source
- title
- module
- parameter
- snippet
- confidence

### 5. Visual Evidence Rendering

系统已经支持图文证据显示。

当证据卡片中包含页码或 figure_id，例如：

```text
page: 641
figure_id: page_0641_visual
```

前端会自动尝试查找对应图片：

```text
page_0641.jpg
```

并在 Streamlit 证据卡片面板中直接显示该图文证据。

这使系统不只是显示文本证据，而是能够展示手册页面截图或图文证据页面，从而形成：

```text
回答结果
↓
证据置信度
↓
答案一致性检查
↓
结构化证据卡
↓
原始图文证据
```

---

## Visual Evidence Assets

在本地演示环境中，图文证据图片可存放于：

```text
safeplc_assist_box/assets/visual_candidate_pages/
```

或从本地多模态运行目录恢复，例如：

```text
full_restore_agent_v2/s7_multimodal_v1/images/visual_candidate_pages/
release_selfcheck_agent_v1/s7_multimodal_v1/images/visual_candidate_pages/
release_selfcheck_format_opt_stress_ok/s7_multimodal_v1/images/visual_candidate_pages/
release_selfcheck_safety_guard_v1/s7_multimodal_v1/images/visual_candidate_pages/
```

For repository size and copyright reasons, the public GitHub repository does not include full Siemens manuals, full OCR outputs, vector databases, or full visual evidence image assets.

完整图文证据资产只在本地演示环境中使用，公开仓库仅保留代码逻辑、项目结构和必要说明。

---

## Repository Boundary

This public repository does not include:

- Full Siemens manual PDFs
- Full OCR intermediate outputs
- Full vector databases
- Full visual evidence image assets
- Local model weights
- Large compressed release packages
- Private keys, tokens, or environment files

The repository is intended to show:

- Front-end implementation
- Safety-aware QA logic
- Evidence confidence module
- Answer-evidence checking module
- Visual evidence rendering logic
- Evaluation scripts and reports
- Hardware prototype documentation
- Competition-oriented product materials

---

## Run

```bash
conda activate s7rag_ui
bash run_streamlit_safeplc_assist_box.sh
```

Then open:

```text
http://localhost:8501
```

---

## Main Modules

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

### Module Description

- `app_assist_box.py`: Streamlit 产品化前端，包含安全边界、证据面板和图文证据显示
- `question_classifier_v11.py`: 问题类型分类与路由
- `safety_risk_guard_v11.py`: 工业安全风险分级
- `evidence_confidence_v11.py`: 证据置信度评估
- `answer_evidence_checker_v11.py`: 答案-证据一致性检查
- `evidence_card_formatter.py`: 证据卡片格式化
- `product_demo_mode.py`: 产品演示模式
- `work_order_demo.py`: 工单式演示输出
- `run_v11_eval.py`: V1.1 测试脚本
- `run_v12_extended_eval.py`: V1.2 扩展测试脚本

---

## Hardware Prototype

项目采用方案 B：

```text
External computing host + productized physical terminal shell
```

即：

```text
外置计算主机 + 产品化实体终端外壳
```

当前原型中，笔记本作为外置计算主机，实体盒子作为显示与交互终端。

实体终端设计包括：

- 屏幕显示
- 状态指示灯
- Query / Demo / Export Log 按钮
- SafePLC-Assist Box 铭牌
- OFFLINE / READ-ONLY 标签
- PLC CONTROL DISABLED 标签

该实体终端不是 PLC 控制器，不连接真实 PLC，也不执行任何控制动作。

---

## Competition Materials

Relevant competition materials are organized in:

```text
safeplc_assist_box/competition_docs/
safeplc_assist_box/prototype_design/
safeplc_assist_box/reports/
hardware/
```

These folders include:

- Business plan materials
- Product R&D plan
- PPT outline
- Prototype appearance design
- Hardware BOM
- Product structure notes
- Demo booth layout
- Test video script
- Product test report
- Prototype acceptance report
- User scenario report

---

## Evaluation

The project includes V1.1 and V1.2 evaluation files:

```text
safeplc_assist_box/testset_v11_basic.json
safeplc_assist_box/testset_v12_extended.json
safeplc_assist_box/eval_report_v11.json
safeplc_assist_box/eval_report_v12_extended.json
```

These files are used to evaluate:

- Question classification
- Safety risk classification
- Evidence confidence
- Answer-evidence consistency
- Evidence card generation
- Extended demo scenario coverage

---

## Project Version

Current public repository version:

```text
SafePLC-Assist Box V1.2
```

Core features:

- Safety-aware QA
- Evidence confidence
- Answer-evidence check
- Structured evidence cards
- Visual evidence rendering
- Streamlit product UI
- Physical terminal prototype design

---

## License / Usage

This project is provided for Siemens Cup competition review, educational demonstration, and research-style prototype evaluation.

It is not intended for direct industrial deployment or real PLC operation.
