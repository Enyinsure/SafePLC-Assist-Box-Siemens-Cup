#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

APP_PATH = Path("safeplc_assist_box/app_assist_box.py")
if not APP_PATH.exists():
    raise FileNotFoundError("未找到 safeplc_assist_box/app_assist_box.py，请在 GitHub 仓库根目录运行本脚本。")

text = APP_PATH.read_text(encoding="utf-8")
start_marker = "# ============================================================\n# Complex Demo Cases Panel for Siemens Cup Review"

if start_marker in text:
    text = text.split(start_marker)[0].rstrip() + "\n"

complex_block = r"""
# ============================================================
# Complex Demo Cases Panel for Siemens Cup Review
# Added for more general and complex industrial review scenarios
# ============================================================
def render_complex_demo_cases_panel() -> None:
    import json
    from pathlib import Path

    st.markdown("## 复杂典型案例展示")
    st.caption("用于展示系统面对多条件、多对象、多图文证据、高风险混合请求等更通用场景时的处理能力。")

    complex_cases_path = Path(__file__).parent / "demo_cases_complex.json"

    if not complex_cases_path.exists():
        st.warning("未找到 demo_cases_complex.json，请确认文件已放在 safeplc_assist_box/ 目录下。")
        return

    try:
        complex_cases = json.loads(complex_cases_path.read_text(encoding="utf-8"))
    except Exception as exc:
        st.error(f"复杂案例文件读取失败：{exc}")
        return

    if not complex_cases:
        st.info("复杂典型案例文件为空。")
        return

    titles = [
        f"{case.get('id', '')}｜{case.get('title', '')}"
        for case in complex_cases
    ]

    selected_title = st.selectbox(
        "选择复杂典型案例",
        titles,
        key="complex_demo_case_selector",
    )

    selected_case = complex_cases[titles.index(selected_title)]

    st.markdown("### 用户复杂提问")
    st.info(selected_case.get("user_question", ""))

    col1, col2, col3 = st.columns(3)
    col1.metric("问题类型", selected_case.get("expected_question_type", ""))
    col2.metric("系统动作", selected_case.get("expected_action", ""))
    col3.metric("风险等级", selected_case.get("expected_risk_level", ""))

    evidence_types = selected_case.get("expected_evidence_types", [])
    if evidence_types:
        st.markdown("### 预期证据类型")
        for item in evidence_types:
            st.markdown(f"- {item}")

    answer_points = selected_case.get("expected_answer_points", [])
    if answer_points:
        st.markdown("### 预期回答要点")
        for item in answer_points:
            st.markdown(f"- {item}")

    st.markdown("---")
    st.caption(
        "说明：该区域用于比赛评审展示，证明系统不只支持固定单点问答，"
        "也覆盖复杂工业查询、故障排查、多证据返回和安全风险识别。"
    )
"""

if "def render_complex_demo_cases_panel" not in text:
    if "\ndef main(" in text:
        text = text.replace("\ndef main(", complex_block + "\n\ndef main(", 1)
    else:
        text = text.rstrip() + "\n" + complex_block + "\n"

old = "    with tab_demo:\n        render_demo_tab()"
new = "    with tab_demo:\n        render_demo_tab()\n        render_complex_demo_cases_panel()"

if old in text and new not in text:
    text = text.replace(old, new, 1)

APP_PATH.write_text(text, encoding="utf-8")
print("OK: app_assist_box.py 已接入复杂典型案例面板")
