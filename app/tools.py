import json
import re
from typing import Dict, Any
from pathlib import Path


KB_PATH = Path(__file__).parent.parent / "data" / "knowledge_base.json"
KB_ARTICLES = json.loads(KB_PATH.read_text(encoding="utf-8"))

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


def check_customer_and_billing_status(customer_context: str) -> str:
    """
    Look up account status, payment history, or customer importance from the internal database.
    """
    ctx = customer_context.lower()

    # Mock backend record for ticket 1 (Free-plan customer charged repeatedly while upgrading).
    if "free" in ctx or "upgrade" in ctx or "29.99" in ctx:
        return json.dumps({
            "account_tier": "Free (Upgrade Stuck)",
            "payment_gateway_logs": [
                {"attempt": 1, "amount": "$29.99", "status": "Gateway Timeout - Pending Hold"},
                {"attempt": 2, "amount": "$29.99", "status": "Gateway Timeout - Pending Hold"},
                {"attempt": 3, "amount": "$29.99", "status": "Gateway Timeout - Pending Hold"}
            ],
            "pro_entitlement_active": False,
            "chargeback_risk": "HIGH (Customer threatened bank dispute)",
            "recommended_handling": "Requires human Billing Specialist / Support Lead to manually reverse 2 holds, capture 1, and unlock Pro features immediately."
        })

    # Mock backend record for ticket 2 (Enterprise customer in Thailand).
    if "enterprise" in ctx or "thailand" in ctx or "45" in ctx:
        return json.dumps({
            "account_tier": "Enterprise",
            "seats": 45,
            "region": "Asia-Southeast (Thailand)",
            "sla_tier": "Platinum (15-minute response SLA for critical outages)",
            "account_health_note": "High-value account. Active client demo today."
        })

    # Mock backend record for ticket 3 (regular Pro-plan customer).
    return json.dumps({
        "account_tier": "Pro",
        "tenure": "5 months",
        "engagement": "High (Daily active user)",
        "billing_status": "Healthy (No failed payments)",
        "client_version": "macOS Desktop v2.4.1 (Affected by cached theme flag bug)"
    })


def check_system_status(region: str = "global") -> str:
    """
    Check server status and internal incidents by region.
    """
    r = region.lower()
    if any(k in r for k in ["asia", "thailand", "ap", "southeast"]):
        return json.dumps({
            "public_status_page": "All Systems Operational",
            "internal_telemetry_alert": "CRITICAL INCIDENT #INC-902: Asia-Southeast API Gateway (ap-southeast-1) is returning HTTP 500 errors due to a database connection pool exhaustion. Started 2 hours ago.",
            "impact": "Enterprise & Pro users in Thailand/Asia region cannot authenticate or load workspace.",
            "action_required": "Escalate affected Enterprise tickets directly to On-Call Incident Commander."
        })

    return json.dumps({
        "public_status_page": "All Systems Operational",
        "internal_telemetry_alert": "No active infrastructure incidents in US/EU regions."
    })


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
            "name": "check_customer_and_billing_status",
            "description": "Look up internal customer account details, SLA tier, and payment gateway transaction logs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_context": {
                        "type": "string",
                        "description": "Brief summary of customer info from the ticket (e.g., 'Free plan upgrade attempted', 'Enterprise Thailand 45 seats', 'Pro plan 5 months')"
                    }
                },
                "required": ["customer_context"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_system_status",
            "description": "Check internal infrastructure monitoring and server health logs for a specific geographic region.",
            "parameters": {
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "description": "Geographic region to check (e.g., 'Asia', 'Thailand', 'Global')"
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
    "check_customer_and_billing_status": check_customer_and_billing_status,
    "check_system_status": check_system_status,
}
