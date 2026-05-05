import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.env import load_agent_env


load_agent_env(__file__)

APP_NAME = "SAP Purchase Team Orchestrator"

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

PURCHASE_ORDER_API_URL = os.getenv(
    "PURCHASE_ORDER_API_URL",
    "http://127.0.0.1:8002/purchase-orders/parse-and-execute",
)
AP_INVOICE_API_URL = os.getenv(
    "AP_INVOICE_API_URL",
    "http://127.0.0.1:8003/ap-invoices/parse-and-execute",
)
PURCHASE_RETURN_API_URL = os.getenv(
    "PURCHASE_RETURN_API_URL",
    "http://127.0.0.1:8004/purchase-returns/parse-and-execute",
)
