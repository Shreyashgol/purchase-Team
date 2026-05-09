import requests

from app.config import GROQ_API_KEY, GROQ_BASE_URL, GROQ_MODEL


def groq_chat_completion(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0,
    max_tokens: int = 1024,
    timeout: int = 120,
) -> str:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is required for RAG SQL generation")

    response = requests.post(
        f"{GROQ_BASE_URL.rstrip('/')}/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": GROQ_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        },
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()
