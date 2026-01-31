# Face Verification API — Reference

Base URL: `http://localhost:8000` (or your deployed URL)

---

## GET /

Service info and list of endpoints.

**Response (200)**

```json
{
  "name": "Face Verification API",
  "version": "1.0.0",
  "status": "running",
  "docs": "/docs",
  "endpoints": {
    "verify": "POST /api/verify",
    "verify_and_store": "POST /api/verify-and-store",
    "health": "GET /api/health"
  }
}
```

---

## GET /api/health

Health check and model loaded status.

**Response (200)**

```json
{
  "status": "healthy",
  "model_loaded": true,
  "version": "1.0.0"
}
```

- `status`: `"healthy"` | `"initializing"` | `"unhealthy"`
- `model_loaded`: `true` when face model is ready

**Example**

```bash
curl http://localhost:8000/api/health
```

---

## POST /api/verify

Verify that 3 images contain the **same person**. Does **not** store images.

**Request**

- **Content-Type:** `multipart/form-data`
- **Body:**
  - `image1` (file, required) — JPEG/PNG
  - `image2` (file, required)
  - `image3` (file, required)

**Response 200 — Same person**

```json
{
  "result": "SAME_PERSON",
  "confidence": 0.92,
  "similarity": {
    "img1_img2": 0.91,
    "img1_img3": 0.89,
    "img2_img3": 0.94
  },
  "analysis": {
    "min_similarity": 0.89,
    "max_similarity": 0.94,
    "avg_similarity": 0.91,
    "std_similarity": 0.025,
    "threshold_used": 0.75,
    "all_pairs_pass": true
  },
  "image_analyses": [...],
  "message": "All 3 images contain the SAME person (confidence: 92.00%)"
}
```

**Response 200 — Different person**

```json
{
  "result": "DIFFERENT_PERSON",
  "confidence": 0.25,
  "similarity": { "img1_img2": 0.3, "img1_img3": 0.2, "img2_img3": 0.25 },
  "message": "Images contain DIFFERENT persons (confidence: 25.00%)"
}
```

**Errors**

- **400** — Invalid image, no face, multiple faces, or quality check failed. `detail` is a string (e.g. `"image2: No face detected in image"`).
- **500** — Server error.

**Example**

```bash
curl -X POST "http://localhost:8000/api/verify" \
  -F "image1=@face1.jpg" \
  -F "image2=@face2.jpg" \
  -F "image3=@face3.jpg"
```

---

## POST /api/verify-and-store

Verify that 3 images are the **same person**. If yes, **store** images in DB and return stored image info. If not, return **400** and do **not** store.

**Request**

- **Content-Type:** `multipart/form-data`
- **Body:**
  - `image1` (file, required) — JPEG/PNG
  - `image2` (file, required)
  - `image3` (file, required)
  - `user_id` (string, optional) — Your app’s user ID to associate with stored images

**Response 200 — Success (same person, stored)**

```json
{
  "result": "SAME_PERSON",
  "confidence": 0.92,
  "similarity": {
    "img1_img2": 0.91,
    "img1_img3": 0.89,
    "img2_img3": 0.94
  },
  "message": "All 3 images verified as same person and stored successfully.",
  "stored_images": [
    {
      "id": 1,
      "storage_path": "uploads/2026/01/31/abc123.jpg",
      "original_filename": "photo1.jpg",
      "mimetype": "image/jpeg",
      "size_bytes": 12345
    },
    { "id": 2, "storage_path": "...", "original_filename": "photo2.jpg", "mimetype": "image/jpeg", "size_bytes": 11200 },
    { "id": 3, "storage_path": "...", "original_filename": "photo3.jpg", "mimetype": "image/jpeg", "size_bytes": 13400 }
  ],
  "image_analyses": [...]
}
```

**Response 400 — Different person (not stored)**

```json
{
  "detail": {
    "code": "DIFFERENT_PERSON",
    "message": "Images do not appear to be the same person (confidence: 45.00%). Verification failed.",
    "confidence": 0.45,
    "processing_time_seconds": 12.5
  }
}
```

**Response 400 — Face/quality error**

`detail` is a string, e.g. `"image2: No face detected in image"` or `"image1: Quality check failed - blur: Too blurry"`.

**Example**

```bash
curl -X POST "http://localhost:8000/api/verify-and-store" \
  -F "image1=@photo1.jpg" \
  -F "image2=@photo2.jpg" \
  -F "image3=@photo3.jpg" \
  -F "user_id=user_abc123"
```

---

## Postman

Import **`Face_Verification_API.postman_collection.json`**, set variable **`base_url`** (e.g. `http://localhost:8000`), and run the requests. All endpoints above are included with examples.
