# SalesMirror

SalesMirror is a local-first SaaS MVP for uploading a sales call audio file, transcribing it, and generating a sales coaching report.

The first version does not use OpenAI or any paid GPT API. The AI pipeline is provider-based:

- Transcription: mock provider by default, optional local `faster-whisper`.
- Analysis: mock provider by default, optional local Ollama.
- Providers are isolated behind service classes so they can be swapped later.

This project intentionally does not include payments, auth, teams, CRM integrations, model training, or fine-tuning.

## Project Structure

```text
salesmirror/
  frontend/   Next.js TypeScript app
  backend/    FastAPI API
  sample_mock_transcript.txt
  .env.example
```

## Run Backend

```powershell
cd C:\Users\serfu\OneDrive\Desktop\projects\salescall\salesmirror\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Backend API: `http://localhost:8000`

SQLite is used by default and creates `salesmirror.db` locally. To use PostgreSQL, set `DATABASE_URL` before starting the backend:

```powershell
$env:DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/salesmirror"
uvicorn app.main:app --reload --port 8000
```

## Run Frontend

```powershell
cd C:\Users\serfu\OneDrive\Desktop\projects\salescall\salesmirror\frontend
npm install
npm run dev
```

Frontend app: `http://localhost:3000`

The frontend expects the backend at `http://localhost:8000`. Override with `NEXT_PUBLIC_API_BASE_URL` if needed.

## Environment

Copy `.env.example` to `backend/.env` for backend AI settings:

```env
WHISPER_MODEL_SIZE=base
USE_MOCK_TRANSCRIPTION=true
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
USE_MOCK_LLM=true
```

Mock mode is the default and requires no local AI install.

## Test With Mock AI

1. Start backend and frontend.
2. Open `http://localhost:3000/upload`.
3. Upload a non-empty `.mp3`, `.wav`, `.m4a`, or `.webm` file.
4. Click `Transcribe`.
5. Click `Analyze`.
6. Click `View Report`.

Supported upload extensions are `.mp3`, `.wav`, `.m4a`, and `.webm`. Empty files are rejected.

To seed a demo report without uploading audio:

```powershell
cd C:\Users\serfu\OneDrive\Desktop\projects\salescall\salesmirror\backend
.\.venv\Scripts\Activate.ps1
python scripts\seed_demo.py
```

Then open `http://localhost:3000/calls`.

## Install Ollama

Install Ollama from the official download page:

- https://ollama.com/download

After installation, Ollama serves its local API at `http://localhost:11434/api`.

Pull a local model:

```powershell
ollama pull qwen2.5:7b
```

Check installed models:

```powershell
ollama ls
```

If Ollama is not already running:

```powershell
ollama serve
```

## Install faster-whisper

Install the optional local transcription dependency:

```powershell
cd C:\Users\serfu\OneDrive\Desktop\projects\salescall\salesmirror\backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements-local-ai.txt
```

The current implementation runs faster-whisper on CPU with `compute_type="int8"` for broad local compatibility. Set `WHISPER_MODEL_SIZE` to a faster or more accurate model size as needed, for example `tiny`, `base`, `small`, or `medium`.

## Run With Real Local AI

Create or update `backend/.env`:

```env
WHISPER_MODEL_SIZE=base
USE_MOCK_TRANSCRIPTION=false
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
USE_MOCK_LLM=false
```

Then restart the backend:

```powershell
cd C:\Users\serfu\OneDrive\Desktop\projects\salescall\salesmirror\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

Run the same upload -> transcribe -> analyze flow in the frontend.

## Testing Ollama Analysis Locally

1. Install Ollama from `https://ollama.com/download`.
2. Pull the local model configured in `.env`:

```powershell
ollama pull qwen2.5:7b
```

3. Start Ollama if it is not already running:

```powershell
ollama serve
```

4. Set `backend/.env`:

```env
USE_MOCK_LLM=false
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
```

5. Run the backend:

