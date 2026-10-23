import json
import re
from pathlib import Path

KB_PATH = Path(__file__).parent.parent / "data" / "knowledge_base.json"
CUSTOMERS_PATH = Path(__file__).parent.parent / "data" / "customers.json"
INCIDENTS_PATH = Path(__file__).parent.parent / "data" / "incidents.json"

KB_ARTICLES = json.loads(KB_PATH.read_text(encoding="utf-8"))
CUSTOMERS = json.loads(CUSTOMERS_PATH.read_text(encoding="utf-8"))
INCIDENTS = json.loads(INCIDENTS_PATH.read_text(encoding="utf-8"))
REGION_CODES = sorted({
    customer["region"] for customer in CUSTOMERS.values()
} | {
    incident["region"] for incident in INCIDENTS
})

# =====================================================================
# Part 1: Tool implementations (real functions backed by mock data)
# =====================================================================
_THAI = re.compile(r"[\u0e00-\u0e7f]")


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.lower()))


def search_knowledge_base(query: str, top_k: int = 3) -> str:
    words = tokenize(query)
    scored = []
    for article in KB_ARTICLES:
        keywords = article["keywords"]
        matched = words & set(keywords)
        for keyword in keywords:
            if _THAI.search(keyword) and keyword in query:
                matched.add(keyword)
        if matched:
            scored.append({
                "article_id": article["id"],
                "title": article["title"],
                "score": len(matched) / len(keywords),
                "matched_keywords": sorted(matched),
                "content": article["content"],
            })
    scored.sort(key=lambda article: article["score"], reverse=True)
    if not scored:
        return json.dumps({"status": "no_match"}, ensure_ascii=False)
    return json.dumps(
        {"status": "success", "results": scored[:top_k]},
        ensure_ascii=False,
    )


def get_customer_profile(customer_id: str) -> str:
    """Look up the customer's account, plan, SLA tier, region and recent billing transactions by customer_id."""
    customer = CUSTOMERS.get(customer_id)
    if customer is None:
        return json.dumps({"found": False, "customer_id": customer_id})
    return json.dumps({"found": True, "customer": customer}, ensure_ascii=False)


def check_system_status(region: str) -> str:
    """Check active infrastructure incidents for a region code."""
    active = [
        incident
        for incident in INCIDENTS
        if incident["region"] == region and incident["status"] == "active"
    ]
    return json.dumps({
        "region": region,
        "public_status_page": "All Systems Operational",
        "active_incidents": active,
    }, ensure_ascii=False)


# =====================================================================
# Part 2: OpenAI tool definitions (schema sent to the model)
# =====================================================================

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Search the internal Knowledge Base (FAQ, troubleshooting docs, known bugs, and feature roadmap) to help answer or triage the ticket. Use English keywords.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Use English keywords (e.g., 'payment failed multiple charges', 'error 500 asia', 'dark mode mac bug schedule')"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Maximum number of articles to return.",
                        "default": 3
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_customer_profile",
            "description": "Look up the customer's account, plan, SLA tier, region and recent billing transactions by customer_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "Internal customer ID, e.g. 'CUST-1001'"
                    }
                },
                "required": ["customer_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_system_status",
            "description": "Check active infrastructure incidents for a region code. Use the region from the customer profile.",
            "parameters": {
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "enum": REGION_CODES,
                        "description": "Region code from the customer profile, e.g. 'ap-southeast-1'"
                    }
                },
                "required": ["region"]
            }
        }
    }
]

# Map a function name (string) requested by the model to the real Python function.
AVAILABLE_TOOLS = {
    "search_knowledge_base": search_knowledge_base,
    "get_customer_profile": get_customer_profile,
    "check_system_status": check_system_status,
}
