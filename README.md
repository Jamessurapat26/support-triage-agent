# Support Ticket Triage Agent

FastAPI service that triages a support ticket: it classifies urgency, looks up the customer, knowledge base, and system status, then returns a structured next action and a draft reply.

See [WRITEUP.md](WRITEUP.md) for architecture decisions, failure modes, and evaluation.

## Setup

Requires Python 3.13.

```bash
cp .env.example .env
```

Set `OPENAI_API_KEY` in `.env`. `OPENAI_MODEL` defaults to `gpt-6-luna`. Set `OPENAI_BASE_URL` when calling an OpenAI-compatible host such as OpenRouter, and use that host's model id in `OPENAI_MODEL` (for example `openai/gpt-6-luna`).

Install dependencies with [uv](https://docs.astral.sh/uv/):

```bash
uv sync
```

Or with pip:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uv run uvicorn main:app --reload
```

If you installed with pip and the virtualenv is active, drop the `uv run` prefix:

```bash
uvicorn main:app --reload
```

The API listens on http://127.0.0.1:8000. Interactive docs are at http://127.0.0.1:8000/docs.

Check that the app and the configured model are reachable:

```bash
curl http://127.0.0.1:8000/health
```

Run one of the three built-in sample tickets (`1`, `2`, or `3`):

```bash
curl -X POST http://127.0.0.1:8000/api/v1/triage/sample/1
```

Run all three samples:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/triage/evaluate-all
```

Submit your own ticket:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/triage \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST-1001",
    "customer_info": "Free plan, 4 months",
    "messages": [
      {"timestamp": "just now", "content": "My payment failed when I tried to upgrade to Pro."}
    ]
  }'
```

`ticket_id` is optional. When it is omitted, the API generates one.
