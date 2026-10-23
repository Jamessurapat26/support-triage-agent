import logging
from typing import List
from fastapi import FastAPI, HTTPException, Response
from app.schemas import TicketInput, APIResponse, HealthResponse, OpenAIHealth
from app.sample_data import SAMPLE_TICKETS
from app.agent import SupportTriageAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("support-triage-agent")

app = FastAPI(
    title="Support Ticket Triage Agent API",
    description="AI Agent that classifies ticket urgency, extracts key info, searches KB, and decides next actions.",
    version="1.1.0",
)


@app.get("/")
def root():
    return {
        "status": "healthy",
        "message": "Support Ticket Triage Agent API is running. Visit /docs for Swagger UI.",
    }


@app.get("/health", response_model=HealthResponse)
def health_check(response: Response):
    """Check that the app is running and the configured OpenAI-compatible API accepts the key."""
    try:
        openai_health = SupportTriageAgent().check_openai_health()
    except ValueError as exc:
        openai_health = {"status": "unhealthy", "model": None, "detail": str(exc)}

    api_ok = openai_health["status"] == "healthy"
    if not api_ok:
        response.status_code = 503

    return HealthResponse(
        status="healthy" if api_ok else "unhealthy",
        message=(
            "Support Ticket Triage Agent API and the OpenAI API are reachable."
            if api_ok
            else "Support Ticket Triage Agent API is running, but the OpenAI API check failed."
        ),
        openai=OpenAIHealth(**openai_health),
    )


@app.post("/api/v1/triage", response_model=APIResponse)
def triage_custom_ticket(ticket: TicketInput):
    """
    Analyze any support ticket submitted as JSON.
    """
    try:
        agent = SupportTriageAgent()
        return agent.process_ticket(ticket)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/triage/sample/{sample_id}", response_model=APIResponse)
def triage_sample_ticket(sample_id: int):
    """
    Run a sample ticket from the assignment (pass 1, 2, or 3) without pasting the message yourself.
    """
    logger.info(f"Received request for sample ticket #{sample_id}")
    if sample_id not in SAMPLE_TICKETS:
        raise HTTPException(
            status_code=404,
            detail=f"Sample ticket {sample_id} not found. Please choose 1, 2, or 3.",
        )
    try:
        agent = SupportTriageAgent()
        return agent.process_ticket(SAMPLE_TICKETS[sample_id])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/triage/evaluate-all", response_model=List[APIResponse])
def evaluate_all_samples():
    """
    Run all 3 sample tickets from the assignment in a single request.
    """
    try:
        agent = SupportTriageAgent()
        results = []
        for sample_id in sorted(SAMPLE_TICKETS.keys()):
            results.append(agent.process_ticket(SAMPLE_TICKETS[sample_id]))
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
