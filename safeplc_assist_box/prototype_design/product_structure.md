# SafePLC-Assist Box 产品结构说明

## 1. 产品组成
SafePLC-Assist Box 由本地计算终端、Streamlit 产品化前端、SafePLC-Agent 后端、多模态手册知识库、典型案例库、证据卡片模块和运维记录生成模块组成。

## 2. 硬件载体
当前原型采用“笔记本电脑 + 展示板 + 模拟 S7 模块卡片 + 运维记录卡片”的桌面展示套件。不连接真实 PLC，不执行真实控制动作。

## 3. 软件模块
- 产品化前端：safeplc_assist_box/app_assist_box.py
- 典型案例：safeplc_assist_box/demo_cases.json
- 证据卡片：safeplc_assist_box/evidence_card_formatter.py
- 运维记录：safeplc_assist_box/work_order_demo.py
- 后端入口：s7_multimodal_v1/ask_s7_agent_v2.py

## 4. 数据流
用户输入问题后，前端通过 subprocess 调用 s7rag 环境中的 Agent v2。Agent v2 完成澄清、安全判断和多模态 RAG 检索后返回回答、页码、图文证据和安全判断，前端再整理为证据卡片和运维辅助记录。

## 5. 用户交互流程
1. 用户进入产品首页。
2. 在工业知识问答页输入问题。
3. 系统判断是否需要补充型号或上下文。
4. 对正常问题返回手册证据。
5. 对危险操作问题进行安全拒答。
6. 用户可生成运维辅助记录。

## 6. 安全边界
本产品是工业知识安全问答终端，不是 PLC 控制设备。不连接真实 PLC，不进行真实 PLC 通信，不替代现场规程、工程师判断和企业审批流程。
