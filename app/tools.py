import json
from typing import Dict, Any

# =====================================================================
# Part 1: Tool implementations (real functions backed by mock data)
# =====================================================================

def search_knowledge_base(query: str, category: str = "general") -> str:
    """
    Search the knowledge base for FAQ articles, basic troubleshooting steps, or known bugs.
    """
    q = query.lower()
    results = []

    # Mock data for billing / payment (covers ticket 1).
    if any(k in q for k in ["payment", "charge", "upgrade", "billing", "pro", "refund"]) or category == "billing":
        results.append({
            "article_id": "KB-101",
            "title": "Failed Upgrades and Multiple Pending Charges",
            "content": (
                "If a customer experiences a payment gateway timeout during a Pro upgrade, "
                "multiple pending authorization holds ($29.99) may appear on their bank statement, "
                "while the account remains on the Free tier. "
                "Action Policy: Billing specialists must manually void duplicate pending authorizations "
                "and force-provision Pro access immediately if the user has an urgent deadline."
            )
        })

    # Mock data for error 500 / outage (covers ticket 2).
    if any(k in q for k in ["500", "outage", "down", "asia", "thailand", "access", "status"]) or category == "technical":
        results.append({
            "article_id": "KB-205",
            "title": "Troubleshooting HTTP 500 Errors & Regional Discrepancies",
            "content": (
                "HTTP 500 errors across multiple browsers/machines indicate a server-side failure. "
                "Note: status.company.com only reflects global core availability and may lag behind "
                "regional edge gateway incidents (e.g., Asia-Pacific CDN/Gateway). "
                "Action Policy: Any Enterprise outage affecting multiple seats must be escalated "
                "immediately to the On-Call Incident / Infrastructure Engineering team."
            )
        })

    # Mock data for dark mode / appearance (covers ticket 3).
    if any(k in q for k in ["dark", "theme", "appearance", "mac", "schedule", "system default"]) or category == "feature":
        results.append({
            "article_id": "KB-312",
            "title": "Dark Mode Settings & Known macOS 'System Default' Sync Bug",
            "content": (
                "1. Known Issue (BUG-884): On macOS, selecting 'System Default' under Settings > Appearance "
                "sometimes fails to detect OS-level Dark Mode due to a cached desktop client flag. "
                "Workaround: Clear app cache (Settings > Advanced > Clear Cache) and restart the app, "
                "which will also reveal the manual 'Dark' toggle on Pro plans.\n"
                "2. Scheduled Dark Mode (Auto-switch by time): Currently not supported. "
                "It is tracked on our public product roadmap (Feature Request ID: FR-409) for Q3."
            )
        })

    if not results:
        return json.dumps({"status": "no_exact_match", "message": "No specific KB article found. Use general triage rules."})

    return json.dumps({"status": "success", "articles": results}, ensure_ascii=False)


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
            "description": "Search the internal Knowledge Base (FAQ, troubleshooting docs, known bugs, and feature roadmap) to help answer or triage the ticket.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Keywords to search for (e.g., 'payment failed multiple charges', 'error 500 asia', 'dark mode mac bug schedule')"
                    },
                    "category": {
                        "type": "string",
                        "enum": ["billing", "technical", "feature", "general"],
                        "description": "Category of the issue"
                    }
                },
                "required": ["query", "category"]
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
