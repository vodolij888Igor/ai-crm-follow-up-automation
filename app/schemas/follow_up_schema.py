"""
Pydantic models for CRM follow-up generation.

These models enforce shape and types at the API boundary so requests and responses
stay consistent and self-documenting for clients and integrators.
"""

from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class FollowUpRequest(BaseModel):
    """Simulated CRM lead payload sent as JSON (no live CRM connection in v1)."""

    contact_name: str = Field(..., min_length=1, description="Full name of the contact.")
    contact_email: EmailStr = Field(..., description="Contact email used for follow-up context.")
    company_name: str = Field(..., min_length=1, description="Company or account name.")
    lead_status: str = Field(
        ...,
        min_length=1,
        description="Pipeline stage or disposition (e.g. interested, qualified, cold).",
    )
    last_contact_days_ago: int = Field(
        ...,
        ge=0,
        description="Days since last outreach; drives urgency in the plan.",
    )
    customer_need: str = Field(
        ...,
        min_length=1,
        description="Short description of what the prospect is trying to solve.",
    )
    budget_usd: float | int = Field(
        ...,
        ge=0,
        description="Stated or inferred budget in USD (used for prioritization heuristics).",
    )
    preferred_tone: Literal["professional", "friendly", "concise", "formal"] = Field(
        default="professional",
        description="Desired tone for the drafted message.",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "contact_name": "John Smith",
                    "contact_email": "john@example.com",
                    "company_name": "Smith Roofing",
                    "lead_status": "interested",
                    "last_contact_days_ago": 5,
                    "customer_need": "Wants to automate customer follow-up emails and lead tracking.",
                    "budget_usd": 2500,
                    "preferred_tone": "professional",
                }
            ]
        }
    }


class FollowUpResponse(BaseModel):
    """Structured follow-up plan from OpenAI (validated at the API boundary)."""

    contact_name: str = Field(..., description="Echo of the contact for traceability.")
    priority: Literal["low", "medium", "high"] = Field(
        ...,
        description="Suggested urgency for the next touch.",
    )
    follow_up_type: str = Field(
        ...,
        description=(
            "Category of follow-up (e.g. sales_follow_up, re_engagement, payment_follow_up, "
            "onboarding_follow_up, support_follow_up, general_follow_up)."
        ),
    )
    summary: str = Field(..., description="One-line context for humans or downstream AI.")
    suggested_message: str = Field(..., description="Draft message aligned with preferred_tone.")
    recommended_action: str = Field(..., description="Concrete next step for the rep or workflow.")
    reasoning: str = Field(
        ...,
        description="Short justification for priority, type, and recommended action.",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "contact_name": "John Smith",
                    "priority": "high",
                    "follow_up_type": "sales_follow_up",
                    "summary": "John Smith is interested in AI automation for follow-up emails and lead tracking.",
                    "suggested_message": (
                        "Hi John, I wanted to follow up on your interest in automating "
                        "customer follow-up emails and lead tracking..."
                    ),
                    "recommended_action": "Send follow-up email and offer a discovery call.",
                    "reasoning": (
                        "The lead has a clear business need, an available budget, "
                        "and has not been contacted for 5 days."
                    ),
                }
            ]
        }
    }
