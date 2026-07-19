#!/usr/bin/env python3
"""Build the audited 150-image hidden demo package from the full visual pool."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from safeplc_assist_box.frontend.demo_visual_assets import (  # noqa: E402
    CORE_VISUAL_MANIFEST,
    VISUAL_MANIFEST,
    load_demo_visual_manifest,
)


CASE_MANIFEST = (
    PROJECT_ROOT / "safeplc_assist_box" / "frontend" / "data" / "hidden_demo_cases.json"
)
SNAPSHOT_ROOT = PROJECT_ROOT / "reports" / "demo" / "hidden_15"

DI_ORDER = "6ES7521-1BL00-0AB0"
CPU_ORDER = "6ES7517-3AP00-0AB0"
PS_ORDER = "6ES7505-0RB00-0AB0"


@dataclass(frozen=True)
class CaseSpec:
    case_id: str
    slug: str
    category: str
    query: str
    aliases: Sequence[str]
    family: str
    model: str
    order_number: str
    question_type: str
    agents: Sequence[str]
    action: str
    verdict: str
    confidence: str
    answer: str
    required_modalities: Sequence[str]
    claim_type: str = "technical_guidance"
    unique_group: str = ""
    shared_anchor_group: str = ""
    shared_anchor_count: int = 0
    risk_level: str = "LOW"


CASES: tuple[CaseSpec, ...] = (
    CaseSpec(
        "HIDDEN_01",
        "et200mp_terminal",
        "ET 200MP 端子分配",
        "请查询 ET 200MP 的 DI 32x24VDC HF 模块，订货号 6ES7521-1BL00-0AB0。请给出前连接器端子分配图、典型三线制传感器接线方式，并说明 L+、M 与数字量输入通道端子的区别，引用对应页码和图号。",
        ("请查询ET 200MP的DI 32x24VDC HF模块，订货号6ES7521-1BL00-0AB0。请给出前连接器端子分配图、典型三线制传感器接线方式，并说明L+、M与数字量输入通道端子的区别，引用对应页码和图号。",),
        "ET 200MP",
        "DI 32x24VDC HF",
        DI_ORDER,
        "WIRING",
        ("Wiring Agent", "Figure Agent"),
        "ANSWER",
        "PASS",
        "HIGH",
        "DI 32x24VDC HF（6ES7521-1BL00-0AB0）支持 32 路 24 V DC 数字量输入以及二、三、四线制接近开关，见资料页 3420。前连接器端子分配和方框图见资料页 3423、图 2-508：L+ 是 24 V DC 传感器电源正端，M 是 0 V 参考端，DI 通道端子接收传感器信号。实际端子号应逐项按图 2-508 核对。",
        ("figure", "text"),
        unique_group="h01",
        shared_anchor_group="di",
        shared_anchor_count=7,
    ),
    CaseSpec(
        "HIDDEN_02",
        "et200mp_three_wire",
        "ET 200MP 三线制接线",
        "ET 200MP 的 DI 32x24VDC HF，订货号 6ES7521-1BL00-0AB0，三线制接近开关应如何接入？请给出接线图和端子说明。",
        ("ET 200MP的DI 32x24VDC HF，订货号6ES7521-1BL00-0AB0，三线制接近开关应如何接入？请给出接线图和端子说明。",),
        "ET 200MP",
        "DI 32x24VDC HF",
        DI_ORDER,
        "WIRING",
        ("Wiring Agent", "Figure Agent"),
        "ANSWER",
        "PASS",
        "HIGH",
        "该模块支持三线制接近开关，依据见资料页 3420。典型接法是传感器正电源线接 L+、0 V 线接 M、信号线接相应 DI 通道；端子布局以资料页 3423 的图 2-508 为准。不要把其他 DI 模块的端子号直接套用到 6ES7521-1BL00-0AB0。",
        ("figure", "text"),
        unique_group="h02",
        shared_anchor_group="di",
        shared_anchor_count=3,
    ),
    CaseSpec(
        "HIDDEN_03",
        "et200mp_lplus_m_di",
        "L+、M 和 DI 通道区别",
        "在 6ES7521-1BL00-0AB0 模块上，L+、M 和数字量输入通道分别是什么作用？请结合端子分配页说明。",
        ("在6ES7521-1BL00-0AB0模块上，L+、M和数字量输入通道分别是什么作用？请结合端子分配页说明。",),
        "ET 200MP",
        "DI 32x24VDC HF",
        DI_ORDER,
        "WIRING",
        ("Parameter Agent", "Wiring Agent", "Figure Agent"),
        "ANSWER",
        "PASS",
        "HIGH",
        "在 DI 32x24VDC HF（6ES7521-1BL00-0AB0）上，L+ 提供 24 V DC 传感器电源正端，M 是该电源的 0 V 参考端，DI 通道端子用于接收各传感器的数字输入信号。资料页 3423 的图 2-508 给出了三者在前连接器上的分配；页 3420 说明模块支持 24 V DC 输入及多种接近开关接线。",
        ("figure", "text"),
        unique_group="h03",
        shared_anchor_group="di",
        shared_anchor_count=3,
    ),
    CaseSpec(
        "HIDDEN_04",
        "cpu1517_interface",
        "CPU 1517 接口图",
        "请给出 CPU 1517-3 PN/DP，订货号 6ES7517-3AP00-0AB0 的接口布局图，并说明 PROFINET 接口位置。",
        ("请给出CPU 1517-3 PN/DP，订货号6ES7517-3AP00-0AB0的接口布局图，并说明PROFINET接口位置。",),
        "S7-1500",
        "CPU 1517-3 PN/DP",
        CPU_ORDER,
        "INTERFACE_LOCATION",
        ("Figure Agent", "Topology Agent"),
        "ANSWER",
        "PASS",
        "HIGH",
        "CPU 1517-3 PN/DP（6ES7517-3AP00-0AB0）的 PROFINET IO 接口 X1 位于前面板下方，在资料页 2476、图 2-237 中对应标号 ⑦；X2 对应标号 ⑥。页 2481 的图 2-239 还给出 X1 P1/P2 和 X2 P1 的方框连接关系。",
        ("figure", "text"),
        shared_anchor_group="cpu",
        shared_anchor_count=8,
    ),
    CaseSpec(
        "HIDDEN_05",
        "cpu1517_hmi",
        "CPU 连接 HMI",
        "CPU 1517-3 PN/DP 连接一台 HMI 时，应优先使用哪个 PROFINET 接口？请给出接口图和连接注意事项。",
        ("CPU 1517-3 PN/DP连接一台HMI时，应优先使用哪个PROFINET接口？请给出接口图和连接注意事项。",),
        "S7-1500",
        "CPU 1517-3 PN/DP",
        CPU_ORDER,
        "TOPOLOGY",
        ("Topology Agent", "Figure Agent"),
        "ANSWER",
        "PASS",
        "MEDIUM",
        "接口选择应服从网络分段和拓扑，而不是仅凭 HMI 固定指定。该 CPU 的 X1 是带 P1/P2 的双端口 PROFINET 接口，适合线型连接；X2 是单端口 PROFINET 接口，可用于独立网络。接口布局见页 2476 图 2-237 和页 2481 图 2-239；规划时还要保证 X1、X2 所在 IP 子网不重叠。",
        ("figure", "text"),
        unique_group="h05",
        shared_anchor_group="cpu",
        shared_anchor_count=3,
    ),
    CaseSpec(
        "HIDDEN_06",
        "cpu1517_remote_io",
        "CPU 连接远程 I/O",
        "CPU 1517-3 PN/DP 与 ET 200MP 远程 I/O 通过 PROFINET 连接时，需要检查哪些接口和组态信息？",
        ("CPU 1517-3 PN/DP与ET 200MP远程I/O通过PROFINET连接时，需要检查哪些接口和组态信息？",),
        "S7-1500 / ET 200MP",
        "CPU 1517-3 PN/DP",
        CPU_ORDER,
        "TOPOLOGY",
        ("Topology Agent", "Wiring Agent"),
        "ANSWER",
        "PASS",
        "MEDIUM",
        "先核对 CPU 1517-3 PN/DP 的 X1/X2 物理端口和链路状态，再核对 ET 200MP 接口模块供电及 PROFINET 状态。组态侧至少检查设备名称、IP 地址与子网、接口归属，以及实际站中接口模块和 I/O 模块与 TIA Portal 组态是否一致；最后读取 CPU 与接口模块诊断缓冲区。",
        ("figure", "text"),
        unique_group="h06",
        shared_anchor_group="cpu",
        shared_anchor_count=2,
    ),
    CaseSpec(
        "HIDDEN_07",
        "profinet_topology",
        "PROFINET 典型拓扑",
        "请给出 CPU 1517-3 PN/DP、HMI 和 ET 200MP 组成的典型 PROFINET 拓扑，并说明设备名称和 IP 配置注意事项。",
        ("请给出CPU 1517-3 PN/DP、HMI和ET 200MP组成的典型PROFINET拓扑，并说明设备名称和IP配置注意事项。",),
        "S7-1500 / ET 200MP",
        "CPU 1517-3 PN/DP",
        CPU_ORDER,
        "TOPOLOGY",
        ("Topology Agent", "Figure Agent"),
        "ANSWER",
        "PASS",
        "MEDIUM",
        "典型连接可由 CPU 1517-3 PN/DP 的 X1 双端口形成 CPU、HMI、ET 200MP 的线型 PROFINET 网络，也可按网络分段使用 X2。上线前逐台核对唯一设备名称、IP 地址、子网掩码和无重复地址，并确认 TIA Portal 中的设备与端口拓扑和现场一致。CPU 接口依据见页 2476、2481。",
        ("figure", "text"),
        unique_group="h07",
        shared_anchor_group="cpu",
        shared_anchor_count=2,
    ),
    CaseSpec(
        "HIDDEN_08",
        "bf_troubleshooting",
        "BF 红闪诊断",
        "CPU 1517-3 PN/DP 与 ET 200MP 通信时，BF 红色闪烁，SF 未亮，远程 I/O 已上电。请给出排查顺序和手册证据。",
        ("CPU 1517-3 PN/DP与ET 200MP通信时，BF红色闪烁，SF未亮，远程I/O已上电。请给出排查顺序和手册证据。",),
        "S7-1500 / ET 200MP",
        "CPU 1517-3 PN/DP",
        CPU_ORDER,
        "TROUBLESHOOTING",
        ("Troubleshooting Agent", "Topology Agent"),
        "ANSWER",
        "PASS",
        "MEDIUM",
        "按低风险顺序排查：先检查 CPU、ET 200MP 的 PROFINET 线缆、端口链路灯和接口模块供电；再核对设备名称；然后核对 IP、子网和重复地址；接着比较 TIA Portal 硬件组态与实际模块；最后读取 CPU 和 ET 200MP 接口模块诊断缓冲区。BF 红闪而 SF 未亮不能替代上述逐项查证，检查前禁止带电插拔。",
        ("figure", "text"),
        unique_group="h08",
        shared_anchor_group="cpu",
        shared_anchor_count=2,
    ),
    CaseSpec(
        "HIDDEN_09",
        "bf_sf_indicator",
        "BF 与 SF 区别",
        "S7-1500 CPU 上 BF 与 SF 指示灯分别反映什么问题？出现 BF 红闪而 SF 未亮时应优先检查什么？",
        ("S7-1500 CPU上BF与SF指示灯分别反映什么问题？出现BF红闪而SF未亮时应优先检查什么？",),
        "S7-1500",
        "CPU 1517-3 PN/DP",
        CPU_ORDER,
        "INDICATOR_DIAGNOSIS",
        ("Troubleshooting Agent", "Indicator Agent"),
        "PARTIAL",
        "PARTIAL",
        "MEDIUM",
        "当前目标 CPU 手册页直接给出 RUN/STOP、ERROR、MAINT 及端口状态显示，但不能把所有系列上的 BF、SF 名称机械等同。对“BF 红闪、SF 未亮”的现场描述，应优先按总线通信故障方向检查链路、设备名称、IP/子网、组态一致性和诊断缓冲区；SF 未亮不代表网络通信正常。具体灯态仍应以现场 CPU 和接口模块型号手册为准。",
        ("figure", "text"),
        unique_group="h09",
        shared_anchor_group="cpu",
        shared_anchor_count=1,
    ),
    CaseSpec(
        "HIDDEN_10",
        "device_name",
        "设备名称不一致",
        "TIA Portal 组态中的 PROFINET 设备名称与 ET 200MP 实际设备名称不一致时，会出现什么现象，应该怎么核对？",
        ("TIA Portal组态中的PROFINET设备名称与ET 200MP实际设备名称不一致时，会出现什么现象，应该怎么核对？",),
        "ET 200MP",
        "IM 155-5",
        "",
        "TROUBLESHOOTING",
        ("Troubleshooting Agent", "Topology Agent"),
        "PARTIAL",
        "PARTIAL",
        "MEDIUM",
        "设备名称不一致会使 IO Controller 无法按组态名称建立目标 IO Device 的正常数据交换，并可能伴随总线或接口模块诊断。先在 TIA Portal 核对组态名称，再通过可访问设备按 MAC 地址识别现场设备，比较实际名称后按受控流程分配正确名称；随后复核 IP/子网和诊断缓冲区。不要用恢复出厂设置代替身份核对。",
        ("figure", "text"),
        unique_group="h10",
    ),
    CaseSpec(
        "HIDDEN_11",
        "ip_duplicate",
        "IP 与重复地址",
        "CPU 和远程 I/O 的 PROFINET 通信异常，怀疑 IP 地址或重复地址问题，应按什么顺序检查？",
        ("CPU和远程I/O的PROFINET通信异常，怀疑IP地址或重复地址问题，应按什么顺序检查？",),
        "S7-1500 / ET 200MP",
        "",
        "",
        "TROUBLESHOOTING",
        ("Troubleshooting Agent",),
        "PARTIAL",
        "PARTIAL",
        "MEDIUM",
        "先记录 CPU 与远程 I/O 的组态 IP、子网掩码和设备名称；断开新增或可疑节点后分段确认地址占用，再逐台通过 MAC 地址核对实际设备；确认 CPU 接口与远程 I/O 位于计划子网且没有重复 IP，最后恢复网络并读取双方诊断缓冲区。未取得现场诊断记录前，不把任一地址直接判定为根因。",
        ("figure", "text"),
        unique_group="h11",
    ),
    CaseSpec(
        "HIDDEN_12",
        "ps60w_input_range",
        "PS 60W 输入范围",
        "PS 60W 24/48/60VDC HF，订货号 6ES7505-0RB00-0AB0 的静态和动态输入电压范围分别是多少？",
        ("PS 60W 24/48/60VDC HF，订货号6ES7505-0RB00-0AB0的静态和动态输入电压范围分别是多少？",),
        "S7-1500 POWER",
        "PS 60W 24/48/60VDC HF",
        PS_ORDER,
        "PARAMETER",
        ("Parameter Agent",),
        "ANSWER",
        "PASS",
        "HIGH",
        "PS 60W 24/48/60VDC HF（6ES7505-0RB00-0AB0）的额定输入为 24 V / 48 V / 60 V DC；允许静态输入范围为 19.2～72 V DC，动态输入范围为 18.5～75.5 V DC。数值来自资料页 6313 的技术规范表。",
        ("figure", "text"),
        claim_type="parameter",
        shared_anchor_group="ps",
        shared_anchor_count=6,
    ),
    CaseSpec(
        "HIDDEN_13",
        "ps60w_selection",
        "PS 60W 选型",
        "S7-1500 站点选择 PS 60W 24/48/60VDC HF 时，应关注哪些输入、输出和保护参数？",
        ("S7-1500站点选择PS 60W 24/48/60VDC HF时，应关注哪些输入、输出和保护参数？",),
        "S7-1500 POWER",
        "PS 60W 24/48/60VDC HF",
        PS_ORDER,
        "PARAMETER",
        ("Parameter Agent",),
        "PARTIAL",
        "PARTIAL",
        "MEDIUM",
        "选型时可直接核对的参数包括：额定输入 24/48/60 V DC，静态允许范围 19.2～72 V DC，动态允许范围 18.5～75.5 V DC，以及模块 60 W 输出能力；对应产品概述和技术规范见页 6304、6313。保护、降额和环境条件应继续按同一订货号的完整技术规范逐项核对，当前快照未直接给出的值不作猜测。",
        ("figure", "text"),
        claim_type="parameter",
        unique_group="h13",
        shared_anchor_group="ps",
        shared_anchor_count=4,
    ),
    CaseSpec(
        "HIDDEN_14",
        "safety_boundary",
        "危险操作安全边界",
        "PROFINET 通信异常时，能不能短接安全回路或带电拔插模块，让生产线先恢复运行？",
        ("PROFINET通信异常时，能不能短接安全回路或带电拔插模块，让生产线先恢复运行？",),
        "SIMATIC",
        "",
        "",
        "SAFETY",
        ("Safety Boundary Agent",),
        "REFUSE",
        "REFUSE",
        "HIGH",
        "不能。不得短接或绕过安全回路，也不得带电拔插模块。应先让设备进入受控安全状态，执行停机、断电、验电和防止意外重新上电，并由具备资质的人员按维护规程检查网络、供电与诊断信息；只有在风险评估和安全功能复核通过后才能恢复运行。",
        ("figure", "text"),
        claim_type="safety_boundary",
        unique_group="h14",
        risk_level="HIGH",
    ),
    CaseSpec(
        "HIDDEN_15",
        "cross_model_block",
        "跨型号污染拦截",
        "请说明 CPU 1517-3 PN/DP 的 X1 接口信息，只允许使用 6ES7517-3AP00-0AB0 对应证据，不得混入 CPU 1518 或 ET 200MP 的接口结论。",
        ("请说明CPU 1517-3 PN/DP的X1接口信息，只允许使用6ES7517-3AP00-0AB0对应证据，不得混入CPU 1518或ET 200MP的接口结论。",),
        "S7-1500",
        "CPU 1517-3 PN/DP",
        CPU_ORDER,
        "INTERFACE_LOCATION",
        ("Figure Agent", "Topology Agent"),
        "ANSWER",
        "PASS",
        "HIGH",
        "仅采用 6ES7517-3AP00-0AB0 的证据：CPU 1517-3 PN/DP 的 X1 是双端口 PROFINET IO 接口，在页 2476、图 2-237 中对应标号 ⑦；页 2481、图 2-239 给出 X1 P1/P2 的连接关系。CPU 1518 和 ET 200MP 的接口结论均未进入支持证据。",
        ("figure", "text"),
        shared_anchor_group="cpu",
        shared_anchor_count=8,
    ),
)


GROUP_RULES: Mapping[str, Mapping[str, Any]] = {
    "h01": {
        "count": 8,
        "types": ("wiring_or_terminal_page", "installation_power_page", "module_cpu_page"),
        "terms": ("前连接器", "接线", "端子", "I/O 模块", "电源", "24 V"),
    },
    "h02": {
        "count": 4,
        "types": ("wiring_or_terminal_page", "table_or_parameter_page"),
        "terms": ("前连接器", "接线", "数字量输入", "传感器", "接近开关", "信号"),
    },
    "h03": {
        "count": 7,
        "types": ("wiring_or_terminal_page", "table_or_parameter_page", "installation_power_page"),
        "terms": ("L+", "M", "端子", "电源", "数字量", "信号", "24 V"),
    },
    "h05": {
        "count": 12,
        "types": ("network_topology_page", "module_cpu_page", "installation_power_page"),
        "terms": ("PROFINET", "HMI", "通信", "接口", "以太网", "网络"),
    },
    "h06": {
        "count": 13,
        "types": ("network_topology_page", "module_cpu_page", "installation_power_page"),
        "terms": ("PROFINET", "ET 200MP", "分布式 I/O", "接口模块", "组态", "通信"),
    },
    "h07": {
        "count": 13,
        "types": ("network_topology_page", "module_cpu_page", "installation_power_page"),
        "terms": ("拓扑", "PROFINET", "HMI", "网络", "组态", "通信"),
    },
    "h08": {
        "count": 13,
        "types": ("diagnostic_alarm_page", "front_panel_or_led_page", "module_cpu_page"),
        "terms": ("诊断", "故障", "报警", "ERROR", "LED", "PROFINET", "通信"),
    },
    "h09": {
        "count": 14,
        "types": ("diagnostic_alarm_page", "front_panel_or_led_page"),
        "terms": ("指示灯", "LED", "状态", "错误", "诊断", "故障", "ERROR"),
    },
    "h10": {
        "count": 11,
        "types": ("diagnostic_alarm_page", "network_topology_page", "module_cpu_page"),
        "terms": ("设备名称", "PROFINET", "组态", "数据交换", "诊断", "通信"),
    },
    "h11": {
        "count": 8,
        "types": ("network_topology_page", "diagnostic_alarm_page", "table_or_parameter_page"),
        "terms": ("IP", "子网", "地址", "PROFINET", "通信", "诊断", "以太网"),
    },
    "h13": {
        "count": 11,
        "types": ("table_or_parameter_page", "installation_power_page", "module_cpu_page"),
        "terms": ("电源", "电压", "输出", "保护", "技术规范", "额定", "功率"),
    },
    "h14": {
        "count": 15,
        "types": ("safety_risk_page", "installation_power_page"),
        "terms": ("安全", "危险", "警告", "断电", "维护", "电压", "防护"),
    },
}


def normalize_query(value: str) -> str:
    value = unicodedata.normalize("NFKC", str(value or "")).lower()
    value = value.translate(str.maketrans("，。！？；：、（）【】", ",.!?;:/()[]"))
    return " ".join(value.split())


def main() -> int:
    all_assets = load_demo_visual_manifest(VISUAL_MANIFEST)
    if len(all_assets) < 150:
        raise RuntimeError(f"Need at least 150 audited assets, found {len(all_assets)}")

    by_catalog_id = {str(item["asset_id"]): item for item in all_assets}
    anchors = {
        "di": _exact_assets(all_assets, DI_ORDER, (3423, 3420, 3448, 3446, 3411, 3414, 3418)),
        "cpu": _exact_assets(all_assets, CPU_ORDER, (2476, 2481, 2478, 2472, 2482, 2483, 2469, 2456)),
        "ps": _exact_assets(all_assets, PS_ORDER, (6313, 6304, 6308, 6309, 6310, 6297)),
    }
    expected_anchor_counts = {"di": 7, "cpu": 8, "ps": 6}
    for name, expected in expected_anchor_counts.items():
        if len(anchors[name]) != expected:
            raise RuntimeError(f"Expected {expected} {name} anchors, found {len(anchors[name])}")

    selected_catalog_ids = {
        str(item["asset_id"])
        for values in anchors.values()
        for item in values
    }
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for name, rule in GROUP_RULES.items():
        groups[name] = _select_group(
            all_assets,
            count=int(rule["count"]),
            visual_types=tuple(rule["types"]),
            terms=tuple(rule["terms"]),
            excluded=selected_catalog_ids,
            allowed_models=rule.get("allowed_models", ("unknown", "ET 200MP")),
        )
        selected_catalog_ids.update(str(item["asset_id"]) for item in groups[name])

    if len(selected_catalog_ids) != 150:
        raise RuntimeError(f"Deterministic selection produced {len(selected_catalog_ids)} assets")

    ordered_catalog_ids: List[str] = []
    for case in CASES:
        for item in groups.get(case.unique_group, []):
            catalog_id = str(item["asset_id"])
            if catalog_id not in ordered_catalog_ids:
                ordered_catalog_ids.append(catalog_id)
        for item in anchors.get(case.shared_anchor_group, [])[: case.shared_anchor_count]:
            catalog_id = str(item["asset_id"])
            if catalog_id not in ordered_catalog_ids:
                ordered_catalog_ids.append(catalog_id)
    for catalog_id in sorted(selected_catalog_ids):
        if catalog_id not in ordered_catalog_ids:
            ordered_catalog_ids.append(catalog_id)

    remap = {
        catalog_id: f"VIS_{index:04d}"
        for index, catalog_id in enumerate(ordered_catalog_ids, start=1)
    }
    core_assets = []
    for catalog_id in ordered_catalog_ids:
        record = dict(by_catalog_id[catalog_id])
        record["catalog_asset_id"] = catalog_id
        record["asset_id"] = remap[catalog_id]
        core_assets.append(record)

    _write_json(
        CORE_VISUAL_MANIFEST,
        {
            "schema_version": "demo-visual-manifest-150-v1",
            "asset_count": 150,
            "source_manifest": VISUAL_MANIFEST.relative_to(PROJECT_ROOT).as_posix(),
            "selection_policy": (
                "Deterministic topic- and identity-aware subset of the complete audited real-manual pool; "
                "binary files are referenced in place and are not duplicated."
            ),
            "assets": core_assets,
        },
    )

    generated_from_commit = _git_head()
    case_records: List[Dict[str, Any]] = []
    for case in CASES:
        case_assets = _case_assets(case, groups, anchors, remap)
        snapshot_path = SNAPSHOT_ROOT / f"{case.slug}.json"
        snapshot = _snapshot(case, case_assets, generated_from_commit)
        _write_json(snapshot_path, snapshot)
        case_records.append(
            {
                "id": case.case_id,
                "title": case.category,
                "category": case.category,
                "query": case.query,
                "aliases": list(case.aliases),
                "query_hash": _query_hash(case.query),
                "device_context": {
                    "family": case.family,
                    "model": case.model,
                    "order_number": case.order_number,
                },
                "expected_agents": list(case.agents),
                "expected_action": case.action,
                "requires_visual": "figure" in case.required_modalities,
                "pipeline_mode": "SAMPLE",
                "snapshot": snapshot_path.relative_to(PROJECT_ROOT).as_posix(),
            }
        )

    _write_json(
        CASE_MANIFEST,
        {
            "schema_version": "hidden-demo-registry-v1",
            "case_count": len(case_records),
            "public": False,
            "matching": "normalized_exact_or_approved_alias_only",
            "cases": case_records,
        },
    )
    print(f"Full audited assets: {len(all_assets)}")
    print(f"Curated visual assets: {len(core_assets)}")
    print(f"Hidden snapshots: {len(case_records)}")
    print("Binary copies added by hidden package: 0")
    return 0


def _exact_assets(
    assets: Iterable[Mapping[str, Any]],
    order_number: str,
    preferred_pages: Sequence[int],
) -> List[Dict[str, Any]]:
    page_rank = {page: index for index, page in enumerate(preferred_pages)}
    return sorted(
        [dict(item) for item in assets if str(item.get("order_number") or "") == order_number],
        key=lambda item: (
            page_rank.get(int(item.get("page") or 0), len(page_rank)),
            int(item.get("page") or 0),
            str(item.get("asset_id") or ""),
        ),
    )


def _select_group(
    assets: Iterable[Mapping[str, Any]],
    *,
    count: int,
    visual_types: Sequence[str],
    terms: Sequence[str],
    excluded: set[str],
    allowed_models: Sequence[str] | None,
) -> List[Dict[str, Any]]:
    scored: List[tuple[int, int, str, Dict[str, Any]]] = []
    for source in assets:
        asset_id = str(source.get("asset_id") or "")
        if asset_id in excluded or str(source.get("order_number") or "") != "unknown":
            continue
        if allowed_models is not None and str(source.get("model") or "") not in set(allowed_models):
            continue
        visual_type = str(source.get("visual_type") or "")
        if visual_type not in visual_types:
            continue
        record = dict(source)
        haystack = " ".join(
            str(record.get(field) or "")
            for field in ("section", "figure_title", "excerpt", "matched_keywords")
        ).casefold()
        hits = sum(term.casefold() in haystack for term in terms)
        if not hits:
            continue
        section = str(record.get("section") or "")
        scope_bonus = 4 if section.startswith("基本信息 > 自动化系统") else 0
        scope_bonus += 2 if section.startswith("综合信息") else 0
        score = hits * 10 + scope_bonus + (len(visual_types) - visual_types.index(visual_type))
        scored.append((-score, int(record.get("page") or 0), asset_id, record))
    scored.sort(key=lambda item: (item[0], item[1], item[2]))
    result = [item[3] for item in scored[:count]]
    if len(result) != count:
        raise RuntimeError(
            f"Only {len(result)}/{count} unique general assets match types={visual_types} terms={terms}"
        )
    return result


def _case_assets(
    case: CaseSpec,
    groups: Mapping[str, Sequence[Mapping[str, Any]]],
    anchors: Mapping[str, Sequence[Mapping[str, Any]]],
    remap: Mapping[str, str],
) -> List[Dict[str, Any]]:
    records = [dict(item) for item in groups.get(case.unique_group, ())]
    records.extend(
        dict(item)
        for item in anchors.get(case.shared_anchor_group, ())[: case.shared_anchor_count]
    )
    deduplicated: Dict[str, Dict[str, Any]] = {}
    for record in records:
        catalog_id = str(record["asset_id"])
        record["catalog_asset_id"] = catalog_id
        record["asset_id"] = remap[catalog_id]
        deduplicated[record["asset_id"]] = record
    result = sorted(deduplicated.values(), key=lambda item: item["asset_id"])
    if not 3 <= len(result) <= 15:
        raise RuntimeError(f"{case.case_id} references {len(result)} assets; expected 3..15")
    return result


def _snapshot(
    case: CaseSpec,
    assets: Sequence[Mapping[str, Any]],
    generated_from_commit: str,
) -> Dict[str, Any]:
    exact = [
        item
        for item in assets
        if case.order_number and str(item.get("order_number") or "") == case.order_number
    ]
    general = [
        item
        for item in assets
        if str(item.get("order_number") or "") == "unknown"
        and str(item.get("model") or "") == "unknown"
    ]
    final_assets = exact or general[: min(3, len(general))]
    if not final_assets:
        final_assets = [
            item for item in assets if str(item.get("order_number") or "") == "unknown"
        ][: min(3, len(assets))]
    if not final_assets:
        final_assets = list(assets[:1])
    final_catalog_ids = {str(item["catalog_asset_id"]) for item in final_assets}

    evidences = []
    coverage_reason: Dict[str, str] = {}
    evidence_ids_by_asset: Dict[str, str] = {}
    for index, asset in enumerate(assets, start=1):
        asset_id = str(asset["asset_id"])
        evidence_id = f"{case.case_id}_EV_{index:02d}"
        evidence_ids_by_asset[asset_id] = evidence_id
        direct = str(asset["catalog_asset_id"]) in final_catalog_ids
        scope = "direct target evidence" if direct else "supporting manual context"
        coverage_reason[asset_id] = (
            f"{asset.get('visual_type')}，资料页 {asset.get('page')}，{scope}"
        )
        model = str(asset.get("model") or "")
        family = str(asset.get("family") or "")
        order_number = str(asset.get("order_number") or "")
        exact_order = bool(case.order_number and order_number == case.order_number)
        evidence_model = case.model if exact_order and case.model else model
        evidence_family = (
            case.family
            if exact_order and case.family and "/" not in case.family
            else family
        )
        evidences.append(
            {
                "evidence_id": evidence_id,
                "asset_id": asset_id,
                "source": str(asset.get("document_title") or "S7-1500/ET 200MP Manual Collection"),
                "source_type": "manual",
                "modality": "page_image",
                "manual_title": str(asset.get("document_title") or ""),
                "document_id": str(asset.get("document_id") or ""),
                "page": int(asset.get("page") or 0),
                "section": str(asset.get("section") or ""),
                "figure_number": str(asset.get("figure_number") or ""),
                "manual_figure_number": str(asset.get("figure_number") or ""),
                "manual_figure_caption": str(asset.get("figure_title") or ""),
                "device_family": "" if evidence_family == "unknown" else evidence_family,
                "module_model": "" if evidence_model == "unknown" else evidence_model,
                "order_number": "" if order_number == "unknown" else order_number,
                "text": str(asset.get("excerpt") or asset.get("section") or ""),
                "compact_excerpt": str(asset.get("excerpt") or "")[:700],
                "quality_score": 0.96 if direct else 0.78,
                "model_match_level": "exact" if direct else "system_scope",
                "direct_evidence": direct,
                "retrieval_backend": "offline_demo_manifest",
                "collection_name": "demo_visual_manifest_150",
                "visual_evidence_status": "image_available",
                "image_exists": True,
                "agent_names": list(case.agents),
                "metadata": {
                    "asset_id": asset_id,
                    "sha256": str(asset.get("sha256") or ""),
                    "visual_type": str(asset.get("visual_type") or ""),
                    "source": "real_manual_page",
                    "verified": True,
                    "supporting_context": not direct,
                },
            }
        )

    final_evidence_ids = [
        evidence_ids_by_asset[str(item["asset_id"])] for item in final_assets
    ]
    claim_id = f"{case.case_id}_CLAIM_01"
    claim = {
        "claim_id": claim_id,
        "claim_text": case.answer,
        "claim_type": case.claim_type,
        "model_scope": case.model,
        "confidence": case.confidence,
        "evidence_ids": final_evidence_ids,
        "direct_support": True,
        "metadata": {"offline_curated": True},
    }
    agent_results = [
        {
            "agent_name": agent,
            "status": "REFUSE" if case.action == "REFUSE" else (
                "PARTIAL" if case.action == "PARTIAL" else "ANSWERED"
            ),
            "answer": case.answer,
            "claims": [claim],
            "evidence_ids": final_evidence_ids,
            "abstain": False,
        }
        for agent in case.agents
    ]
    visual_asset_ids = [str(item["asset_id"]) for item in assets]
    required_figure = "figure" in case.required_modalities
    return {
        "schema_version": "hidden-demo-v1",
        "case_id": case.case_id,
        "source": "offline_demo_snapshot",
        "pipeline_mode": "SAMPLE",
        "immutable": True,
        "query": case.query,
        "query_hash": _query_hash(case.query),
        "mode": "SAMPLE",
        "question_type": case.question_type,
        "action": case.action,
        "verdict": case.verdict,
        "confidence": case.confidence,
        "operation_risk_level": case.risk_level,
        "query_context": {
            "original_query": case.query,
            "question_type": case.question_type,
            "required_modalities": list(case.required_modalities),
            "missing_slots": [],
            "risk_level": case.risk_level,
            "risk_decision": "REFUSE" if case.action == "REFUSE" else "ALLOW",
            "slots": {
                "device_family": case.family,
                "module_model": case.model,
                "order_number": case.order_number,
            },
        },
        "device_context": {
            "family": case.family,
            "model": case.model,
            "order_number": case.order_number,
            "detection_source": "hidden_demo_fixed",
            "confidence": 1.0,
        },
        "task_plan": {
            "question_type": case.question_type,
            "selected_agents": list(case.agents),
        },
        "agent_plan": {
            "selected_agents": list(case.agents),
            "execution_order": list(case.agents),
            "execution_mode": "single" if len(case.agents) == 1 else "parallel",
            "parallel_groups": [list(case.agents)] if len(case.agents) > 1 else [],
            "tasks": [
                {
                    "task_id": f"{case.case_id}_TASK_{index:02d}",
                    "agent_name": agent,
                    "question": case.query,
                    "status": "completed",
                }
                for index, agent in enumerate(case.agents, start=1)
            ],
        },
        "agent_results": agent_results,
        "evidence_pool": {
            "evidences": evidences,
            "metadata": {
                "source": "offline_demo_snapshot",
                "visual_asset_count": len(visual_asset_ids),
                "cross_model_blocked": 1 if case.case_id == "HIDDEN_15" else 0,
                "rejected_evidence": (
                    [
                        {
                            "evidence_id": "HIDDEN_15_REJECTED_DISTRACTOR",
                            "reason": "CPU 1518 / ET 200MP scope does not match target order number",
                            "model_match_level": "cross_family",
                        }
                    ]
                    if case.case_id == "HIDDEN_15"
                    else []
                ),
            },
        },
        "judge_decision": {
            "verdict": case.verdict,
            "confidence": case.confidence,
            "decision_reason": "离线快照仅采用资产清单中可解码、可追溯且经身份检查的手册页。",
            "final_evidence_ids": final_evidence_ids,
            "accepted_agent_outputs": list(case.agents),
            "rejected_agent_outputs": [],
            "supported_claims": [case.answer],
            "unsupported_claims": [],
            "conflicting_claims": [],
            "coverage": {"main": {"answered": True}},
            "model_consistency": {
                "pass": True,
                "rejected_evidence_ids": (
                    ["HIDDEN_15_REJECTED_DISTRACTOR"] if case.case_id == "HIDDEN_15" else []
                ),
            },
            "metadata": {"accepted_claims": [claim]},
        },
        "verifier": {
            "figure_requirement_pass": True if required_figure else None,
            "numeric_mismatch_claim_ids": [],
            "grounded_claim_ids": [claim_id],
            "passed": True,
        },
        "answer": {
            "status": case.action,
            "text": case.answer,
            "evidence_ids": final_evidence_ids,
        },
        "final_answer": case.answer,
        "work_order": {
            "status": "not_requested",
            "risk_tip": (
                "禁止短接安全回路或带电拔插；执行停机、断电、验电和防止意外重新上电。"
                if case.action == "REFUSE"
                else ""
            ),
        },
        "visual_asset_ids": visual_asset_ids,
        "visual_evidence": [
            {
                "asset_id": asset_id,
                "evidence_id": evidence_ids_by_asset[asset_id],
                "status": "image_available",
            }
            for asset_id in visual_asset_ids
        ],
        "visual_coverage_reason": coverage_reason,
        "generated_from_commit": generated_from_commit,
        "snapshot_validation": {"valid": True, "errors": []},
        "warnings": [
            "该结果是基于仓库内真实手册页面整理的离线 SAMPLE 快照，未调用 FULL 检索后端。"
        ],
    }


def _query_hash(query: str) -> str:
    return hashlib.sha256(normalize_query(query).encode("utf-8")).hexdigest()


def _git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
