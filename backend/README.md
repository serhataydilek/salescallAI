# SalesMirror Backend

FastAPI backend for the local-first SalesMirror MVP.

## Run Locally

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

SQLite is used by default. Set `DATABASE_URL` to use PostgreSQL.

Run migrations before starting the backend against a fresh database:

```powershell
.\.venv\Scripts\alembic.exe upgrade head
```

SQLite is the default local MVP database. PostgreSQL can be used by setting `DATABASE_URL` before running migrations and starting the app. Do not commit local database files.

If you already have a pre-Alembic local SQLite database with data, back it up first. Use `alembic stamp head` only when the existing schema already matches the current models.

Create a new migration after changing SQLAlchemy models:

```powershell
.\.venv\Scripts\alembic.exe revision --autogenerate -m "message"
```

The backend no longer creates tables unconditionally on startup. Alembic is the normal schema path. For one-off local recovery only, set `SALESMIRROR_AUTO_CREATE_TABLES=true` before starting the backend.

## Environment

The backend app and backend scripts load local settings from:

```text
backend/.env
```

Create it from the repo example:

```powershell
copy ..\.env.example .env
```

Never commit real `.env` files.

## AI Providers

Mock providers are enabled by default:

```env
WHISPER_MODEL_SIZE=base
USE_MOCK_TRANSCRIPTION=true
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
USE_MOCK_LLM=true
```

For local AI:

```powershell
pip install -r requirements-local-ai.txt
ollama pull qwen2.5:7b
```

Then set:

```env
USE_MOCK_TRANSCRIPTION=false
USE_MOCK_LLM=false
WHISPER_MODEL_SIZE=base
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
```

## Smoke Tests

Run backend regression tests:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Test Ollama analysis without the frontend:

```powershell
python scripts\test_ollama_analysis.py
```

Test faster-whisper transcription without the frontend:

```powershell
python scripts\test_faster_whisper_transcription.py C:\path\to\audio.webm
```

Test the full local AI pipeline without the frontend:

```powershell
python scripts\test_local_ai_pipeline.py C:\path\to\audio.webm
```

## Seed Demo Data

```powershell
python scripts\seed_demo.py
```

This creates one analyzed demo call using `sample_mock_transcript.txt`.
