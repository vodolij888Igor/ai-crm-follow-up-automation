# AI CRM Follow-up Automation

Portfolio backend for **AI Automation Engineer**, **AI Integration Developer**, **Full-Stack AI Product Developer**, and **AI Creator** roles. It exposes a single API that accepts CRM-style lead JSON and returns a structured follow-up plan suitable for human reps or downstream automation.

## Project overview

This service simulates the “brain” of a follow-up assistant: it takes what you know about a lead (name, company, status, need, budget, recency) and returns **priority**, **message draft**, **recommended next action**, and short **reasoning**. **`POST /generate-follow-up` uses the OpenAI API** to analyze the lead and produce a structured, CRM-ready follow-up plan (JSON in / JSON out). There is no database; state is sent on each request.

## Business use case

Sales and success teams lose deals when follow-ups are late, generic, or unprioritized. A small API like this can sit behind a CRM, a scheduling tool, or a workflow engine to:

- Standardize what “good” follow-up looks like for each lead.
- Produce a **draft message** aligned with tone preferences.
- Emit **priority** and **next action** for queues, Slack alerts, or task creation.

## Tech stack

| Layer        | Choice                          |
| ------------ | ------------------------------- |
| API          | [FastAPI](https://fastapi.tiangolo.com/) |
| Validation   | [Pydantic v2](https://docs.pydantic.dev/) |
| Server       | [Uvicorn](https://www.uvicorn.org/) |
| AI           | [OpenAI API](https://platform.openai.com/) (chat completions, JSON output) |
| Config       | `python-dotenv` (`.env`), optional `pydantic-settings` |

## Setup instructions

**Prerequisites:** Python 3.10+ recommended.

1. **Clone or copy** this repository and open a terminal in the project root.

2. **Create and activate a virtual environment**

   - Windows (PowerShell):

     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```

   - macOS / Linux:

     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure OpenAI:** copy `.env.example` to `.env` and set `OPENAI_API_KEY` (required for `POST /generate-follow-up`). Optionally set `OPENAI_MODEL` (defaults to `gpt-4o-mini` if unset).

5. **Run the API**

   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Explore docs:** open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for interactive OpenAPI (Swagger UI).

### Running tests

Automated tests mock the OpenAI client—no real API key or network call is required.

```bash
pip install -r requirements.txt
pytest
```

## API

### `POST /generate-follow-up`

Accepts JSON body matching the CRM-style lead shape below.

### Sample request

```http
POST /generate-follow-up HTTP/1.1
Host: 127.0.0.1:8000
Content-Type: application/json

```

```json
{
  "contact_name": "John Smith",
  "contact_email": "john@example.com",
  "company_name": "Smith Roofing",
  "lead_status": "interested",
  "last_contact_days_ago": 5,
  "customer_need": "Wants to automate customer follow-up emails and lead tracking.",
  "budget_usd": 2500,
  "preferred_tone": "professional"
}
```

Example with `curl`:

```bash
curl -s -X POST "http://127.0.0.1:8000/generate-follow-up" ^
  -H "Content-Type: application/json" ^
  -d "{\"contact_name\":\"John Smith\",\"contact_email\":\"john@example.com\",\"company_name\":\"Smith Roofing\",\"lead_status\":\"interested\",\"last_contact_days_ago\":5,\"customer_need\":\"Wants to automate customer follow-up emails and lead tracking.\",\"budget_usd\":2500,\"preferred_tone\":\"professional\"}"
```

On macOS/Linux, use `\` for line continuation instead of `^`.

### Sample response

Wording comes from the model and will vary by lead and prompt; the **response shape** is stable. `priority` is always `low`, `medium`, or `high`. `follow_up_type` is one of: `sales_follow_up`, `re_engagement`, `payment_follow_up`, `onboarding_follow_up`, `support_follow_up`, `general_follow_up`.

```json
{
  "contact_name": "John Smith",
  "priority": "high",
  "follow_up_type": "sales_follow_up",
  "summary": "John Smith from Smith Roofing is interested: Wants to automate customer follow-up emails and lead tracking.",
  "suggested_message": "Hi John, I wanted to follow up with you at Smith Roofing about the following: Wants to automate customer follow-up emails and lead tracking. I'd love to share how we can help and answer any questions. Would you have 20 minutes this week for a quick discovery call?",
  "recommended_action": "Send follow-up email and offer a discovery call.",
  "reasoning": "The lead has a clear budget signal and has gone several days without contact. Last contact was 5 day(s) ago; budget signal is around $2,500."
}
```

The response shape is fixed; text fields are **OpenAI-generated** from your request and the system prompt in `app/services/follow_up_service.py`.

### Errors

| HTTP status | When |
| ----------- | ---- |
| **503** | `OPENAI_API_KEY` is missing or empty (`detail` explains configuration). |
| **502** | OpenAI request failed, or the model returned output that could not be parsed or validated. |

## Screenshot

The screenshot below shows a successful POST /generate-follow-up request in FastAPI Swagger UI with a 200 response.

![Swagger UI successful CRM follow-up response](docs/images/swagger-crm-follow-up-code-200.png)

## Current limitations

- **Requires OpenAI:** You need a valid API key and network access to OpenAI; rate limits and outages surface as **502** responses.
- **No persistence:** Nothing is stored; each request is stateless.
- **No CRM connector:** Leads are simulated by posting JSON; no HubSpot/Salesforce sync.
- **No auth:** Endpoints are open—add API keys or OAuth before production.
- **CORS is permissive:** Suitable for local demos; tighten for deployment.

## Future improvements

- Retries, backoff, and request timeouts tuned per deployment; optional streaming or batched generation.
- Add **OAuth2 / API keys** and rate limiting.
- Persist leads and outcomes in **PostgreSQL** or a CRM webhook pipeline.
- Add **batch generation** and **webhooks** for async CRM workflows.
- Introduce **A/B tone variants** and brand-specific prompt packs.

## License

Use freely for portfolio and learning; add a license file if you publish publicly.
