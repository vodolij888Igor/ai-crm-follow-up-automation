"""
FastAPI entrypoint: CRM-style JSON in → follow-up plan JSON out.

Run locally: `uvicorn app.main:app --reload`
Environment: copy `.env.example` to `.env` and set OPENAI_API_KEY.
"""

from dotenv import load_dotenv

# Load `.env` before importing the service so configuration is available everywhere.
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.schemas.follow_up_schema import FollowUpRequest, FollowUpResponse
from app.services.follow_up_service import (
    MissingOpenAIConfigurationError,
    OpenAIInvocationError,
    generate_follow_up_plan,
)

app = FastAPI(
    title="AI CRM Follow-up Automation",
    description=(
        "Accepts simulated CRM lead data and returns an AI-ready follow-up plan: "
        "priority, message draft, recommended action, and short reasoning. "
        "Powered by OpenAI (requires OPENAI_API_KEY)."
    ),
    version="0.2.0",
)

# Allow browser demos / local frontends without extra config during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(MissingOpenAIConfigurationError)
async def missing_openai_config_handler(
    _request: Request, exc: MissingOpenAIConfigurationError
) -> JSONResponse:
    """Service is not configured for upstream AI (missing API key)."""
    return JSONResponse(
        status_code=503,
        content={"detail": exc.message, "error": "service_unavailable"},
    )


@app.exception_handler(OpenAIInvocationError)
async def openai_invocation_handler(_request: Request, exc: OpenAIInvocationError) -> JSONResponse:
    """Upstream OpenAI failed or returned unusable output."""
    return JSONResponse(
        status_code=502,
        content={"detail": exc.message, "error": "bad_gateway"},
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
