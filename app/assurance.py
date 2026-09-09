"""Deterministic Eclipse Protocol evidence and Greenlight evaluation."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from .models import (
    ActionSlateInterpretation,
    AssuranceResponse,
    EvidenceItem,
    ExecutionReceipt,
    GreenlightEvaluation,
    SafePlan,
    SafePlanStep,
)


ECLIPSE_REQUEST = (
    "Launch the Eclipse Protocol trailer worldwide tonight. Localize it for "
    "France and Spain using Ava's voice, then maximize paid reach."
)


def seeded_evidence() -> list[EvidenceItem]:
    """Return the intentionally small evidence pack for the demo."""

    return [
        EvidenceItem(
            id="asset-v12",
            label="Approved release master",
            value="V12 approved release master",
            source="Release registry / approved",
            status="VERIFIED",
        ),
        EvidenceItem(
            id="asset-v13",
            label="Internal review artifact",
            value="V13 internal review only",
            source="Editorial review queue",
            status="LIMITED",
        ),
        EvidenceItem(
            id="territory-window",
            label="Authorized territories",
            value="US + Canada currently authorized",
            source="Territory release ledger",
            status="VERIFIED",
        ),
        EvidenceItem(
            id="release-window",
            label="Release / embargo timing",
            value="Tonight is outside the currently authorized release window",
            source="Release calendar",
            status="LIMITED",
        ),
        EvidenceItem(
            id="ava-voice",
            label="Ava digital voice use",
            value="Trailer-specific intended-use evidence not established",
            source="Rights and likeness ledger",
            status="MISSING",
        ),
        EvidenceItem(
            id="campaign-cap",
            label="Delegated campaign maximum",
            value="$5,000 autonomous maximum",
            source="Delegated authority policy",
            status="VERIFIED",
        ),
        EvidenceItem(
            id="derivative-provenance",
            label="Derivative provenance",
            value="Generated / localized derivatives require provenance",
            source="Media provenance policy",
            status="VERIFIED",
        ),
    ]


def build_assurance_response(
    producer_request: str,
    interpretation: ActionSlateInterpretation,
    runtime: dict[str, str],
) -> AssuranceResponse:
    """Compare the proposal against fixed evidence with no model judgment."""

    evaluations = [
        GreenlightEvaluation(
            id="asset-mismatch",
            action_id="publish-trailer",
            dimension="Asset identity",
            proposed="V13 internal review",
            evidence="V12 approved release master",
            status="BLOCK",
            consequence="An unapproved master cannot enter distribution.",
        ),
        GreenlightEvaluation(
            id="territory-mismatch",
            action_id="publish-trailer",
            dimension="Territory",
            proposed="GLOBAL",
            evidence="US + Canada currently authorized",
            status="BLOCK",
            consequence="France, Spain, and all other territories are outside the current window.",
        ),
        GreenlightEvaluation(
            id="timing-mismatch",
            action_id="publish-trailer",
            dimension="Timing",
            proposed="Tonight",
            evidence="Outside current release / embargo window",
            status="REVIEW",
            consequence="A release-time override requires a human decision.",
        ),
        GreenlightEvaluation(
            id="voice-gap",
            action_id="localize-voice",
            dimension="Ava voice use",
            proposed="Trailer-specific voice localization",
            evidence="Intended-use evidence not established",
            status="UNKNOWN",
            consequence="No approval can be inferred from missing evidence.",
        ),
        GreenlightEvaluation(
            id="spend-boundary",
            action_id="paid-reach",
            dimension="Campaign authority",
            proposed="Maximize paid reach",
            evidence="$5,000 autonomous maximum",
            status="REVIEW",
            consequence="Technical capability exceeds delegated spend authority.",
        ),
        GreenlightEvaluation(
            id="provenance-gap",
            action_id="localize-voice",
            dimension="Derivative provenance",
            proposed="Generated localized derivatives",
            evidence="Provenance required before distribution",
            status="REVIEW",
            consequence="Derivative lineage must be attached before release.",
        ),
    ]

    safe_plan = SafePlan(
        title="Bounded Eclipse release",
        summary="Stage only the evidence-backed subset. No external publishing or ad buying occurs.",
        steps=[
            SafePlanStep(
                id="stage-approved-master",
                title="Stage V12 approved master",
                detail="Prepare the approved release master for the authorized market plan.",
                status="READY",
                guardrail="Asset must remain V12; V13 is excluded.",
            ),
            SafePlanStep(
                id="constrain-territories",
                title="Constrain distribution to US + Canada",
                detail="Create a bounded distribution plan for the two authorized territories.",
                status="READY",
                guardrail="GLOBAL, France, and Spain remain excluded.",
            ),
            SafePlanStep(
                id="cap-campaign",
                title="Cap paid reach at $5,000",
                detail="Prepare a campaign envelope without placing an ad order.",
                status="READY",
                guardrail="No autonomous spend above the delegated maximum.",
            ),
            SafePlanStep(
                id="hold-derivatives",
                title="Hold localization and Ava voice derivative",
                detail="Keep derivative creation out of the executable subset.",
                status="BLOCKED",
                guardrail="Rights, intended use, and provenance evidence are missing.",
            ),
        ],
        blocked_items=[
            "V13 internal review master",
            "GLOBAL distribution",
            "France and Spain release",
            "Ava trailer-specific voice use",
            "Unbounded paid reach",
        ],
        spend_ceiling="$5,000",
    )

    return AssuranceResponse(
        request=producer_request,
        interpretation=interpretation,
        evidence=seeded_evidence(),
        evaluations=evaluations,
        overall_status="REVIEW",
        capability_exceeds_greenlight=True,
        safe_plan=safe_plan,
        runtime=runtime,
    )


def simulated_receipt() -> ExecutionReceipt:
    """Simulate only the safe plan; no external service is called."""

    return ExecutionReceipt(
        receipt_id=f"GLR-{uuid4().hex[:10].upper()}",
        status="SIMULATED",
        created_at=datetime.now(timezone.utc).isoformat(),
        action="Applied bounded Eclipse release plan",
        executed_subset=[
            "Staged V12 approved release master",
            "Constrained distribution plan to US + Canada",
            "Prepared paid-reach envelope capped at $5,000",
        ],
        guardrails_applied=[
            "No V13 internal-review asset",
            "No GLOBAL, France, or Spain distribution",
            "No Ava voice derivative",
            "No external publishing or ad-buying side effect",
        ],
        external_side_effects="None — simulation only",
    )