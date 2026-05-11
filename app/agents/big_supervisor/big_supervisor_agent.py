from app.operations.groq_client import groq_chat_completion
from app.agents.supervisor.supervisor_agent import execute as purchase_team_execute
from app.schema.response import PurchaseTeamRoutingResponse

_BIG_SUPERVISOR_SYSTEM = """You are a top-level routing agent for an SAP Business One ERP system.

Your ONLY job is to read the user's request and decide which team should handle it:

- "purchase" team: handles anything related to buying from VENDORS — purchase orders, AP invoices (vendor bills), purchase returns, vendor payments, goods receipts.
- "sales" team: handles anything related to selling to CUSTOMERS — sales orders, AR invoices (customer bills), customer accounts, sales revenue, delivered goods.

Reply with ONLY one word: purchase OR sales

No explanation. No punctuation. Just one lowercase word.
"""


def decide_team(prompt: str) -> str:
    """Use LLM to decide whether the prompt belongs to purchase or sales team."""
    try:
        messages = [
            {"role": "system", "content": _BIG_SUPERVISOR_SYSTEM},
            {"role": "user", "content": prompt},
        ]
        result = groq_chat_completion(messages, temperature=0.0, max_tokens=5, timeout=30)
        team = result.strip().lower().split()[0]
        return team if team in ("purchase", "sales") else "purchase"
    except Exception:
        # Keyword fallback
        lowered = prompt.lower()
        sales_keywords = (
            "sales order", "so ", "ar invoice", "sales invoice", "customer",
            "revenue", "selling", "sold", "delivery", "client", "receivable",
        )
        return "sales" if any(k in lowered for k in sales_keywords) else "purchase"


def route(prompt: str) -> dict:
    """
    Big Supervisor entry point.
    Returns a dict:
    {
        "team": "purchase" | "sales",
        "team_label": str,
        "endpoint": str,
        "routing_decision": dict,
    }
    """
    team = decide_team(prompt)

    if team == "sales":
        # Determine sales document type for display
        lowered = prompt.lower()
        if any(k in lowered for k in ("ar invoice", "sales invoice", "invoice", "receivable", "billing")):
            doc_type = "ar_invoice"
            doc_label = "AR Invoice"
        else:
            doc_type = "sales_order"
            doc_label = "Sales Order"

        return {
            "team": "sales",
            "team_label": "Sales Team",
            "endpoint": "/sales/parse-and-execute",
            "routing_decision": {
                "action": "fetch",
                "documentType": doc_type,
                "documentAgent": "sales_agent",
                "subagent": "sales_agent.fetch_agent",
                "team": "sales",
                "reason": f"Big Supervisor detected SALES intent → {doc_label} fetch",
                "conditions": [
                    "Sales team handles customer-facing documents",
                    "All sales operations are read-only fetch via RAG SQL",
                ],
            },
        }

    # Purchase team — use existing purchase supervisor
    try:
        purchase_response: PurchaseTeamRoutingResponse = purchase_team_execute(prompt)
        response_data = purchase_response.model_dump()["data"]
        routing_decision = response_data.get("fetchAgent", {})
    except Exception:
        routing_decision = {
            "action": "fetch",
            "documentType": "purchase_order",
            "documentAgent": "purchase_order_agent",
            "subagent": "purchase_order_agent.fetch_agent",
            "team": "purchase",
        }

    # Map document type to endpoint
    _ENDPOINTS = {
        "purchase_order": "/purchase-orders/parse-and-execute",
        "ap_invoice": "/ap-invoices/parse-and-execute",
        "purchase_return": "/purchase-returns/parse-and-execute",
    }
    doc_type = routing_decision.get("documentType", "purchase_order")
    endpoint = _ENDPOINTS.get(doc_type, "/purchase-orders/parse-and-execute")

    return {
        "team": "purchase",
        "team_label": "Purchase Team",
        "endpoint": endpoint,
        "routing_decision": routing_decision,
    }
