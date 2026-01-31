"""
Save verified images to disk and create DB records.
"""
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from app.config import UPLOAD_DIR
from app.db.models import Image
from app.db.database import SessionLocal


def _subdir() -> Path:
    now = datetime.utcnow()
    d = UPLOAD_DIR / str(now.year) / f"{now.month:02d}" / f"{now.day:02d}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _ext_from_mimetype(mimetype: Optional[str], filename: str) -> str:
    if mimetype:
        if "jpeg" in mimetype or "jpg" in mimetype:
            return ".jpg"
        if "png" in mimetype:
            return ".png"
    suf = Path(filename).suffix.lower()
    return suf if suf in (".jpg", ".jpeg", ".png") else ".jpg"


def save_verified_image(
    image_bytes: bytes,
    original_filename: str,
    mimetype: Optional[str],
    user_id: Optional[str],
) -> Image:
    """Save image to disk and create verified Image record."""
    subdir = _subdir()
    ext = _ext_from_mimetype(mimetype, original_filename)
    name = f"{uuid.uuid4().hex}{ext}"
    storage_path = subdir / name
    storage_path.write_bytes(image_bytes)
    # Store path as string (relative to UPLOAD_DIR or absolute)
    path_str = str(storage_path)

    db = SessionLocal()
    try:
        rec = Image(
            user_id=user_id,
            original_filename=original_filename,
            storage_path=path_str,
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
    """Save multiple images and return Image records in order."""
    return [
        save_verified_image(data[0], data[1], data[2], user_id)
        for data in items
    ]
