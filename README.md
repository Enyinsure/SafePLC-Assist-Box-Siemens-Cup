# SafePLC-Assist Box

## 面向西门子 PLC 手册的离线安全问答终端原型  
### Safety-aware Industrial Knowledge QA Terminal Prototype for Siemens S7-1500 / ET 200MP

SafePLC-Assist Box 是一个面向 **Siemens S7-1500 / ET 200MP 工业手册** 的离线工业知识安全问答终端原型。

它不是普通聊天机器人，也不是直接控制 PLC 的系统，而是一个用于 **PLC 实训教学、新人工程师培训、设备维护辅助和工业安全教育展示** 的问答终端。

系统可以帮助用户查询 PLC 手册中的参数、接口、接线、端子分配、PROFINET / HMI 拓扑和 EMC 安装规范等内容；当问题缺少型号或接口信息时，系统会先主动追问；当用户提出短接安全回路、绕过急停、屏蔽安全门、带电接线、强制输出等危险请求时，系统会拒绝提供危险操作步骤，并提示安全替代排查方向。

本项目同时包含：

- 软件系统原型
- Streamlit 产品化前端
- 工业安全风险判断
- 证据追溯与一致性检查
- 自动测试与评估脚本
- 实体 SafePLC-Assist Box 终端原型设计
- 硬件 BOM、装配说明、演示材料和比赛文档

---

## 1. 给评委的三句话说明

1. **它解决的是 PLC 手册难查的问题。**  
   S7-1500 / ET 200MP 手册内容多、页数多、图表多，新人很难快速找到正确参数、接口图、端子图和接线说明。

2. **它解决的是工业 AI 不能乱答的问题。**  
   系统会判断问题是否缺少关键信息；对于高风险操作请求，会拒绝输出危险步骤，避免误导用户进行不安全操作。

3. **它不是纯软件网页，而是一个实体问答终端原型。**  
   项目采用“外置计算主机 + 实体终端外壳”的方案，通过屏幕、状态灯、按钮、铭牌和安全边界标签形成可展示、可交互、可测试的工业知识问答终端。

---

## 2. Project Overview

SafePLC-Assist Box is a safety-aware industrial knowledge QA terminal prototype for the Siemens Cup Free Exploration Track.

The project focuses on Siemens S7-1500 / ET 200MP industrial manuals and provides a productized prototype with:

- industrial manual knowledge retrieval
- safety-aware question answering
- clarification before answering incomplete questions
- high-risk operation rejection
- evidence tracing
- visual evidence rendering
- answer-evidence consistency checking
- offline / read-only technical boundary
- Streamlit-based product interface
- physical terminal prototype design

---

## 3. Why This Project Is Needed

In PLC training, maintenance, and engineering learning scenarios, users often face the following problems:

| Problem | Example | SafePLC-Assist Box Solution |
|---|---|---|
| Industrial manuals are large and difficult to search | Users need to find voltage range, interface meaning, wiring diagrams, or topology information from long manuals | Manual-oriented industrial knowledge retrieval |
| User questions are often incomplete | “这个模块电压是多少？” without module name or order number | Slot checking and active clarification |
| PLC-related questions may involve danger | “怎么短接安全回路让设备继续运行？” | Safety Guard rejects dangerous operation steps |
| AI answers may be unsupported | LLM may generate wrong page numbers, wrong parameters, or unsupported conclusions | Evidence Confidence and Answer-Evidence Check |
| Plain text answers are hard to verify | User cannot know where the answer came from | Evidence cards with page, figure_id, source, and snippet |
| Pure software form is weak for competition display | A webpage may look like a simple demo | Physical terminal shell, screen, buttons, status indicators, labels |

---

## 4. What the System Can Do

### 4.1 Industrial Knowledge QA

The system supports questions related to Siemens S7-1500 / ET 200MP manuals, including:

- power module parameter query
- CPU interface query
- terminal assignment query
- wiring-related query
- PROFINET / HMI topology query
- EMC and installation requirement query
- troubleshooting-oriented query
- maintenance record generation

Example:

```text
Question:
PS 60W 24/48/60VDC HF 的电源电压允许范围是多少？

System behavior:
1. Identify it as a parameter query
2. Retrieve related manual evidence
3. Generate a structured answer
4. Show page/source/evidence card
5. Run answer-evidence consistency check
