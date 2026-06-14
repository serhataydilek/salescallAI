import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")

from app.database import Base, engine
from app.routers.analytics import router as analytics_router
from app.routers.calls import router as calls_router
from app.routers.exports import router as exports_router
from app.routers.imports import router as imports_router

if os.getenv("SALESMIRROR_AUTO_CREATE_TABLES", "").strip().lower() in {"1", "true", "yes", "on"}:
    # Local fallback only. Use Alembic migrations for normal schema management.
    Base.metadata.create_all(bind=engine)

app = FastAPI(title="SalesMirror API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(calls_router)
app.include_router(analytics_router)
app.include_router(exports_router)
app.include_router(imports_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
