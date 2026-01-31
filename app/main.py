"""Face Verification API — 3-image same-person verification for dating app profile."""
import os
import logging
from pathlib import Path
import uvicorn
from dotenv import load_dotenv

# Load .env if present (local dev); Docker uses env_file / -e, don't overwrite those
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path, override=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.verify import get_services, router as verify_router
from app.config import CORS_ORIGINS
from app.db import models  # noqa: F401 — register ORM
from app.db.database import Base, engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")

app = FastAPI(
    title="Face Verification API",
    description="Verify 3 images are the same person; optionally store verified images.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(verify_router, prefix="/api", tags=["verification"])


@app.get("/")
async def root():
    """Service info and endpoint list."""
    return {
        "name": "Face Verification API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "verify": "POST /api/verify",
            "verify_and_store": "POST /api/verify-and-store",
            "health": "GET /api/health",
        },
    }


@app.on_event("startup")
async def startup_event():
    """Create DB tables and load face model so /api/health reports healthy."""
    Base.metadata.create_all(bind=engine)
    try:
        get_services()
    except Exception as e:
        logging.warning("Model load at startup failed: %s. First request will retry.", e)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
