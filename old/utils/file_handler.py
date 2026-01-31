import uuid
import logging
from pathlib import Path
from typing import Tuple
import pandas as pd
from fastapi import UploadFile, HTTPException

# -------------------------------------------------------------------
# CONFIGURATION (should ideally come from env in large systems)
# -------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_BASE = BASE_DIR / "static"

UPLOAD_DIR = STATIC_BASE / "uploads"
CHART_DIR = STATIC_BASE / "charts"
REPORT_DIR = STATIC_BASE / "reports"

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".parquet"}
CHUNK_SIZE = 1024 * 1024  # 1 MB

# -------------------------------------------------------------------
# INITIALIZATION
# -------------------------------------------------------------------

for path in (UPLOAD_DIR, CHART_DIR, REPORT_DIR):
    path.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# FILE UPLOAD (SECURE & STREAMED)
# -------------------------------------------------------------------

def save_upload(file: UploadFile, dataset_id: int) -> Tuple[str, Path]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is missing")

    ext = Path(file.filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}"
        )

    dataset_dir = UPLOAD_DIR / f"dataset_{dataset_id}"
    dataset_dir.mkdir(parents=True, exist_ok=True)

    unique_name = f"{uuid.uuid4().hex}{ext}"
    target_path = dataset_dir / unique_name

    size = 0

    try:
        with open(target_path, "wb") as buffer:
            while True:
                chunk = file.file.read(CHUNK_SIZE)
                if not chunk:
                    break

                size += len(chunk)
                if size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="File size exceeds allowed limit"
                    )

                buffer.write(chunk)

    except HTTPException:
        if target_path.exists():
            target_path.unlink()
        raise

    except Exception as exc:
        if target_path.exists():
            target_path.unlink()
        logger.exception("File upload failed")
        raise HTTPException(status_code=500, detail="File upload failed") from exc

    return str(target_path), target_path

# -------------------------------------------------------------------
# DATASET LOADING (ROBUST)
# -------------------------------------------------------------------

def load_dataset(path: Path) -> pd.DataFrame:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    suffix = path.suffix.lower()

    try:
        if suffix in (".xlsx", ".xls"):
            return pd.read_excel(path)

        if suffix == ".parquet":
            return pd.read_parquet(path)

        if suffix == ".csv":
            return pd.read_csv(path)

    except Exception as exc:
        logger.exception("Failed to load dataset")
        raise ValueError("Failed to read dataset file") from exc

    raise ValueError(f"Unsupported dataset format: {suffix}")

# -------------------------------------------------------------------
# DATAFRAME SAVE (ATOMIC & SAFE)
# -------------------------------------------------------------------

def save_dataframe(df: pd.DataFrame, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    temp_path = path.with_suffix(".tmp")

    try:
        df.to_csv(temp_path, index=False)
        temp_path.replace(path)
    except Exception as exc:
        if temp_path.exists():
            temp_path.unlink()
        logger.exception("Failed to save DataFrame")
        raise

# -------------------------------------------------------------------
# CHART SAVE (SANITIZED)
# -------------------------------------------------------------------

def save_chart(fig, filename: str) -> str:

    safe_name = Path(filename).name  # prevent ../../ traversal
    target_path = CHART_DIR / safe_name

    try:
        fig.savefig(target_path, bbox_inches="tight")
    except Exception as exc:
        logger.exception("Failed to save chart")
        raise RuntimeError("Chart saving failed") from exc

    return str(target_path)
