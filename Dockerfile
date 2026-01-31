# Face Verification API — FastAPI + DeepFace/TensorFlow
FROM python:3.11-slim

# System deps for OpenCV and psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps (use headless OpenCV in container)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip uninstall -y opencv-python 2>/dev/null || true && \
    pip install --no-cache-dir opencv-python-headless==4.9.0.80

COPY app/ ./app/
COPY .env.example .env.example

# Create data dir for SQLite + local uploads
RUN mkdir -p /app/data && chmod 777 /app/data

ENV PYTHONUNBUFFERED=1
ENV UPLOAD_DIR=/app/data/uploads
EXPOSE 8000

# Default: SQLite in /app/data if DATABASE_URL not set
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
