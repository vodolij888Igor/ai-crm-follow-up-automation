"""
CRM follow-up plan generation via OpenAI.

Produces structured JSON aligned with `FollowUpResponse`. Missing configuration or
upstream failures surface as explicit exceptions for the API layer to map to HTTP status codes.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from dotenv import load_dotenv
from openai import APIError, OpenAI

from app.schemas.follow_up_schema import FollowUpRequest, FollowUpResponse

logger = logging.getLogger(__name__)

# Load `.env` early so imports/tests that skip `main` still see variables.
load_dotenv()

ALLOWED_FOLLOW_UP_TYPES = frozenset(
    {
        "sales_follow_up",
        "re_engagement",
        "payment_follow_up",
        "onboarding_follow_up",
        "support_follow_up",
        "general_follow_up",
    }
)
ALLOWED_PRIORITY = frozenset({"low", "medium", "high"})

DEFAULT_MODEL = "gpt-4o-mini"


class MissingOpenAIConfigurationError(Exception):
    """OPENAI_API_KEY is unset or empty; API maps this to HTTP 503."""

    def __init__(self, message: str = "OPENAI_API_KEY is not set or is empty.") -> None:
        self.message = message
        super().__init__(message)


class OpenAIInvocationError(Exception):
    """OpenAI request failed or returned unusable output; API maps this to HTTP 502."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


_SYSTEM_PROMPT = """You are a CRM follow-up assistant for B2B sales and customer success.

Given lead fields (JSON in the user message), analyze urgency, intent, and context.

Respond with ONE JSON object only (no markdown fences). Use exactly these keys:
- contact_name: string (must match the input contact_name exactly)
- priority: one of "low", "medium", "high"
- follow_up_type: one of:
  "sales_follow_up", "re_engagement", "payment_follow_up", "onboarding_follow_up",
  "support_follow_up", "general_follow_up"
- summary: one concise sentence for operators or downstream automation
- suggested_message: email-style draft; honor preferred_tone (professional, friendly, concise, formal)
- recommended_action: single concrete next step for a rep or workflow
- reasoning: 2–4 sentences explaining priority and follow_up_type from the data

Rules:
- Ground reasoning in budget_usd, last_contact_days_ago, lead_status, and customer_need.
- Do not invent private facts; stay within the supplied fields.
- suggested_message should address the contact by first name when natural."""


def _get_api_key() -> str:
    key = os.environ.get("OPENAI_API_KEY")
    if key is None or not str(key).strip():
        raise MissingOpenAIConfigurationError()
    return str(key).strip()


def _model_name() -> str:
    return os.environ.get("OPENAI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


def _lead_payload_dict(payload: FollowUpRequest) -> dict[str, Any]:
    return {
        "contact_name": payload.contact_name,
        "contact_email": str(payload.contact_email),
        "company_name": payload.company_name,
        "lead_status": payload.lead_status,
        "last_contact_days_ago": payload.last_contact_days_ago,
        "customer_need": payload.customer_need,
        "budget_usd": payload.budget_usd,
        "preferred_tone": payload.preferred_tone,
    }


def _normalize_llm_dict(data: dict[str, Any], payload: FollowUpRequest) -> dict[str, Any]:
    """Coerce enums and enforce contact_name echo before Pydantic validation."""
    out = dict(data)
    p = out.get("priority", "medium")
    if p not in ALLOWED_PRIORITY:
        out["priority"] = "medium"
    else:
        out["priority"] = p

    t = out.get("follow_up_type", "general_follow_up")
    if t not in ALLOWED_FOLLOW_UP_TYPES:
        out["follow_up_type"] = "general_follow_up"
    else:
        out["follow_up_type"] = t

    out["contact_name"] = payload.contact_name
    return out


def _extract_message_content(raw: object) -> str:
    if raw is None:
        raise OpenAIInvocationError("OpenAI returned no message content.")
    text = str(raw).strip()
    if not text:
        raise OpenAIInvocationError("OpenAI returned empty message content.")
    return text


def generate_follow_up_plan(payload: FollowUpRequest) -> FollowUpResponse:
    """
    Call OpenAI to produce a follow-up plan matching `FollowUpResponse`.

    Raises:
        MissingOpenAIConfigurationError: when OPENAI_API_KEY is missing (HTTP 503 at API layer).
        OpenAIInvocationError: when the provider fails or output cannot be parsed (HTTP 502).
    """
    api_key = _get_api_key()
    model = _model_name()
    client = OpenAI(api_key=api_key, timeout=60.0)

    user_content = json.dumps(_lead_payload_dict(payload), ensure_ascii=False)

    try:
        completion = client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.35,
        )
    except APIError as exc:
        logger.exception("OpenAI API error: %s", exc)
        raise OpenAIInvocationError(
            "The OpenAI API request failed or returned an error. Try again later."
        ) from exc

    try:
        choice = completion.choices[0]
        content = _extract_message_content(choice.message.content)
        parsed = json.loads(content)
    except (IndexError, KeyError, json.JSONDecodeError, TypeError, ValueError) as exc:
        logger.exception("Failed to parse OpenAI response: %s", exc)
        raise OpenAIInvocationError(
            "OpenAI returned a response that could not be parsed as structured JSON."
        ) from exc

    if not isinstance(parsed, dict):
        raise OpenAIInvocationError("OpenAI returned JSON that is not an object.")

    try:
        normalized = _normalize_llm_dict(parsed, payload)
        return FollowUpResponse.model_validate(normalized)
    except Exception as exc:
        logger.exception("Validation failed for OpenAI output: %s", exc)
        raise OpenAIInvocationError(
            "OpenAI returned JSON that did not match the expected follow-up plan shape."
        ) from exc
