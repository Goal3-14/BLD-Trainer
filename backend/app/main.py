"""BLD Trainer FastAPI application entry point."""
from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(title="BLD Trainer API", version="0.1.0")
app.include_router(router, prefix="/api")
