"""Typed ActionSlate Cycle 1 request and agent-result models."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


ArgumentProvenance = Literal[
    "USER_EXPLICIT",
    "USER_CONTEXT",
    "AGENT_INFERRED",
    "POLICY_DEFAULT",
    "TOOL_DEFAULT",
    "UNKNOWN",
]


class ConsequentialAction(BaseModel):
    """One action the media agent believes the producer is requesting."""

    action_id: str = Field(description="Stable short identifier for this action.")
    action_type: str = Field(
        description="Normalized action family, such as publish, localize, or promote."
    )
    description: str = Field(description="Plain-language description of the action.")
    arguments: dict[str, Any] = Field(
        description="Exact arguments that make this action consequential."
    )
    argument_provenance: dict[str, ArgumentProvenance] = Field(
        description="How each consequential argument was obtained."
    )
    required_evidence: list[str] = Field(
        description="Evidence dimensions that must support the action."
    )
    uncertainties: list[str] = Field(
        default_factory=list,
        description="Ambiguities or evidence gaps discovered by the agent.",
    )


class ActionSlateInterpretation(BaseModel):
    """Structured Gemini result consumed by the next assurance cycle."""

    request_summary: str = Field(
        description="Short summary of what the producer is trying to accomplish."
    )
    consequential_actions: list[ConsequentialAction] = Field(
        min_length=1,
        description="Ordered actions implied by the producer request.",
    )
    interpretation_notes: list[str] = Field(
        default_factory=list,
        description="Important semantic discoveries made during interpretation.",
    )


class InterpretRequest(BaseModel):
    """API request for the Cycle 1 interpretation endpoint."""

    producer_request: str = Field(min_length=10, max_length=4000)


DecisionStatus = Literal["ALLOW", "REVIEW", "BLOCK", "UNKNOWN"]


class EvidenceItem(BaseModel):
    """A minimum evidence fact used by the deterministic assurance layer."""

    id: str
    label: str
    value: str
    source: str
    status: Literal["VERIFIED", "LIMITED", "MISSING"]


class GreenlightEvaluation(BaseModel):
    """An inspectable comparison between a proposal and evidence."""

    id: str
    action_id: str
    dimension: str
    proposed: str
    evidence: str
    status: DecisionStatus
    consequence: str


class SafePlanStep(BaseModel):
    """A simulated, bounded step extracted from a compound request."""

    id: str
    title: str
    detail: str
    status: Literal["READY", "HOLD", "BLOCKED"]
    guardrail: str


class SafePlan(BaseModel):
    """The executable subset that remains after deterministic evaluation."""

    title: str
    summary: str
    steps: list[SafePlanStep]
    blocked_items: list[str]
    spend_ceiling: str


class ExecutionReceipt(BaseModel):
    """A receipt for a simulated action, never a real publishing call."""

    receipt_id: str
    status: Literal["SIMULATED"]
    created_at: str
    action: str
    executed_subset: list[str]
    guardrails_applied: list[str]
    external_side_effects: str


class AssuranceResponse(BaseModel):
    """Complete assurance response rendered by the one-page client."""

    request: str
    interpretation: ActionSlateInterpretation
    evidence: list[EvidenceItem]
    evaluations: list[GreenlightEvaluation]
    overall_status: DecisionStatus
    capability_exceeds_greenlight: bool
    safe_plan: SafePlan
    receipt: ExecutionReceipt | None = None
    runtime: dict[str, str]


class ExecuteRequest(BaseModel):
    """Request to simulate the already-reviewed safe plan."""

    plan_id: str = "eclipse-safe-plan"