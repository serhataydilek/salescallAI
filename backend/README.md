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
```

## Smoke Tests

Test Ollama analysis without the frontend:

```powershell
python scripts\test_ollama_analysis.py
```

Test faster-whisper transcription without the frontend:

```powershell
python scripts\test_faster_whisper_transcription.py C:\path\to\audio.webm
```

## Seed Demo Data

```powershell
python scripts\seed_demo.py
```

This creates one analyzed demo call using `sample_mock_transcript.txt`.
