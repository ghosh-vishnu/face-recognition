"""
Save verified images: Cloudinary (primary) or local disk (fallback).
"""
import io
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from app.config import UPLOAD_DIR
from app.db.database import SessionLocal
from app.db.models import Image

logger = logging.getLogger(__name__)

def _env_paths() -> list[Path]:
    """Paths to try for .env: cwd first (where uvicorn was run), then project root by file."""
    paths = [Path.cwd() / ".env"]
    root = Path(__file__).resolve().parent.parent.parent
    if root / ".env" not in paths:
        paths.append(root / ".env")
    return paths


def _get_cloudinary_config() -> tuple[str, str, str, str]:
    """Read Cloudinary credentials from .env file only (no process env)."""
    for key in list(os.environ.keys()):
        if key.startswith("CLOUDINARY_"):
            del os.environ[key]
    cloud_name = api_key = api_secret = ""
    folder = "face_verify"
    for env_path in _env_paths():
        if not env_path.exists():
            continue
        with open(env_path, encoding="utf-8-sig") as f:  # utf-8-sig strips BOM
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                k = k.strip()
                v = v.strip().replace("\r", "").replace("\n", "").strip()
                if len(v) >= 2 and v[0] in "'\"" and v[-1] == v[0]:
                    v = v[1:-1].replace("\r", "").replace("\n", "").strip()
                if k == "CLOUDINARY_CLOUD_NAME":
                    cloud_name = v
                elif k == "CLOUDINARY_API_KEY":
                    api_key = v
                elif k == "CLOUDINARY_API_SECRET":
                    api_secret = v
                elif k == "CLOUDINARY_FOLDER" and v:
                    folder = v
        if cloud_name and api_key and api_secret:
            logger.info("Cloudinary .env loaded from %s", env_path)
            break
    return cloud_name, api_key, api_secret, folder


def _upload_to_cloudinary(
    image_bytes: bytes,
    original_filename: str,
    mimetype: Optional[str],
    user_id: Optional[str],
) -> str:
    """Upload image bytes to Cloudinary. Returns secure_url. Credentials from .env file only."""
    cloud_name, api_key, api_secret, folder = _get_cloudinary_config()
    if not all([cloud_name, api_key, api_secret]):
        raise ValueError("Missing Cloudinary credentials in .env")

    # Set env BEFORE importing cloudinary — SDK reads os.environ on first import and caches it
    os.environ["CLOUDINARY_CLOUD_NAME"] = cloud_name
    os.environ["CLOUDINARY_API_KEY"] = api_key
    os.environ["CLOUDINARY_API_SECRET"] = api_secret

    import cloudinary
    import cloudinary.uploader
    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
    )
    ext = Path(original_filename).suffix.lower() or ".jpg"
    name = f"{user_id or 'anon'}_{uuid.uuid4().hex}{ext}"
    result = cloudinary.uploader.upload(
        io.BytesIO(image_bytes),
        public_id=name,
        folder=folder,
        resource_type="image",
        overwrite=False,
    )
    return result["secure_url"]


def _save_local(
    image_bytes: bytes,
    original_filename: str,
    mimetype: Optional[str],
) -> str:
    """Save to local disk. Returns path string."""
    now = datetime.utcnow()
    subdir = UPLOAD_DIR / str(now.year) / f"{now.month:02d}" / f"{now.day:02d}"
    subdir.mkdir(parents=True, exist_ok=True)
    ext = Path(original_filename).suffix.lower()
    if ext not in (".jpg", ".jpeg", ".png"):
        ext = ".jpg"
    name = f"{uuid.uuid4().hex}{ext}"
    path = subdir / name
    path.write_bytes(image_bytes)
    return str(path)


def save_verified_image(
    image_bytes: bytes,
    original_filename: str,
    mimetype: Optional[str],
    user_id: Optional[str],
) -> Image:
    """Save image to Cloudinary (if configured in .env) or local disk; create DB record."""
    cloud_name, api_key, api_secret, _ = _get_cloudinary_config()
    use_cloudinary = bool(cloud_name and api_key and api_secret)
    if use_cloudinary:
        try:
            storage_path = _upload_to_cloudinary(
                image_bytes, original_filename, mimetype, user_id
            )
        except Exception as e:
            err_msg = str(e)
            if "Invalid Signature" in err_msg:
                logger.warning(
                    "Cloudinary upload failed (Invalid Signature), falling back to local: %s — "
                    "Fix: copy API Secret again from Cloudinary Dashboard → API Keys and set "
                    "CLOUDINARY_API_SECRET in .env with no extra spaces or newlines.",
                    err_msg,
                )
            else:
                logger.warning("Cloudinary upload failed, falling back to local: %s", e)
            storage_path = _save_local(image_bytes, original_filename, mimetype)
    else:
        storage_path = _save_local(image_bytes, original_filename, mimetype)

    db = SessionLocal()
    try:
        rec = Image(
            user_id=user_id,
            original_filename=original_filename,
            storage_path=storage_path,
            mimetype=mimetype,
            size_bytes=len(image_bytes),
            verified=True,
            verified_at=datetime.utcnow(),
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        return rec
    finally:
        db.close()


def save_verified_batch(
    items: List[Tuple[bytes, str, Optional[str]]],
    user_id: Optional[str],
) -> List[Image]:
    """Save multiple images; return Image records in order."""
    return [
        save_verified_image(data[0], data[1], data[2], user_id)
        for data in items
    ]
