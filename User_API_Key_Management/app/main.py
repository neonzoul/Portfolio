# :Modules: FastAPI Application Entrypoint
# === Purpose ===
# Bootstraps the API server, wires up lifespan events, and registers routers.

from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.routers.users_apikeys import router as apikeys_router
from app.api.routers.auth import router as auth_router
from app.db.session import create_db_and_tables


# === Lifespan (startup/shutdown) ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


# === FastAPI Application Setup ===
app = FastAPI(title="User API Key Management", lifespan=lifespan)

# --- Routers Registration ---
app.include_router(auth_router)  # Authentication endpoints (register/login)
app.include_router(apikeys_router)  # API key management endpoints under /users/me/apikeys
