"""
Production config from environment.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root; override=True so project .env wins over system/shell env
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path, override=True)

# Base
ENV = os.getenv("ENV", "development")
DEBUG = os.getenv("DEBUG", "0").lower() in ("1", "true", "yes")

# Database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./face_verify.db",
)

# Storage: local fallback directory (used only when Cloudinary not configured)
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Cloudinary (primary storage for verified images) — strip to avoid "Unknown API key"
CLOUDINARY_CLOUD_NAME = (os.getenv("CLOUDINARY_CLOUD_NAME") or "").strip()
CLOUDINARY_API_KEY = (os.getenv("CLOUDINARY_API_KEY") or "").strip()
CLOUDINARY_API_SECRET = (os.getenv("CLOUDINARY_API_SECRET") or "").strip()
CLOUDINARY_FOLDER = (os.getenv("CLOUDINARY_FOLDER") or "face_verify").strip() or "face_verify"
USE_CLOUDINARY = bool(CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET)

# CORS: in production set NODE_APP_ORIGIN or CORS_ORIGINS
CORS_ORIGINS_STR = os.getenv("CORS_ORIGINS", "*")
CORS_ORIGINS = [o.strip() for o in CORS_ORIGINS_STR.split(",") if o.strip()]

# Optional: API key for server-to-server (Node.js -> this service)
API_KEY_HEADER = "X-API-Key"
API_KEY = os.getenv("API_KEY", "")  # empty = no auth

# Limits
MAX_IMAGE_SIZE_MB = int(os.getenv("MAX_IMAGE_SIZE_MB", "10"))
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024
