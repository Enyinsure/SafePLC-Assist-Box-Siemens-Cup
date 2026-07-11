# SafePLC-Assist Box 西门子杯说明

SafePLC-Assist Box 面向 PLC 教学、实训和维护查证，围绕 S7-1500、ET 200MP 等工业手册提供文本、表格和图像证据检索。系统只提供离线、只读的知识辅助，不连接真实 PLC、TIA Portal 或 OT 网络，也不执行写入和控制动作。

## Agent 架构

所有入口统一调用仓库内的 `safeplc_assist_box.agents.orchestrator.run_agent_system()`：

1. Dynamic Supervisor 分解问题并选择少量专业 Agent。
2. 专业 Agent 独立返回结构化 claim、证据引用或 abstain。
3. Shared Evidence Pool 统一证据、模型身份、来源和冲突。
4. Judge Agent 在 claim 级别检查证据覆盖、型号、数值、单位、接口与图像要求。
5. Verifier 和确定性合成器只输出通过审查的结论。

前端、CLI、benchmark 和 ablation 共用上述 Orchestrator，不依赖仓库外 Python 脚本或预先存在的 Conda 环境。

## 运行

```bash
python -m safeplc_assist_box.agents.orchestrator "CPU 1517-3 PN 的 X1 接口在哪里？" --mode SAMPLE --json
streamlit run safeplc_assist_box/app_assist_box.py
```

SAMPLE 仅用于本地功能回归。FULL 需要用户在目标服务器显式配置 collection、embedding 和资产路径，并按 `docs/FULL_SERVER_VALIDATION.md` 自行验证；仓库不声明真实服务器、Chroma、图片或性能已通过验收。
