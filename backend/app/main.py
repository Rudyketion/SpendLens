"""FastAPI application entry point."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from . import models
from .config import get_settings
from .database import SessionLocal, init_db
from .routers import analytics, categories, statements, transactions
from .services.categorizer import CATEGORIES

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("spendlens")


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    """Initialize DB and seed baseline categories at startup."""
    init_db()
    with SessionLocal() as db:
        existing = {c.name for c in db.execute(select(models.Category)).scalars()}
        for cdef in CATEGORIES:
            if cdef.name not in existing:
                db.add(models.Category(name=cdef.name, color=cdef.color, icon=cdef.icon))
        db.commit()

    settings = get_settings()
    log.info("SpendLens started — AI categorization: %s", "ON" if settings.ai_enabled else "OFF (rule-based)")
    yield


app = FastAPI(
    title="SpendLens API",
    description=(
        "Personal finance tracker with AI-powered categorization. "
        "Upload CSV/PDF bank statements, see where your money goes."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(statements.router)
app.include_router(analytics.router)


@app.get("/", tags=["meta"])
def root():
    return {
        "name": "SpendLens API",
        "version": "0.1.0",
        "ai_enabled": settings.ai_enabled,
        "docs": "/docs",
    }


@app.get("/healthz", tags=["meta"])
def healthz():
    return {"status": "ok"}
