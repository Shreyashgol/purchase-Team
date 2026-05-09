import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.db.runtime import resolve_database_connection_string
from shared.env import load_agent_env


load_agent_env(__file__)

APP_NAME = "SAP B1 Purchase Supervisor Agent"
API_PREFIX = ""

SAP_BASE_URL = os.getenv("SAP_BASE_URL", "http://localhost:50000/b1s/v1")
SAP_USERNAME = os.getenv("SAP_USERNAME", "manager")
SAP_PASSWORD = os.getenv("SAP_PASSWORD", "password")
SAP_COMPANYDB = os.getenv("SAP_COMPANYDB", "SBODEMOUS")

JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "120"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

SQL_QUERY_TIMEOUT = int(os.getenv("SQL_QUERY_TIMEOUT", "30"))
DATABASE_CONNECTION_STRING = resolve_database_connection_string()

PURCHASE_RAG_EMBEDDING_MODEL = os.getenv("PURCHASE_RAG_EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")
_purchase_rag_persist_dir = Path(os.getenv("PURCHASE_RAG_PERSIST_DIR", ".rag_chroma/purchase"))
PURCHASE_RAG_PERSIST_DIR = (
    _purchase_rag_persist_dir
    if _purchase_rag_persist_dir.is_absolute()
    else REPO_ROOT / _purchase_rag_persist_dir
)

PURCHASE_ORDER_API_URL = os.getenv(
    "PURCHASE_ORDER_API_URL",
    "http://127.0.0.1:8000/purchase-orders/parse-and-execute",
)
AP_INVOICE_API_URL = os.getenv(
    "AP_INVOICE_API_URL",
    "http://127.0.0.1:8000/ap-invoices/parse-and-execute",
)
PURCHASE_RETURN_API_URL = os.getenv(
    "PURCHASE_RETURN_API_URL",
    "http://127.0.0.1:8000/purchase-returns/parse-and-execute",
)
