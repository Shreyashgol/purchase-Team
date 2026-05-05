import logging

from fastapi import FastAPI

from app.api import ap_invoices, auth
from app.config import API_PREFIX, APP_NAME
from app.db.base import init_db_pool


logging.basicConfig(level=logging.INFO)

app = FastAPI(title=APP_NAME)

app.include_router(auth.router, tags=["Auth"])
app.include_router(ap_invoices.router, prefix=API_PREFIX, tags=["AP Invoices"])


@app.on_event("startup")
async def startup_event():
    try:
        init_db_pool()
    except Exception as exc:
        logging.error("Failed to initialize AP invoice database: %s", str(exc))
        raise


@app.get("/")
def root():
    return {"message": f"{APP_NAME} is running"}