```powershell
cd C:\Users\serfu\OneDrive\Desktop\projects\salescall\salesmirror\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

6. Run the backend-only Ollama smoke test:

```powershell
python scripts\test_ollama_analysis.py
```

The script loads `data/samples/price_objection_sales_call.txt`, calls the Ollama provider directly, validates the SalesMirror analysis schema, prints the JSON, and prints `PASS` or `FAIL`.

7. Test from the frontend by uploading a call, transcribing it, and clicking `Analyze`.

## Comparing Local Ollama Models

Pull the local models you want to compare:

```powershell
ollama pull qwen2.5:7b
ollama pull dolphin-llama3:latest
```

Run the backend-only comparison script:

```powershell
cd C:\Users\serfu\OneDrive\Desktop\projects\salescall\salesmirror\backend
.\.venv\Scripts\Activate.ps1
python scripts\compare_ollama_models.py qwen2.5:7b dolphin-llama3:latest
```

The script reads transcripts from `data/samples/`, calls each model through the Ollama provider, validates every output with the SalesMirror schema, prints a terminal comparison report, and saves local results to:

```text
backend/eval_results/ollama_model_comparison.json
```

Generated evaluation result JSON files are ignored by git because future results may contain private transcript text or model output.

Use [docs/model_review_template.md](docs/model_review_template.md) to manually compare:

- JSON reliability
- sales reasoning quality
- objection detection
- discovery-question detection
- closing and follow-up detection
- usefulness of suggested improvements
- Turkish and English understanding
- report readability

Choose the default model by setting `OLLAMA_MODEL` in `backend/.env`:

```env
OLLAMA_MODEL=qwen2.5:7b
```

## Testing faster-whisper Locally

Install optional local transcription dependencies:

```powershell
cd C:\Users\serfu\OneDrive\Desktop\projects\salescall\salesmirror\backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements-local-ai.txt
```

Set `backend/.env`:

```env
WHISPER_MODEL_SIZE=base
USE_MOCK_TRANSCRIPTION=false
```

Run the backend-only transcription smoke test with a real audio file:

```powershell
python scripts\test_faster_whisper_transcription.py C:\path\to\audio.webm
```

The script calls the faster-whisper provider directly, prints the transcript, and prints `PASS` or `FAIL`.

## Backend Endpoints

- `POST /calls/upload`
- `POST /calls/{call_id}/transcribe`
- `POST /calls/{call_id}/analyze`
- `GET /calls`
- `GET /calls/{call_id}`
- `GET /calls/{call_id}/report.txt`
- `GET /health`

## Provider Architecture

Transcription providers:

- `backend/app/services/transcription/base.py`
- `backend/app/services/transcription/mock_transcription.py`
- `backend/app/services/transcription/faster_whisper_transcription.py`

LLM providers:

- `backend/app/services/llm/base.py`
- `backend/app/services/llm/mock_llm.py`
- `backend/app/services/llm/ollama_llm.py`

Rubric:

- `backend/app/services/analysis/rubric.py`

## Data and Model Training Plan

This MVP is currently for learning and testing sales call analysis. Do not fine-tune a model yet.

Phase 1: Prompt + rubric

- Improve the sales coaching rubric.
- Test whether Ollama can return valid JSON consistently.
- Compare model output against expected coaching reports.

Phase 2: Sample transcripts

- Use synthetic transcripts in `data/samples/`.
- Cover good calls, weak calls, price objections, poor discovery, and strong closing.
- Keep examples realistic but free of real customer data.

Phase 3: Evaluation dataset

- Use `data/eval/sales_calls_eval.jsonl` to test output quality.
- Do not train on eval examples.
- Track whether scores, mistakes, missed questions, and suggested responses match the transcript.

Phase 4: Local Ollama testing

- Run Ollama locally with `USE_MOCK_LLM=false`.
- Send sample transcripts through the analysis prompt.
- Check JSON validity, scoring consistency, and usefulness of feedback.

Phase 5: Future LoRA fine-tuning

- Only consider LoRA fine-tuning after the rubric, prompt, and labels are stable.
- Collect at least 100 to 300 high-quality labeled examples first.
- Keep fine-tuning local or privacy-safe; do not add paid APIs for this MVP.

## Privacy and Security Notes

Real sales call recordings may contain personal data, confidential business details, customer names, phone numbers, email addresses, pricing, or contract terms.

Do not upload real customer calls unless consent, retention policy, deletion policy, and access controls are handled.

For this MVP, uploaded files are stored locally in `backend/storage/uploads/` and are ignored by git. No API keys are hardcoded.

## Known Limitations

- Speaker diarization is not implemented.
- Talk ratio feedback is qualitative only.
- Ollama JSON quality depends on the local model.
- faster-whisper can be slow on CPU for long calls.
- Text report export is implemented; PDF export is not.
- Database migrations are not implemented yet.
