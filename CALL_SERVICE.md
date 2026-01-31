# Service Ko Call Kaise Kare

Ye doc batata hai ki **koi bhi backend** (Node.js, PHP, etc.) is Face Verification service ko **kaise call karega**.

---

## 1. Service ka URL (Base URL)

Service jahan chal rahi hai, wahi URL use karo:

| Scenario | Base URL |
|----------|----------|
| **Same machine** (Node.js aur ye service dono isi PC pe) | `http://localhost:8000` |
| **Different machine, same WiFi** (e.g. Node.js server 192.168.1.5 pe, ye service 192.168.1.10 pe) | `http://192.168.1.10:8000` |
| **Production** (deploy ke baad) | `https://face-verify.yourdomain.com` |

**Environment variable rakho (recommended):**

```env
FACE_VERIFY_URL=http://localhost:8000
```

---

## 2. Kaun sa endpoint call karna hai

Profile creation ke liye (3 photos verify + store):

- **Endpoint:** `POST {BASE_URL}/api/verify-and-store`
- **Content-Type:** `multipart/form-data`

**Form fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `image1` | File | Yes | Pehli image (JPEG/PNG) |
| `image2` | File | Yes | Doosri image |
| `image3` | File | Yes | Teesri image |
| `user_id` | String | No | Apne app ka user ID (optional) |

---

## 3. Response kaise handle kare

### Success (200 OK)

Sab same person — images verify ho chuki aur DB me save ho chuki.

```json
{
  "result": "SAME_PERSON",
  "confidence": 0.92,
  "similarity": { "img1_img2": 0.91, "img1_img3": 0.89, "img2_img3": 0.94 },
  "message": "All 3 images verified as same person and stored successfully.",
  "stored_images": [
    { "id": 1, "storage_path": "uploads/2026/01/31/abc.jpg", "original_filename": "photo1.jpg", "mimetype": "image/jpeg", "size_bytes": 12345 },
    { "id": 2, "storage_path": "...", "original_filename": "photo2.jpg", ... },
    { "id": 3, "storage_path": "...", "original_filename": "photo3.jpg", ... }
  ]
}
```

**Aap kya karo:** Profile create complete karo, `stored_images` me jo `id` / `storage_path` aaya wo apne DB me save kar lo (optional).

### Failure (400 Bad Request)

- **Different person** — 3 images me same person nahi hai.
- **Face / quality error** — kisi image me face nahi mila ya quality fail.

Response body me `detail` aata hai (string ya object). User ko message dikhao: *"Please upload 3 clear photos of yourself only."*

### Server error (500)

Service down ya internal error. User ko *"Verification temporarily unavailable. Try again later."* dikhao.

---

## 4. Node.js se call kaise kare

### Dependencies

```bash
npm install axios form-data
```

### Example — 3 file paths se

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

const FACE_VERIFY_URL = process.env.FACE_VERIFY_URL || 'http://localhost:8000';

async function verifyAndStorePhotos(image1Path, image2Path, image3Path, userId = null) {
  const form = new FormData();
  form.append('image1', fs.createReadStream(image1Path));
  form.append('image2', fs.createReadStream(image2Path));
  form.append('image3', fs.createReadStream(image3Path));
  if (userId) form.append('user_id', userId);

  const response = await axios.post(
    `${FACE_VERIFY_URL}/api/verify-and-store`,
    form,
    {
      headers: form.getHeaders(),
      maxBodyLength: Infinity,
      maxContentLength: Infinity,
    }
  );

  return response.data; // { result, stored_images, ... }
}
```

### Example — Multer se (files buffer me)

```javascript
// Express route: user ne 3 images upload ki (multer)
app.post('/api/profile/verify-photos', upload.fields([
  { name: 'image1', maxCount: 1 },
  { name: 'image2', maxCount: 1 },
  { name: 'image3', maxCount: 1 },
]), async (req, res) => {
  try {
    const FormData = require('form-data');
    const form = new FormData();

    form.append('image1', req.files.image1[0].buffer, {
      filename: req.files.image1[0].originalname,
      contentType: req.files.image1[0].mimetype,
    });
    form.append('image2', req.files.image2[0].buffer, {
      filename: req.files.image2[0].originalname,
      contentType: req.files.image2[0].mimetype,
    });
    form.append('image3', req.files.image3[0].buffer, {
      filename: req.files.image3[0].originalname,
      contentType: req.files.image3[0].mimetype,
    });
    if (req.user?.id) form.append('user_id', req.user.id);

    const response = await axios.post(
      `${process.env.FACE_VERIFY_URL}/api/verify-and-store`,
      form,
      {
        headers: form.getHeaders(),
        maxBodyLength: Infinity,
        maxContentLength: Infinity,
      }
    );

    return res.json(response.data);
  } catch (err) {
    if (err.response?.status === 400) {
      const d = err.response.data?.detail;
      const message = typeof d === 'string' ? d : (d?.message || 'Verification failed.');
      return res.status(400).json({ error: message, code: d?.code });
    }
    return res.status(500).json({ error: 'Verification service error. Try again later.' });
  }
});
```

---

## 5. cURL se test

```bash
# Health check
curl http://localhost:8000/api/health

# Verify and store (3 images + user_id)
curl -X POST "http://localhost:8000/api/verify-and-store" \
  -F "image1=@photo1.jpg" \
  -F "image2=@photo2.jpg" \
  -F "image3=@photo3.jpg" \
  -F "user_id=user_123"
```

---

## 6. Postman se test

1. **Import** karo: `Face_Verification_API.postman_collection.json`
2. Collection variable **`base_url`** = `http://localhost:8000` (ya jahan service chal rahi hai)
3. **POST Verify and Store** request kholo → Body → form-data me `image1`, `image2`, `image3` me 3 images select karo → **Send**

---

## Short summary

| Step | Kya karna hai |
|------|----------------|
| 1 | Service ka base URL set karo (env: `FACE_VERIFY_URL`) |
| 2 | `POST {BASE_URL}/api/verify-and-store` pe request bhejo |
| 3 | Body: `multipart/form-data` — `image1`, `image2`, `image3` (files), optional `user_id` |
| 4 | 200 → success, `stored_images` use karo; 400 → user ko retry/clear photos bolo; 500 → try again later |

Details ke liye: **API.md** (request/response format).
