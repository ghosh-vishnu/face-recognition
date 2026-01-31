# Docker Deployment — Fresh Ubuntu Server

Face Verification API ko Docker se deploy karne ke steps (fresh Ubuntu 24.04).

---

## 1. Server par Docker install karo

SSH se connect karo, phir:

```bash
# Docker install (official script)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Logout/login ya: newgrp docker
```

Docker Compose (v2) usually script ke saath aa jata hai. Check:

```bash
docker --version
docker compose version
```

---

## 2. Repo clone karo

```bash
cd /opt   # ya jahan deploy karna hai
sudo git clone https://github.com/Venturing-Digitally-VeD/Dating-App-Face-Verification-Api.git face-verify
cd face-verify
```

---

## 3. Environment file banao

```bash
cp .env.example .env
nano .env   # ya vim
```

**Zaroor set karo:**

- `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` — Cloudinary dashboard se
- `CORS_ORIGINS` — apne frontend/Node app ka URL (e.g. `https://your-app.com`)
- Optional: `DATABASE_URL` — PostgreSQL use karoge to `postgresql+psycopg2://user:pass@host:5432/face_verify`
- Optional: `API_KEY` — Node.js se call ke liye secret

Save karke exit.

---

## 4. Build aur run

```bash
sudo docker compose build --no-cache
sudo docker compose up -d
```

Logs dekhne ke liye:

```bash
sudo docker compose logs -f api
```

API chal raha hoga: **http://SERVER_IP:8000**

- Docs: http://SERVER_IP:8000/docs  
- Health: http://SERVER_IP:8000/api/health  

---

## 5. Firewall (agar port band hai)

```bash
sudo ufw allow 8000/tcp
sudo ufw enable
sudo ufw status
```

---

## Useful commands

| Command | Kaam |
|--------|------|
| `docker compose up -d` | Background mein start |
| `docker compose down` | Stop + remove containers |
| `docker compose logs -f api` | Live logs |
| `docker compose restart api` | Restart API |
| `docker compose pull && docker compose up -d --build` | Repo update ke baad rebuild + run |

---

## Nginx reverse proxy (optional)

Agar 80/443 par domain se serve karna ho:

```nginx
# /etc/nginx/sites-available/face-verify
server {
    listen 80;
    server_name api.yourdomain.com;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 10M;
    }
}
```

Enable: `sudo ln -s /etc/nginx/sites-available/face-verify /etc/nginx/sites-enabled/` then `sudo nginx -t && sudo systemctl reload nginx`

---

## Troubleshooting

- **Container start nahi ho raha:** `docker compose logs api` — env / Cloudinary / DB URL check karo.
- **Out of memory:** TensorFlow/DeepFace heavy hai; server par kam se kam 2GB RAM rakho.
- **Health unhealthy:** Pehla request slow ho sakta hai (model load); 1–2 min wait karke phir `/api/health` check karo.
