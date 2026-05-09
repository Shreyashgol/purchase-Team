import json
from typing import Any

from app.config import GROQ_API_KEY
from app.operations.groq_client import groq_chat_completion
from app.operations.llm_client import chat_completion


SYSTEM_PROMPT = """
You are a helpful SAP Business One purchase assistant inside a chatbot.
Answer like a practical business assistant, not like a raw API logger.

Your job:
- Explain what happened in plain language.
- Mention the routed document type and action only if useful.
- If the backend failed, explain what information is missing or what the user should fix.
- Generate the next 2-4 useful suggestions from the user's prompt, routing decision, and backend response.
- For fetch results, mention the specific result shape: row count, key totals, top rows, or the entity asked about.
- If backendResponse.data.strategy is rag, explain the answer as an analytical fetch without exposing implementation details.
- Keep answers concise, specific, and interactive.
- Do not invent SAP document numbers, vendor names, item names, prices, or database records.
- If suggesting prompts, use placeholders only when the needed value is unknown.
- Do not expose raw tokens, secrets, stack traces, or internal implementation details.
"""


def _json_preview(value: Any, max_chars: int = 5000) -> str:
    try:
        text = json.dumps(value, indent=2, default=str)
    except TypeError:
        text = str(value)
    if len(text) <= max_chars:
        return text
    return f"{text[:max_chars]}\n...truncated..."


def _fallback_response(
    prompt: str,
    routing_decision: dict[str, Any],
    api_response: dict[str, Any],
    status_code: int | None,
) -> str:
    action = routing_decision.get("action", "request")
    document_type = routing_decision.get("documentType", "purchase document").replace("_", " ")
    detail = api_response.get("detail") or api_response.get("message") or "No detailed backend message was returned."

    if status_code and 200 <= status_code < 300:
        message = api_response.get("message", "The request completed successfully.")
        data = api_response.get("data") or {}
        rows = data.get("results") or data.get("rows") or []
        row_count = data.get("rowCount", len(rows) if isinstance(rows, list) else 0)
        strategy = data.get("strategy")
        summary = _rows_summary(rows) if isinstance(rows, list) else ""
        suggestions = _suggestions(prompt, document_type)
        analysis_note = " I handled this as an analytical fetch." if strategy == "rag" else ""
        return (
            f"{message}\n\n"
            f"I handled this as a **{document_type}** `{action}` request and found **{row_count}** matching result(s).{analysis_note}"
            f"{summary}\n\n"
            f"**You can ask next:**\n{suggestions}"
        )

    return (
        f"I understood your request as a **{document_type}** `{action}` request, but I could not complete it yet.\n\n"
        f"**What needs attention:** {detail}\n\n"
        "Please send the missing or corrected details in one message, and I will try again."
    )


def _rows_summary(rows: list[Any], limit: int = 3) -> str:
    if not rows:
        return ""

    lines = []
    for row in rows[:limit]:
        if not isinstance(row, dict):
            continue
        useful_items = []
        for key, value in row.items():
            if value is None or isinstance(value, (dict, list)):
                continue
            useful_items.append(f"{key}: {value}")
            if len(useful_items) == 4:
                break
        if useful_items:
            lines.append("- " + ", ".join(useful_items))

    if not lines:
        return ""
    return "\n\n**Key results:**\n" + "\n".join(lines)


def _suggestions(prompt: str, document_type: str) -> str:
    lowered = prompt.lower()
    if "purchase order" in document_type:
        suggestions = [
            "Show overdue open purchase orders",
            "Which vendors have the highest pending purchase order value?",
            "Which items have the most pending PO quantity?",
        ]
    elif "invoice" in document_type:
        suggestions = [
            "What is the total AP invoice balance due?",
            "Which vendors have the highest AP invoice amount?",
            "Which items have the highest invoiced quantity?",
        ]
    else:
        suggestions = [
            "What is the total purchase return value?",
            "Which vendors have the highest purchase return amount?",
            "Which items are returned the most?",
        ]

    if "vendor" in lowered:
        suggestions.append("Show the latest documents for vendor <vendor code>")

    return "\n".join(f"- {suggestion}" for suggestion in suggestions[:4])


def generate_chat_response(
    prompt: str,
    routing_decision: dict[str, Any],
    api_response: dict[str, Any],
    status_code: int | None,
) -> str:
    user_payload = {
        "userPrompt": prompt,
        "routingDecision": routing_decision,
        "backendStatusCode": status_code,
        "backendResponse": api_response,
    }

    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Create the final chatbot reply for this SAP request.\n\n"
                    f"{_json_preview(user_payload)}"
                ),
            },
        ]
        if GROQ_API_KEY:
            return groq_chat_completion(messages, temperature=0.2, max_tokens=2048, timeout=120)
        return chat_completion(messages, temperature=0.3, max_tokens=2048, timeout=120)
    except Exception:
        return _fallback_response(prompt, routing_decision, api_response, status_code)
