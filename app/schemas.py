from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


# ==========================================
# 1. Required choices from the assignment (Enums)
# ==========================================
class UrgencyLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class NextAction(str, Enum):
    AUTO_RESPOND = "auto_respond"
    ROUTE_TO_SPECIALIST = "route_to_specialist"
    ESCALATE_TO_HUMAN = "escalate_to_human"


# ==========================================
# 2. Input schema (API request)
# ==========================================
class TicketMessage(BaseModel):
    timestamp: str = Field(
        ...,
        description="When the message was sent, e.g. '3 hours ago' or 'just now'"
    )
    content: str = Field(
        ...,
        description="Message content from the customer"
    )


class TicketInput(BaseModel):
    ticket_id: str = Field(
        default_factory=lambda: f"TICKET-{uuid4().hex[:8].upper()}",
        description="Optional ticket reference id, e.g. 'TICKET-001'. Auto-generated when omitted."
    )
    customer_id: str | None = Field(
        None,
        description="Optional internal customer ID, e.g. 'CUST-1001'"
    )
    customer_info: str = Field(
        ...,
        description="Basic customer details, such as plan and how long they have been a customer"
    )
    messages: list[TicketMessage] = Field(
        ...,
        description="Customer messages in chronological order"
    )


# ==========================================
# 3. Output schema (agent and API response)
# ==========================================
class ExtractedInfo(BaseModel):
    product_area: str = Field(
        ...,
        description="Related product area or feature, e.g. 'Billing & Subscription', 'Core Platform', 'UI/Appearance'"
    )
    issue_type: str = Field(
        ...,
        description="Issue type, e.g. 'Payment Failure / Multiple Charges', 'System Outage (Error 500)', 'Bug & Feature Request'"
    )
    customer_sentiment: str = Field(
        ...,
        description="Customer sentiment, e.g. 'Angry / Frustrated', 'Panicked / Urgent', 'Friendly / Curious'"
    )
    detected_language: str = Field(
        ...,
        description="Primary language the customer used, e.g. 'en' or 'th'"
    )
    summary: str = Field(
        ...,
        description="Short summary of the customer's issue in 1-2 sentences"
    )


class TriageResult(BaseModel):
    urgency: UrgencyLevel = Field(
        ...,
        description="Urgency level of the ticket"
    )
    extracted_info: ExtractedInfo = Field(
        ...,
        description="Key information extracted from the ticket"
    )
    relevant_kb_articles: list[str] = Field(
        ...,
        description="Knowledge Base article titles or ids used to help answer the ticket"
    )
    next_action: NextAction = Field(
        ...,
        description="Decision on what to do with this ticket next"
    )
    reasoning: str = Field(
        ...,
        description="Reasoning behind the urgency and next-action decision"
    )
    suggested_response: str = Field(
        ...,
        description="Draft reply to the customer, written in the same language the customer used"
    )


class APIResponse(BaseModel):
    ticket_id: str
    tools_called: list[str] = Field(
        ...,
        description="Tools the agent called while analyzing the ticket"
    )
    triage_result: TriageResult


class OpenAIHealth(BaseModel):
    status: str = Field(..., description="'healthy' when the API accepts the key and the configured model is listed")
    model: str | None = Field(None, description="Model configured for triage")
    detail: str | None = Field(None, description="Why the OpenAI API check failed")


class HealthResponse(BaseModel):
    status: str = Field(..., description="'healthy' when the app and the OpenAI API are both reachable")
    message: str
    openai: OpenAIHealth
