# Support Ticket Triage AI Agent

An automated AI Support Ticket Triage system built with **FastAPI**, **OpenAI Function Calling**, and **Pydantic Structured Outputs**. The agent evaluates incoming multi-turn support conversations, investigates context via internal tools (customer SLA, billing logs, internal telemetry, and knowledge base), classifies urgency, extracts structured metadata, and decides the appropriate operational next action.

---

## Key Capabilities

* **Urgency Classification**: Categorizes issues into `critical`, `high`, `medium`, or `low` based on SLA, business impact, and deadline pressures.
* **Metadata Extraction**: Extracts `product_area`, `issue_type`, `customer_sentiment`, `detected_language`, and a concise executive `summary`.
* **Tool-Driven Investigation**: Mandates calling at least 2 internal tools (mocked) to gather facts before reaching a verdict:
  * `search_knowledge_base`: Retrieves troubleshooting steps, known bugs, or workarounds.
  * `get_customer_profile`: Looks up account, plan, SLA tier, region, and recent billing transactions by customer ID.
  * `check_system_status`: Checks active infrastructure incidents for a region code.
* **Next Action Routing**: Decides whether to `auto_respond`, `route_to_specialist`, or `escalate_to_human`.
* **Language-Preserved Response**: Automatically crafts an empathetic resolution response in the customer's native language (e.g., Thai or English).

---

## Project Structure

```text
├── app/
│   ├── __init__.py
│   ├── agent.py          # Core Agent loop (tool calling + structured output)
│   ├── prompts.py        # System prompt with triage guardrails
│   ├── sample_data.py    # 3 sample tickets provided in the assignment
│   ├── schemas.py        # Pydantic schemas (Request, Response, Enums)
│   └── tools.py          # Tool schemas and mock implementations
├── main.py               # FastAPI application and test endpoints
├── pyproject.toml        # Project dependencies (uv-compatible)
├── requirements.txt      # Standard pip dependencies
├── .env.example          # Environment variables template
└── README.md             # Documentation and design write-up
