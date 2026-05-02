"""
FastAPI entrypoint: CRM-style JSON in → follow-up plan JSON out.

Run locally: `uvicorn app.main:app --reload`
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.schemas.follow_up_schema import FollowUpRequest, FollowUpResponse
from app.services.follow_up_service import generate_follow_up_plan

app = FastAPI(
    title="AI CRM Follow-up Automation",
    description=(
        "Accepts simulated CRM lead data and returns an AI-ready follow-up plan: "
        "priority, message draft, recommended action, and short reasoning. "
        "v1 uses placeholder rules (no external AI calls)."
    ),
    version="0.1.0",
)

# Allow browser demos / local frontends without extra config during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check for load balancers and quick sanity checks."""
    return {"status": "ok"}


@app.post(
    "/generate-follow-up",
    response_model=FollowUpResponse,
    summary="Generate a follow-up plan from CRM lead data",
)
def generate_follow_up(body: FollowUpRequest) -> FollowUpResponse:
    """
    Validate incoming CRM-style JSON and return a structured follow-up plan.

    Request body is validated by Pydantic; invalid payloads return 422 with details.
    """
    return generate_follow_up_plan(body)
