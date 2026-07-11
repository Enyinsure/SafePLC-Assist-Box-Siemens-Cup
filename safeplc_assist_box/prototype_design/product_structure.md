# SafePLC-Assist Box 产品结构

## 产品组成

SafePLC-Assist Box 由 Streamlit 前端、统一 Agent Orchestrator、专业 Agent Pool、Shared Evidence Pool、Judge Agent、多模态检索工具、典型案例和运维记录演示模块组成。

## 软件入口

- 前端：`safeplc_assist_box/app_assist_box.py`
- 统一后端：`safeplc_assist_box/agents/orchestrator.py`
- CLI：`python -m safeplc_assist_box.agents.orchestrator`
- Benchmark：`safeplc_assist_box/evaluation/run_agent_benchmark.py`
- Ablation：`safeplc_assist_box/evaluation/run_agent_ablation.py`

## 数据流

用户问题先由 Supervisor 分解并选择专业 Agent。Agent 通过统一 Tool Registry 检索文本、表格和图像证据，Shared Evidence Pool 去重并标记冲突，Judge 对每条 claim 进行证据闭环检查，Verifier 再阻止无证据或不一致结论进入最终答案。

## 工业操作边界

系统是离线只读知识助手，不连接或控制真实 PLC。对于短接安全回路、旁路保护、带电接线、强制输出等请求，系统拒绝提供执行步骤，并给出停机、隔离、查阅图纸、记录现象和交由具备资质人员处理等替代建议。
