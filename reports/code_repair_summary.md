# Code Repair Summary

本报告只确认代码实现、单元测试、SAMPLE regression 和 mock Chroma 测试。真实 Chroma、Figure Chroma、图片路径、FULL Benchmark 和服务器性能由用户自行在目标服务器验证。

本轮修复覆盖 Python 3.10/3.11 兼容性、显式 Chroma collection 选择、本地 embedding 适配与维度检查、严格 JSONL fallback、模型身份解析、证据排序与去重、查询分解、claim-level Judge、答案 verifier，以及部署诊断脚本。

仓库不包含真实服务器 FULL 验收结论。所有目标服务器产生的诊断、benchmark、ablation 和验收输出应写入被 Git 忽略的 `reports/runtime/`。
