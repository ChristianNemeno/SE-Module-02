# RR-045 · Deploy FastAPI to DigitalOcean

**Linear:** REA-30 | **Branch:** `feature/rea-30-rr-045-deploy-fastapi-to-digitalocean`

## Context

Deploy the FastAPI microservice to a public HTTPS URL. HTTPS is mandatory — `getUserMedia` (camera/mic access) requires secure context on all mobile browsers. Service must auto-redeploy on push to `main`.

**Platform:** DigitalOcean 16GB CPU-Optimized Droplet ($80/mo)
- App Platform is NOT viable — hard 4GB RAM cap; WhisperX large-v3 alone needs ~3.3GB
- Combined load (large-v3 + MediaPipe + OS) peaks at ~8-10GB

**Deployment path:** GitHub Actions → DigitalOcean Container Registry → SSH deploy → Nginx reverse proxy + Let's Encrypt HTTPS

---

## Files to Create/Modify (in order)

### 1. `app/config.py`
Add three fields to `Settings`:
- `SUPABASE_URL: str = ""`
- `SUPABASE_SERVICE_KEY: str = ""` — service role key, NOT anon key (bypasses RLS)
- `ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]` — pydantic-settings parses as JSON array

### 2. `app/routers/health.py` *(new)*
Extract `HealthController` from `AnalyzeController` (currently mixed in at `analyze.py:18` and `analyze.py:46-48`).

```python
class HealthController:
    def __init__(self) -> None:
        self.router = APIRouter(tags=["health"])
        self.router.add_api_route("/health", self.health, methods=["GET"])

    async def health(self) -> dict[str, str]:
        return {"status": "ok"}
```

### 3. `app/routers/analyze.py`
- Remove `/health` route from `__init__` (line 18)
- Remove `async def health(self)` method (lines 46-48)
- Update class docstring

### 4. `app/main.py`
- Import `get_settings` and `HealthController`
- Replace hardcoded `allow_origins=["http://localhost:5173"]` with `allow_origins=get_settings().ALLOWED_ORIGINS`
- Wire in `HealthController().router`

### 5. `pyrightconfig.json`
Remove `"venvPath"` and `"venv"` keys — breaks pyright in GitHub Actions CI (no `.venv` present). Pyright auto-detects active environment.

### 6. `Dockerfile` *(new)*
```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download large-v3 into default HuggingFace cache (~/.cache/huggingface)
# whisperx.load_model() finds it there at startup with no code changes needed
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('large-v3', device='cpu', compute_type='float32')"

COPY app/ ./app/

ENV WHISPERX_MODEL=large-v3
ENV WHISPERX_DEVICE=cpu
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Notes:**
- `python:3.12-slim` — project uses PEP 695 `type X = ...` syntax, 3.11 breaks it
- Model layer before `COPY app/` — code changes don't invalidate the 3GB model cache layer
- **Expected image size: ~6-7GB** (PyTorch + whisperx + mediapipe + large-v3)

### 7. `.dockerignore` *(new)*
```
.venv/
__pycache__/
*.py[cod]
.env
.env.*
!.env.example
.git/
.github/
tests/
docs/
*.md
.pytest_cache/
pyrightconfig.json
pytest.ini
```

### 8. `.env.example`
- Replace `SUPABASE_ANON_KEY` with `SUPABASE_SERVICE_KEY`
- Add `ALLOWED_ORIGINS=["http://localhost:5173"]` with JSON array format note

### 9. `.github/workflows/deploy.yml` *(new)*
Three-job pipeline on push to `main`:

**Job 1 — `test`:** pyright + pytest with `API_KEY=test-key-for-ci`

**Job 2 — `build-and-push`** (needs: test):
- Login to DO Container Registry via `doctl`
- `docker build --cache-from latest` — reuses previous image layers, avoids re-downloading 3GB model
- Push `:<sha>` and `:latest` tags

**Job 3 — `deploy`** (needs: build-and-push):
- SSH via `appleboy/ssh-action`
- `docker pull` → `docker stop/rm` → `docker run -d --env-file /etc/readright/env -p 127.0.0.1:8000:8000`
- Retry health check loop (60s for WhisperX model load)

**Required GitHub Secrets:**
| Secret | Value |
|---|---|
| `DIGITALOCEAN_ACCESS_TOKEN` | DO personal access token (registry read/write) |
| `DO_REGISTRY_NAME` | Registry name (e.g. `readright`) |
| `DROPLET_IP` | Droplet public IP |
| `DROPLET_SSH_KEY` | Private SSH key PEM for root access |

---

## Manual Droplet Setup (One-Time)

1. **Provision** — 16GB CPU-Optimized, Ubuntu 24.04, Docker pre-installed
2. **Install** — `nginx certbot python3-certbot-nginx` + `doctl` via snap
3. **Secrets file** — `/etc/readright/env` (chmod 600): `API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `ALLOWED_ORIGINS`
4. **DNS** — `A` record: `api.readright.app → <DROPLET_IP>`
5. **Nginx** — reverse proxy to `127.0.0.1:8000`, `client_max_body_size 100M`, `proxy_read_timeout 120s`
6. **HTTPS** — `certbot --nginx -d api.readright.app` (auto-renews via systemd timer)
7. **Deploy key** — generate `ed25519` on Droplet, add to `authorized_keys`, copy private key to GitHub secret `DROPLET_SSH_KEY`
8. **First run** — manual `docker run` to verify before CI takes over
9. **Frontend** — set `VITE_FASTAPI_URL=https://api.readright.app`

---

## Risks

| Risk | Mitigation |
|---|---|
| WhisperX startup takes 15-45s | `HEALTHCHECK --start-period=60s`; deploy uses retry loop |
| 6-7GB image on first CI push | `--cache-from latest` reuses layers on subsequent pushes |
| Port 8000 exposed to internet | Bind to `127.0.0.1:8000` only; Nginx is sole public entry point |
| `ALLOWED_ORIGINS` JSON in shell | Works fine in Docker `--env-file`; in shell use single quotes |

---

## Verification (DoD Checklist)

```bash
curl https://api.readright.app/health
# → {"status":"ok"}

curl -X POST https://api.readright.app/analyze \
  -H "X-API-Key: <key>" \
  -F "file=@test.webm" \
  -F "passage_id=grade3-a"
# → AssessmentResult JSON (200)
```

- DO Registry shows image tagged with commit SHA
- Push trivial commit → CI runs → Droplet picks up new container automatically
- `git log -p | grep -i "api_key\|service_key"` — no secrets in repo
