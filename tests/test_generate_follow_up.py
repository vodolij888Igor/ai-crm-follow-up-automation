"""Tests for POST /generate-follow-up (OpenAI client is always mocked)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from openai import APIError

from app.services.follow_up_service import ALLOWED_FOLLOW_UP_TYPES
from tests.conftest import make_chat_completion_json

ALLOWED_PRIORITIES = frozenset({"low", "medium", "high"})

MOCK_LLM_BODY = {
    "contact_name": "John Smith",
    "priority": "high",
    "follow_up_type": "sales_follow_up",
    "summary": "John Smith from Smith Roofing is interested in automation for follow-up and tracking.",
    "suggested_message": "Hi John, following up on automating follow-up emails and lead tracking at Smith Roofing.",
    "recommended_action": "Send a discovery-call invite within 24 hours.",
    "reasoning": "Budget and clear need justify immediate outreach; last touch was 5 days ago.",
}


@pytest.fixture(autouse=True)
def fake_openai_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure tests never rely on a real key from the developer machine."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-mock-not-real")


@patch("app.services.follow_up_service.OpenAI")
def test_success_returns_200_with_expected_fields(
    _mock_openai_class: MagicMock,
    client,
    valid_follow_up_payload: dict,
) -> None:
    mock_client = _mock_openai_class.return_value
    mock_client.chat.completions.create.return_value = make_chat_completion_json(MOCK_LLM_BODY)

    response = client.post("/generate-follow-up", json=valid_follow_up_payload)

    assert response.status_code == 200
    data = response.json()
    for key in (
        "contact_name",
        "priority",
        "follow_up_type",
        "summary",
        "suggested_message",
        "recommended_action",
        "reasoning",
    ):
        assert key in data, f"missing field: {key}"
        assert isinstance(data[key], str) and len(data[key]) > 0


@patch("app.services.follow_up_service.OpenAI")
def test_priority_is_allowed_value(
    _mock_openai_class: MagicMock,
    client,
    valid_follow_up_payload: dict,
) -> None:
    mock_client = _mock_openai_class.return_value
    mock_client.chat.completions.create.return_value = make_chat_completion_json(MOCK_LLM_BODY)

    response = client.post("/generate-follow-up", json=valid_follow_up_payload)
    assert response.status_code == 200
    assert response.json()["priority"] in ALLOWED_PRIORITIES


@patch("app.services.follow_up_service.OpenAI")
def test_follow_up_type_is_allowed_value(
    _mock_openai_class: MagicMock,
    client,
    valid_follow_up_payload: dict,
) -> None:
    mock_client = _mock_openai_class.return_value
    mock_client.chat.completions.create.return_value = make_chat_completion_json(MOCK_LLM_BODY)

    response = client.post("/generate-follow-up", json=valid_follow_up_payload)
    assert response.status_code == 200
    assert response.json()["follow_up_type"] in ALLOWED_FOLLOW_UP_TYPES


@patch("app.services.follow_up_service.OpenAI")
def test_invalid_priority_coerced_to_allowed_set(
    _mock_openai_class: MagicMock,
    client,
    valid_follow_up_payload: dict,
) -> None:
    """Service normalizes invalid model output before validation."""
    bad_priority = {**MOCK_LLM_BODY, "priority": "urgent"}
    mock_client = _mock_openai_class.return_value
    mock_client.chat.completions.create.return_value = make_chat_completion_json(bad_priority)

    response = client.post("/generate-follow-up", json=valid_follow_up_payload)
    assert response.status_code == 200
    assert response.json()["priority"] in ALLOWED_PRIORITIES


@patch("app.services.follow_up_service.OpenAI")
def test_invalid_follow_up_type_coerced_to_general(
    _mock_openai_class: MagicMock,
    client,
    valid_follow_up_payload: dict,
) -> None:
    bad_type = {**MOCK_LLM_BODY, "follow_up_type": "unknown_type_xyz"}
    mock_client = _mock_openai_class.return_value
    mock_client.chat.completions.create.return_value = make_chat_completion_json(bad_type)

    response = client.post("/generate-follow-up", json=valid_follow_up_payload)
    assert response.status_code == 200
    assert response.json()["follow_up_type"] == "general_follow_up"


def test_missing_required_field_returns_422(client, valid_follow_up_payload: dict) -> None:
    bad = {**valid_follow_up_payload}
    del bad["contact_name"]
    response = client.post("/generate-follow-up", json=bad)
    assert response.status_code == 422


def test_invalid_email_returns_422(client, valid_follow_up_payload: dict) -> None:
    bad = {**valid_follow_up_payload, "contact_email": "not-a-valid-email"}
    response = client.post("/generate-follow-up", json=bad)
    assert response.status_code == 422


@patch("app.services.follow_up_service.OpenAI")
def test_missing_openai_api_key_returns_503(
    mock_openai_class: MagicMock,
    client,
    valid_follow_up_payload: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "")
    response = client.post("/generate-follow-up", json=valid_follow_up_payload)
    assert response.status_code == 503
    body = response.json()
    assert body.get("error") == "service_unavailable"
    assert "detail" in body
    mock_openai_class.assert_not_called()


@patch("app.services.follow_up_service.OpenAI")
def test_openai_api_failure_returns_502(
    mock_openai_class: MagicMock,
    client,
    valid_follow_up_payload: dict,
) -> None:
    mock_openai_class.return_value.chat.completions.create.side_effect = APIError(
        "mock upstream failure",
        MagicMock(),
        body=None,
    )

    response = client.post("/generate-follow-up", json=valid_follow_up_payload)
    assert response.status_code == 502
    body = response.json()
    assert body.get("error") == "bad_gateway"
    assert "detail" in body
