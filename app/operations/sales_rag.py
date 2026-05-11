from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import PURCHASE_RAG_EMBEDDING_MODEL, REPO_ROOT
from app.operations.groq_client import groq_chat_completion

RAG_ROOT = Path(__file__).resolve().parents[1] / "rag"
DATA_DIR = RAG_ROOT / "data"
SALES_TABLES_PATH = DATA_DIR / "sales_tables.json"
SALES_QUERIES_PATH = DATA_DIR / "sales_queries.json"

SALES_RAG_PERSIST_DIR = REPO_ROOT / ".rag_chroma" / "sales"

ALLOWED_SALES_TABLES = {"ORDR", "RDR1", "OINV", "INV1", "OCRD", "OITM"}


@dataclass(frozen=True)
class RagDocument:
    id: str
    content: str
    embedding_text: str
    metadata: dict[str, Any]


def _load_json(path: Path):
    return json.loads(path.read_text())


def _stable_id(prefix: str, value: str) -> str:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"


def _table_documents() -> list[RagDocument]:
    data = _load_json(SALES_TABLES_PATH)
    documents: list[RagDocument] = []
    for table_name, table_data in data.items():
        columns = "\n".join(f"{name}: {desc}" for name, desc in table_data.get("columns", {}).items())
        joins = "\n".join(f"{j['table']} ON {j['on']}" for j in table_data.get("joins", []))
        content = f"""Table: {table_name}
Description: {table_data.get("description", "")}
Business Meaning: {table_data.get("business_meaning", "")}
Business Terms: {", ".join(table_data.get("business_terms", []))}
Columns:
{columns}
Joins:
{joins}""".strip()
        documents.append(
            RagDocument(
                id=_stable_id("sales_schema", table_name),
                content=content,
                embedding_text=table_data.get("embedding_text", ""),
                metadata={"type": "schema", "table_name": table_name},
            )
        )
    return documents


def _query_documents() -> list[RagDocument]:
    data = _load_json(SALES_QUERIES_PATH)
    documents: list[RagDocument] = []
    for index, entry in enumerate(data):
        content = f"""Question: {entry.get("question", "")}
Intent: {entry.get("intent", "")}
Business Context: {entry.get("business_context", "")}
Tables Used: {", ".join(entry.get("tables_used", []))}
SQL Pattern: {entry.get("sql", "")}""".strip()
        documents.append(
            RagDocument(
                id=_stable_id("sales_query", f"{index}:{entry.get('question', '')}"),
                content=content,
                embedding_text=entry.get("embedding_text", ""),
                metadata={
                    "type": "query",
                    "intent": entry.get("intent", ""),
                    "sql": entry.get("sql", ""),
                },
            )
        )
    return documents


class _EmbeddingModel:
    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(PURCHASE_RAG_EMBEDDING_MODEL)

    def encode(self, texts: list[str]) -> list[list[float]]:
        return [e.tolist() for e in self.model.encode(texts, normalize_embeddings=True)]


class _SalesRagStore:
    def __init__(self):
        import chromadb
        self.embedding_model = _EmbeddingModel()
        self.client = chromadb.PersistentClient(path=str(SALES_RAG_PERSIST_DIR))
        self.schema_collection = self.client.get_or_create_collection("sales_tables")
        self.query_collection = self.client.get_or_create_collection("sales_queries")
        self._ensure_indexed(self.schema_collection, _table_documents())
        self._ensure_indexed(self.query_collection, _query_documents())

    def _ensure_indexed(self, collection, documents: list[RagDocument]):
        existing_count = collection.count()
        if existing_count == len(documents):
            return
        if existing_count:
            existing = collection.get(include=[])
            ids = existing.get("ids") or []
            if ids:
                collection.delete(ids=ids)
        embeddings = self.embedding_model.encode([d.embedding_text or d.content for d in documents])
        collection.add(
            ids=[d.id for d in documents],
            documents=[d.content for d in documents],
            metadatas=[d.metadata for d in documents],
            embeddings=embeddings,
        )

    def retrieve(self, question: str, top_k: int = 2) -> dict[str, list[dict]]:
        q_embed = self.embedding_model.encode([question])[0]

        def _search(col):
            res = col.query(query_embeddings=[q_embed], n_results=min(top_k, col.count()))
            docs = []
            if res["documents"] and res["documents"][0]:
                for doc, meta in zip(res["documents"][0], res["metadatas"][0]):
                    docs.append({"content": doc, "metadata": meta})
            return docs

        return {
            "schema": _search(self.schema_collection),
            "queries": _search(self.query_collection),
        }


_STORE: _SalesRagStore | None = None


def _get_store() -> _SalesRagStore:
    global _STORE
    if _STORE is None:
        _STORE = _SalesRagStore()
    return _STORE


def _extract_sql(text: str) -> str:
    cleaned = text.strip()
    fenced = re.search(r"```(?:sql)?\s*(.*?)```", cleaned, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        cleaned = fenced.group(1).strip()
    match = re.search(r"\bselect\b.*", cleaned, flags=re.IGNORECASE | re.DOTALL)
    if match:
        cleaned = match.group(0).strip()
    return cleaned.rstrip(";").strip()


SALES_SQL_SYSTEM = """You are a SAP HANA SQL expert for SAP Business One SALES queries.

Return ONLY one valid SAP HANA SELECT query — no explanation, no markdown, no code fences.

STRICT RULES:
- Always alias tables: FROM ORDR T0, JOIN OCRD T1 ON ...
- Use alias when referencing columns: T0."DocTotal", T1."CardName"
- ALWAYS wrap EVERY column name in double quotes: T0."DocEntry" WITHOUT EXCEPTION
- Use LIMIT N for row limiting, not TOP
- Use IFNULL() not ISNULL()
- Use CURRENT_DATE for today's date
- Use COALESCE for null handling
- Never use semicolons
- Never use CTEs unless absolutely required
- Only use tables: ORDR, RDR1, OINV, INV1, OCRD, OITM

STATUS RULES:
- "DocStatus" = 'O' means Open, 'C' means Closed
- "CANCELED" = 'Y' means Cancelled

SAP SALES TABLES:
- Sales Orders: header=ORDR, lines=RDR1 (join on "DocEntry")
- AR Invoices:  header=OINV, lines=INV1 (join on "DocEntry")
- Customers: OCRD (join ORDR or OINV on "CardCode")
- Items:     OITM (join RDR1 or INV1 on "ItemCode")
"""


def generate_sales_sql(question: str) -> str:
    store = _get_store()
    retrieval = store.retrieve(question)
    schema_ctx = "\n\n--\n\n".join(d["content"] for d in retrieval["schema"])
    queries_ctx = "\n\n--\n\n".join(d["content"] for d in retrieval["queries"])

    messages = [
        {"role": "system", "content": SALES_SQL_SYSTEM},
        {
            "role": "user",
            "content": (
                f"SCHEMA_DETAILS:\n{schema_ctx or 'No schema found'}\n\n"
                f"QUERY_EXAMPLES:\n{queries_ctx or 'No examples found'}\n\n"
                f"USER_QUERY: {question}\nSQL:"
            ),
        },
    ]
    raw = groq_chat_completion(messages, temperature=0.1, max_tokens=512, timeout=60)
    return _extract_sql(raw)
