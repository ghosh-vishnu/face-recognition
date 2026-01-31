# Backend - Face Verification API

Production-ready FastAPI backend for face verification using InsightFace.

## Features

-  Face detection using InsightFace (Buffalo-L model)
-  ArcFace embeddings (512-dimensional)
-  Quality checks (blur, brightness, face size)
-  Cosine similarity comparison
-  Pairwise verification for 3 images
-  Comprehensive error handling
-  API documentation (Swagger/ReDoc)

## Installation

### Prerequisites

- Python 3.10 or higher
- pip

### Setup

1. **Create virtual environment:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Download models:**

First run will automatically download InsightFace models (~500MB).

## Usage

### Start the server:

```bash
# Development mode (with auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Test the API:

```bash
# Health check
curl http://localhost:8000/api/health

# Verify faces
curl -X POST http://localhost:8000/api/verify \
  -F "image1=@face1.jpg" \
  -F "image2=@face2.jpg" \
  -F "image3=@face3.jpg"
```

## API Endpoints

### POST /api/verify

Verify if 3 images contain the same person.

**Request:**
- Content-Type: `multipart/form-data`
- Files: `image1`, `image2`, `image3` (JPEG/PNG)

**Response:**
```json
{
  "result": "SAME_PERSON",
  "confidence": 0.87,
  "similarity": {
    "img1_img2": 0.88,
    "img1_img3": 0.86,
    "img2_img3": 0.87
  },
  "analysis": {
    "min_similarity": 0.86,
    "max_similarity": 0.88,
    "avg_similarity": 0.87,
    "threshold_used": 0.75
  },
  "message": "All 3 images contain the SAME person (confidence: 87%)"
}
```

### GET /api/health

Check API health and model status.

## Configuration

### Quality Thresholds

Edit `app/services/quality_check.py`:

```python
MIN_BLUR_SCORE = 100.0  # Laplacian variance
MIN_BRIGHTNESS = 30
MAX_BRIGHTNESS = 225
MIN_FACE_SIZE = 80  # pixels
MIN_FACE_SCORE = 0.7  # detection confidence
```

### Similarity Threshold

Edit `app/services/similarity.py`:

```python
SAME_PERSON_THRESHOLD = 0.75  # Cosine similarity
```

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── api/
│   │   └── verify.py        # Verification endpoint
│   ├── services/
│   │   ├── face_detector.py # Face detection
│   │   ├── embedding.py     # Embedding extraction
│   │   ├── similarity.py    # Similarity computation
│   │   └── quality_check.py # Quality validation
│   ├── schemas/
│   │   └── response.py      # Pydantic models
│   └── utils/
│       └── image_utils.py   # Image preprocessing
├── requirements.txt
└── README.md
```

## Performance

### Optimization Tips

1. **Use GPU acceleration:**
```python
# In face_detector.py
providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
```

2. **Adjust detection size:**
```python
# Smaller = faster, larger = more accurate
det_size=(640, 640)  # Current
det_size=(320, 320)  # Faster
```

3. **Enable workers:**
```bash
uvicorn app.main:app --workers 4
```

## Troubleshooting

### Model download fails

```bash
# Manually download models
mkdir -p ~/.insightface/models
# Download from: https://github.com/deepinsight/insightface/releases
```

### Out of memory

Reduce `det_size` or process images sequentially.

### Slow processing

Use GPU or reduce image resolution before upload.

## Security

-  File size limits (10MB)
-  Format validation (JPEG/PNG only)
-  Single face validation
-  Quality checks
-  Add rate limiting in production
-  Add authentication in production

## License

MIT
