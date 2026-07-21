from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from afridock_api.api.routes import health
from afridock_api.config import get_settings
from afridock_api.logging import configure_logging

settings = get_settings()
configure_logging(settings.api_env)

app = FastAPI(title="Afridock API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
