"""
Follow-up plan generation (placeholder implementation).

v1 uses deterministic rules so the API is stable without calling an LLM.
Replace this module's core logic with an AI provider when you are ready.
"""

from typing import Literal

from app.schemas.follow_up_schema import FollowUpRequest, FollowUpResponse

# Heuristic thresholds — tune or replace when integrating real scoring / AI.
_BUDGET_HIGH_USD = 2000
_DAYS_STALE_FOR_HIGH_PRIORITY = 3


def _normalize_status(status: str) -> str:
    return status.strip().lower()


def _compute_priority(payload: FollowUpRequest) -> tuple[Literal["low", "medium", "high"], str]:
    """
    Returns (priority, reasoning_fragment).

    Simple rule engine: budget + recency + pipeline stage drive urgency.
    """
    status = _normalize_status(payload.lead_status)
    days = payload.last_contact_days_ago
    budget = float(payload.budget_usd)

    if status in ("cold", "lost", "disqualified"):
        return (
            "low",
            f"The lead is marked as '{payload.lead_status}', so urgency is reduced.",
        )

    if budget >= _BUDGET_HIGH_USD and days >= _DAYS_STALE_FOR_HIGH_PRIORITY:
        return (
            "high",
            "The lead has a clear budget signal and has gone several days without contact.",
        )

    if days >= 7 or budget >= _BUDGET_HIGH_USD:
        return (
            "medium",
            "Either budget or time since last touch suggests a timely follow-up.",
        )

    return (
        "medium",
        "Standard follow-up cadence applies based on status and recency.",
    )


def _follow_up_type_for_status(status: str) -> str:
    s = _normalize_status(status)
    if s in ("cold", "nurture"):
        return "nurture"
    if s in ("qualified", "proposal", "negotiation"):
        return "advance_deal"
    return "sales_follow_up"


def _opening_for_tone(first_name: str, tone: str) -> str:
    if tone == "formal":
        return f"Dear {first_name},"
    if tone == "friendly":
        return f"Hi {first_name} — hope you're doing well!"
    if tone == "concise":
        return f"Hi {first_name},"
    return f"Hi {first_name},"


def _build_suggested_message(payload: FollowUpRequest) -> str:
    """Assemble a template draft; real AI would personalize further."""
    first = payload.contact_name.split()[0] if payload.contact_name else "there"
    opening = _opening_for_tone(first, payload.preferred_tone)
    need = payload.customer_need.strip().rstrip(".")
    company = payload.company_name

    # Neutral template — keeps grammar sane whether the need is a fragment or a full sentence.
    body = (
        f"I wanted to follow up with you at {company} about the following: {need}. "
        f"I'd love to share how we can help and answer any questions."
    )
    closing = (
        "Would you have 20 minutes this week for a quick discovery call?"
        if payload.preferred_tone != "concise"
        else "Open to a brief call this week?"
    )
    return f"{opening} {body} {closing}"


def _recommended_action(priority: str, follow_up_type: str) -> str:
    if follow_up_type == "nurture":
        return "Add to a nurture sequence and send a value-focused touchpoint."
    if follow_up_type == "advance_deal":
        return "Schedule a call to align on scope, timeline, and next steps."
    if priority == "high":
        return "Send follow-up email and offer a discovery call."
    return "Send a personalized follow-up and propose a time to connect."


def generate_follow_up_plan(payload: FollowUpRequest) -> FollowUpResponse:
    """
    Produce a follow-up plan from CRM-style fields.

    This is intentionally deterministic for portfolio demos and tests.
    """
    priority, budget_reason = _compute_priority(payload)
    follow_up_type = _follow_up_type_for_status(payload.lead_status)

    need_snippet = payload.customer_need.strip().rstrip(".")
    status_word = _normalize_status(payload.lead_status)
    summary = (
        f"{payload.contact_name} from {payload.company_name} is {status_word}: {need_snippet}."
    )

    suggested = _build_suggested_message(payload)
    action = _recommended_action(priority, follow_up_type)

    days = payload.last_contact_days_ago
    reasoning = (
        f"{budget_reason} Last contact was {days} day(s) ago; "
        f"budget signal is around ${float(payload.budget_usd):,.0f}."
    )

    return FollowUpResponse(
        contact_name=payload.contact_name,
        priority=priority,
        follow_up_type=follow_up_type,
        summary=summary,
        suggested_message=suggested,
        recommended_action=action,
        reasoning=reasoning,
    )
