"""Shared fixtures for API tests."""

from __future__ import annotations

import json
from collections.abc import Generator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """HTTP client against the FastAPI app (no live server)."""
    from app.main import app

    with TestClient(app) as tc:
        yield tc


@pytest.fixture
def valid_follow_up_payload() -> dict:
    """Minimal valid body for POST /generate-follow-up."""
    return {
        "contact_name": "John Smith",
        "contact_email": "john@example.com",
        "company_name": "Smith Roofing",
        "lead_status": "interested",
        "last_contact_days_ago": 5,
        "customer_need": "Wants to automate customer follow-up emails and lead tracking.",
        "budget_usd": 2500,
        "preferred_tone": "professional",
    }


def make_chat_completion_json(content: dict) -> MagicMock:
    """Build a mock OpenAI chat completion whose message content is JSON."""
    completion = MagicMock()
    message = MagicMock()
    message.content = json.dumps(content)
    choice = MagicMock()
    choice.message = message
    completion.choices = [choice]
    return completion
