from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.routers.users_apikeys import router as apikeys_router
from app.db.session import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="User API Key Management", lifespan=lifespan)

app.include_router(apikeys_router)
