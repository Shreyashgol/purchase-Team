import logging

from fastapi import FastAPI

from app.api import auth, purchase_returns
from app.config import API_PREFIX, APP_NAME
from app.db.base import init_db_pool


logging.basicConfig(level=logging.INFO)

app = FastAPI(title=APP_NAME)

app.include_router(auth.router, tags=["Auth"])
app.include_router(purchase_returns.router, prefix=API_PREFIX, tags=["Purchase Returns"])


@app.on_event("startup")
async def startup_event():
    init_db_pool()


@app.get("/")
def root():
    return {"message": f"{APP_NAME} is running"}
