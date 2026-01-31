# Face Verification API

Production-ready FastAPI service for **3-image same-person verification** (e.g. dating app profile). Verifies that three uploaded images show the same face; optionally stores verified images in the database.

## Features

- **Face detection & embedding** — DeepFace (Facenet512), single-face validation
- **Quality checks** — Blur, brightness, face size
- **Pairwise similarity** — Cosine similarity; threshold-based same-person decision
- **Verify only** — `POST /api/verify` (no storage)
- **Verify and store** — `POST /api/verify-and-store` (saves images to DB when same person)
- **Health** — `GET /api/health` (model loaded status)
- **OpenAPI** — `/docs` (Swagger), `/redoc`

## Quick start

### Prerequisites

- Python 3.10+
- pip

### Setup

```bash
# Clone / cd to project
cd backend

# Virtual environment (recommended)
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Run

```bash
# Development (auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or from Python
python -m app.main
```

First run may download models (~500MB). Then:

- **API docs:** http://localhost:8000/docs  
- **Health:** http://localhost:8000/api/health  

### Environment (optional)

Copy `.env.example` to `.env` and adjust:

| Variable        | Default              | Description                    |
|-----------------|----------------------|--------------------------------|
| `DATABASE_URL`  | `sqlite:///./face_verify.db` | DB connection string   |
| `CLOUDINARY_CLOUD_NAME` | — | Cloudinary cloud name (from dashboard) |
| `CLOUDINARY_API_KEY`    | — | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | — | Cloudinary API secret |
| `CLOUDINARY_FOLDER`     | `face_verify` | Folder name in Cloudinary |
| `UPLOAD_DIR`    | `uploads`            | Local fallback when Cloudinary not set |
| `CORS_ORIGINS`  | `*`                  | Comma-separated allowed origins |
| `MAX_IMAGE_SIZE_MB` | `10`            | Max image size (MB)            |

**Cloudinary:** When `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, and `CLOUDINARY_API_SECRET` are set, verified images are uploaded to Cloudinary. Response `stored_images[].storage_path` will be the Cloudinary **secure URL**. If not set, images are saved locally under `UPLOAD_DIR`.

## API summary

| Method | Endpoint               | Description                          |
|--------|------------------------|--------------------------------------|
| GET    | `/`                    | Service info & endpoint list          |
| GET    | `/api/health`          | Health & model loaded status          |
| POST   | `/api/verify`          | Verify 3 images (same person); no store |
| POST   | `/api/verify-and-store` | Verify 3 images; if same person, store & return image IDs |

Full request/response examples: see **[API.md](API.md)**.  
**Service ko call kaise kare (Node.js / cURL / Postman):** see **[CALL_SERVICE.md](CALL_SERVICE.md)**.

## Examples

### cURL — Health

```bash
curl http://localhost:8000/api/health
```

Example response:

```json
{
  "status": "healthy",
  "model_loaded": true,
  "version": "1.0.0"
}
```

### cURL — Verify (no store)

```bash
curl -X POST "http://localhost:8000/api/verify" \
  -F "image1=@photo1.jpg" \
  -F "image2=@photo2.jpg" \
  -F "image3=@photo3.jpg"
```

### cURL — Verify and store (for profile creation)

```bash
curl -X POST "http://localhost:8000/api/verify-and-store" \
  -F "image1=@photo1.jpg" \
  -F "image2=@photo2.jpg" \
  -F "image3=@photo3.jpg" \
  -F "user_id=user_abc123"
```

Success (200) returns `result: "SAME_PERSON"` and `stored_images` with `id`, `storage_path`, `original_filename`, etc. Failure (400) when images are not the same person or quality/face checks fail.

## Postman collection

Use **`Face_Verification_API.postman_collection.json`** for testing:

1. Open Postman → **Import** → select `Face_Verification_API.postman_collection.json`.
2. Set collection variable **`base_url`** (e.g. `http://localhost:8000`).
3. Run **Health Check**, then **POST Verify and Store** with 3 same-person images in form-data (`image1`, `image2`, `image3`; optional `user_id`).

## Project structure

```
backend/
├── app/
│   ├── main.py           # FastAPI app, startup
│   ├── config.py         # Env config
│   ├── api/
│   │   └── verify.py     # /api/verify, /api/verify-and-store, /api/health
│   ├── db/
│   │   ├── database.py   # SQLAlchemy engine, session
│   │   └── models.py     # Image model
│   ├── schemas/
│   │   └── response.py   # Pydantic response models
│   ├── services/
│   │   ├── face_detector.py
│   │   ├── embedding.py
│   │   ├── similarity.py
│   │   ├── quality_check.py
│   │   └── storage.py     # Save verified images
│   └── utils/
│       └── image_utils.py
├── Face_Verification_API.postman_collection.json
├── API.md                # API reference & examples
├── CALL_SERVICE.md       # Service ko call kaise kare (Node.js, cURL, Postman)
├── requirements.txt
└── README.md
```

## Node.js integration

For integrating this API from a Node.js (or any) backend, see **[CALL_SERVICE.md](CALL_SERVICE.md)** for:

- Base URL and endpoint
- Request/response handling
- Node.js examples (axios + FormData, Express + multer)
- cURL and Postman testing

## License

MIT
