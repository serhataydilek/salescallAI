from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")

from app.database import Base, engine
from app.routers.calls import router as calls_router

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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
