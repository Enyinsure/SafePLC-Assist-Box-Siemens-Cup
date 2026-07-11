#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class AgentStatus(str, Enum):
    ANSWERED = "ANSWERED"
    PARTIAL = "PARTIAL"
    ABSTAIN = "ABSTAIN"
    NEED_MORE_EVIDENCE = "NEED_MORE_EVIDENCE"
    NEED_CLARIFICATION = "NEED_CLARIFICATION"
    REFUSE = "REFUSE"


class ExecutionMode(str, Enum):
    SINGLE = "single"
    PARALLEL = "parallel"
    SERIAL = "serial"
    CLARIFY = "clarify"


class JudgeVerdict(str, Enum):
    PASS = "PASS"
    REVIEW = "REVIEW"
    FAIL = "FAIL"
    CONFLICT = "CONFLICT"
    NEED_CLARIFICATION = "NEED_CLARIFICATION"


class JudgeConfidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    CONFLICT = "CONFLICT"
    NOT_AVAILABLE = "NOT_AVAILABLE"


@dataclass
class SlotResult:
    name: str
    value: str = ""
    source: str = "query"
    confidence: float = 0.0
    required: bool = False


@dataclass
class QueryContext:
    original_query: str
    context: str = ""
    normalized_query: str = ""
    question_type: str = "UNKNOWN"
    slots: Dict[str, SlotResult] = field(default_factory=dict)
    missing_slots: List[str] = field(default_factory=list)
    required_modalities: List[str] = field(default_factory=list)
    risk_level: str = "SAFE"
    risk_decision: str = "ALLOW"
    risk_reason: str = ""
    is_dangerous_operation: bool = False
    expected_output_type: str = "answer"
    clarify_question: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def slot_values(self) -> Dict[str, str]:
        return {name: slot.value for name, slot in self.slots.items() if slot.value}

    def to_dict(self) -> Dict[str, Any]:
        return to_plain_dict(self)


@dataclass
class AgentTask:
    task_id: str
    agent_name: str
    role: str
    query: str
    context: str = ""
    objective: str = ""
    input_slots: Dict[str, str] = field(default_factory=dict)
    required_evidence_types: List[str] = field(default_factory=list)
    tool_names: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentPlan:
    selected_agents: List[str]
    rejected_agents: List[str]
    selection_reason: Dict[str, str]
    execution_mode: str
    task_assignments: Dict[str, AgentTask]
    expected_evidence_types: List[str]
    stop_condition: str
    max_agent_calls: int
    routing_strategy: str = "adaptive"
    execution_order: List[str] = field(default_factory=list)
    parallel_groups: List[List[str]] = field(default_factory=list)
    need_clarification: bool = False
    clarification_prompt: str = ""
    scores: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return to_plain_dict(self)


@dataclass
class AgentObservation:
    tool_name: str
    query: str
    status: str
    evidence_ids: List[str] = field(default_factory=list)
    latency_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentEvidence:
    evidence_id: str
    source: str
    source_type: str
    modality: str
    text: str
    page: Optional[int] = None
    section: str = ""
    figure_id: str = ""
    title: str = ""
    module: str = ""
    order_number: str = ""
    parameter: str = ""
    retrieval_score: float = 0.0
    agent_names: List[str] = field(default_factory=list)
    claim_links: List[str] = field(default_factory=list)
    conflict_with: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def signature(self) -> str:
        fields = [
            self.source.lower().strip(),
            self.source_type.lower().strip(),
            self.modality.lower().strip(),
            str(self.page or ""),
            self.figure_id.lower().strip(),
            self.title.lower().strip(),
            self.text.lower().strip()[:240],
        ]
        return "|".join(fields)


@dataclass
class AgentResult:
    agent_name: str
    task_id: str
    status: str
    answer_fragment: str = ""
    evidence_ids: List[str] = field(default_factory=list)
    confidence: str = "NOT_AVAILABLE"
    assumptions: List[str] = field(default_factory=list)
    missing_information: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    follow_up_request: str = ""
    latency_ms: int = 0
    tool_calls: int = 0
    abstain_reason: str = ""
    observations: List[AgentObservation] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return to_plain_dict(self)


@dataclass
class EvidencePool:
    evidences: List[AgentEvidence] = field(default_factory=list)
    agent_claims: Dict[str, List[str]] = field(default_factory=dict)
    conflicts: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return to_plain_dict(self)


@dataclass
class JudgeDecision:
    accepted_agent_outputs: List[str]
    rejected_agent_outputs: List[str]
    conflict_groups: List[Dict[str, Any]]
    supported_claims: List[str]
    unsupported_claims: List[str]
    conflicting_claims: List[str]
    final_evidence_ids: List[str]
    need_more_evidence: bool
    need_clarification: bool
    final_answer: str
    verdict: str
    confidence: str
    decision_reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return to_plain_dict(self)


@dataclass
class SafePLCResponse:
    query: str
    context: str
    mode: str
    query_context: QueryContext
    agent_plan: AgentPlan
    agent_results: List[AgentResult]
    evidence_pool: EvidencePool
    judge_decision: JudgeDecision
    verifier: Dict[str, Any]
    final_answer: str
    question_type: str = ""
    extracted_slots: Dict[str, str] = field(default_factory=dict)
    missing_slots: List[str] = field(default_factory=list)
    operation_risk_level: str = ""
    action: str = ""
    routing_strategy: str = "adaptive"
    selected_agents: List[str] = field(default_factory=list)
    execution_order: List[str] = field(default_factory=list)
    evidence_items: List[AgentEvidence] = field(default_factory=list)
    supported_claims: List[str] = field(default_factory=list)
    unsupported_claims: List[str] = field(default_factory=list)
    conflicting_claims: List[str] = field(default_factory=list)
    verdict: str = ""
    confidence: str = ""
    total_agent_calls: int = 0
    total_tool_calls: int = 0
    total_latency_ms: int = 0
    generated_at: str = ""
    version: str = "agent_first_v1"
    work_order: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return to_plain_dict(self)


def to_plain_dict(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {k: to_plain_dict(v) for k, v in asdict(value).items()}
    if isinstance(value, dict):
        return {str(k): to_plain_dict(v) for k, v in value.items()}
    if isinstance(value, list):
        return [to_plain_dict(v) for v in value]
    return value
