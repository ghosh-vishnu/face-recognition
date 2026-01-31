"""
Production config from environment.
"""
import os
from pathlib import Path

# Base
ENV = os.getenv("ENV", "development")
DEBUG = os.getenv("DEBUG", "0").lower() in ("1", "true", "yes")

# Database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./face_verify.db",
)

# Storage: directory for verified images (use S3/GCS path in production if needed)
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# CORS: in production set NODE_APP_ORIGIN or CORS_ORIGINS
CORS_ORIGINS_STR = os.getenv("CORS_ORIGINS", "*")
CORS_ORIGINS = [o.strip() for o in CORS_ORIGINS_STR.split(",") if o.strip()]

# Optional: API key for server-to-server (Node.js -> this service)
API_KEY_HEADER = "X-API-Key"
API_KEY = os.getenv("API_KEY", "")  # empty = no auth

# Limits
MAX_IMAGE_SIZE_MB = int(os.getenv("MAX_IMAGE_SIZE_MB", "10"))
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024
