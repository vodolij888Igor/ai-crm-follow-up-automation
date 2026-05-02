# AI CRM Follow-up Automation

Portfolio backend for **AI Automation Engineer**, **AI Integration Developer**, **Full-Stack AI Product Developer**, and **AI Creator** roles. It exposes a single API that accepts CRM-style lead JSON and returns a structured follow-up plan suitable for human reps or downstream automation.

## Project overview

This service simulates the “brain” of a follow-up assistant: it takes what you know about a lead (name, company, status, need, budget, recency) and returns **priority**, **message draft**, **recommended next action**, and short **reasoning**. Version **0.1.0** uses **placeholder rules** in code—no live LLM and no database—so the contract is stable and easy to demo.

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
| Config (future) | `pydantic-settings`, `python-dotenv` |

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

4. **Optional:** copy `.env.example` to `.env` for future API keys (not required for v1).

5. **Run the API**

   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Explore docs:** open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for interactive OpenAPI (Swagger UI).

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

Field wording may vary slightly depending on placeholder rules; shape is stable.

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

The response shape is stable; exact wording follows the placeholder rules in `app/services/follow_up_service.py` and may change if you tune thresholds.

## Screenshot

The screenshot below shows a successful POST /generate-follow-up request in FastAPI Swagger UI with a 200 response.

![Swagger UI successful CRM follow-up response](docs/images/swagger-crm-follow-up-code-200.png)

## Current limitations

- **No LLM:** Messages and reasoning come from **fixed rules**, not generative AI.
- **No persistence:** Nothing is stored; each request is stateless.
- **No CRM connector:** Leads are simulated by posting JSON; no HubSpot/Salesforce sync.
- **No auth:** Endpoints are open—add API keys or OAuth before production.
- **CORS is permissive:** Suitable for local demos; tighten for deployment.

## Future improvements

- Swap `follow_up_service` internals for **OpenAI** (or another provider) with retries, timeouts, and cost controls.
- Add **OAuth2 / API keys** and rate limiting.
- Persist leads and outcomes in **PostgreSQL** or a CRM webhook pipeline.
- Add **batch generation** and **webhooks** for async CRM workflows.
- Introduce **A/B tone variants** and brand-specific prompt packs.

## License

Use freely for portfolio and learning; add a license file if you publish publicly.
