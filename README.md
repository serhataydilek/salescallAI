# SalesMirror

SalesMirror is a local-first sales call coaching app. It lets you upload a call recording or paste a transcript, generate a coaching report, review score trends, and export or restore local data.

The default setup uses mock AI providers so the app can be demoed without Ollama, faster-whisper, paid APIs, auth, or external services. Optional local AI providers are available when you want real local transcription and analysis:

- Transcription: mock provider by default, optional local `faster-whisper`.
- Analysis: mock provider by default, optional local Ollama.
- Providers are isolated behind service classes.

This project intentionally does not include payments, auth, teams, CRM integrations, model training, or fine-tuning.

## Finished Local App

Current show-ready flow:

- Analyze audio uploads or pasted transcripts.
- Edit transcripts and re-run analysis.
- View polished coaching reports with scores, mistakes, missed questions, suggested improvements, and example responses.
- Print reports or save them as PDF from the browser print dialog.
- Search, filter, sort, delete, and clear local calls.
- View analytics, score distribution, and score trends.
- Export calls and analytics locally.
- Restore calls from JSON backup without restoring uploaded audio binaries.
- Run backend regression tests with mock providers only.

## Project Structure

```text
salesmirror/
  frontend/   Next.js TypeScript app
  backend/    FastAPI API
  data/       sample transcripts and evaluation examples
  docs/       review templates and data strategy notes
  .env.example
```

## Quick Demo

Use the mock-provider demo when you want the fastest reliable walkthrough:

1. Start the backend.
2. Start the frontend.
3. Seed one analyzed call:

```powershell
cd salesmirror\backend
.\.venv\Scripts\python.exe scripts\seed_demo.py
```

4. Open `http://localhost:3000`.
5. Walk through the dashboard, latest calls, the call report, transcript editing, report print/download, calls search/filtering, JSON export, and restore preview.

For a live creation demo, open `http://localhost:3000/upload`, expand `Already have a transcript?`, paste `data/samples/good_sales_call.txt`, and click `Analyze Transcript`. This avoids waiting for local audio transcription and does not require Ollama.

## Screenshot Checklist

Capture these screens if you need a README or portfolio image set:

- Dashboard with at least one analyzed call.
- Upload page showing the audio flow and transcript shortcut.
- Generated coaching report with score breakdown and recommendations.
- Calls page with filters, export buttons, and the collapsed Backup and restore section.
- Backup and restore section after `Preview Restore`.

## Demo Notes

- Mock mode is the recommended show path because it requires no Ollama or faster-whisper.
- Use synthetic sample transcripts from `data/samples/`; do not demo with private customer calls.
- Browser print is the supported PDF path.
- Uploaded audio files are local-only and are not embedded in exports or restored from backups.
- The Danger Zone clear-all control is intentionally de-emphasized; normal cleanup should use per-call delete.

## Run Backend

```powershell
cd salesmirror\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\.venv\Scripts\alembic.exe upgrade head
uvicorn app.main:app --reload --port 8000
```

Backend API: `http://localhost:8000`

SQLite is used by default and creates `salesmirror.db` locally after migrations run. To use PostgreSQL, set `DATABASE_URL` before running migrations and starting the backend:

```powershell
$env:DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/salesmirror"
.\.venv\Scripts\alembic.exe upgrade head
uvicorn app.main:app --reload --port 8000
```

Create a new migration after changing backend SQLAlchemy models:

```powershell
cd salesmirror\backend
.\.venv\Scripts\alembic.exe revision --autogenerate -m "message"
```

Do not commit local database files.

## Run Frontend

```powershell
cd salesmirror\frontend
npm install
npm run dev
```

Frontend app: `http://localhost:3000`

The frontend expects the backend at `http://localhost:8000`. Override with `NEXT_PUBLIC_API_BASE_URL` if needed.

## Environment

The backend loads environment variables from:

```text
backend/.env
```

Create it from the committed example:

```powershell
copy .env.example backend\.env
```

Never commit real `.env` files. `.env`, `backend/.env`, and `frontend/.env` are ignored by git.

Safer mock development mode:

```env
WHISPER_MODEL_SIZE=base
USE_MOCK_TRANSCRIPTION=true
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
USE_MOCK_LLM=true
```

Mock mode requires no Ollama or faster-whisper install.

Real local AI mode:

```env
USE_MOCK_TRANSCRIPTION=false
USE_MOCK_LLM=false
WHISPER_MODEL_SIZE=base
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
```

Real local AI mode requires Ollama running with `qwen2.5:7b` pulled and faster-whisper dependencies installed.

## Test With Mock AI

1. Start backend and frontend.
2. Open `http://localhost:3000/upload`.
3. Paste a sample transcript or upload a short audio file.
4. Click `Analyze Transcript` or `Analyze Audio Call`.
5. SalesMirror creates the call, analyzes it, and opens the report automatically.

Supported upload extensions are `.mp3`, `.wav`, `.m4a`, and `.webm`. Empty files are rejected.

To seed a demo report without uploading audio:

```powershell
cd salesmirror\backend
.\.venv\Scripts\Activate.ps1
python scripts\seed_demo.py
```

Then open `http://localhost:3000/calls` or `http://localhost:3000`.

## Recommended Live Demo Flow

1. Start from the dashboard and show totals, score trend, and latest activity.
2. Open `Calls` and show search, filters, JSON/CSV export, and the secondary Backup and restore section.
3. Open an analyzed call report and show the score breakdown, coaching notes, transcript editor, print, and text report download.
4. Open `Upload`, expand `Already have a transcript?`, paste a sample transcript, and generate a fresh report.
5. Return to the dashboard to show that the new local call is reflected in analytics.

For a slower audio demo, upload a short `.wav`, `.webm`, `.mp3`, or `.m4a` file and click `Analyze Audio Call`.

If your source is video, convert it to a transcript first with VideoToText when needed:
`https://github.com/serhataydilek/videototext`

To use real local Ollama analysis instead of mock analysis, set `backend/.env`:

```env
USE_MOCK_LLM=false
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_BASE_URL=http://localhost:11434
```

## Using Direct Transcript Input

Use direct transcript input when you already have a transcript and want to test SalesMirror analysis without audio transcription. This is a secondary shortcut; the main app flow is audio upload -> transcription -> analysis -> report.

1. Start the backend and frontend.
2. Open `http://localhost:3000/upload`.
3. Expand `Already have a transcript?`.
4. Enter an optional title.
5. Paste a transcript using speaker labels, for example:

```text
Salesperson: Hi, thanks for joining today.
Customer: Happy to talk.
```

6. Click `Analyze Transcript`.
7. Wait while SalesMirror creates the call, analyzes it, and opens the report.

The analysis uses the configured provider. With `USE_MOCK_LLM=true`, it uses mock analysis. With `USE_MOCK_LLM=false`, it uses local Ollama.

This is useful for testing prompt and model quality without waiting for faster-whisper transcription.

## Editing Transcripts and Re-running Analysis

Transcripts from audio can contain mistakes. Open a call report and click `Edit Transcript` in the transcript section to correct speaker labels, wording, or missing text.

Saving a transcript:

- validates that the transcript is not empty and is at least 30 characters
- updates the stored transcript without touching the uploaded audio file
- marks the call status back to `transcribed`
- keeps the existing report visible, but shows a warning that the analysis may be outdated

Click `Re-run Analysis` after saving to analyze the corrected transcript. Re-analysis uses the current configured provider, so it is also useful after switching between mock and Ollama providers or changing the coaching rubric. If a report already exists, SalesMirror updates that analysis record instead of creating a duplicate.

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
cd salesmirror\backend
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
cd salesmirror\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

Run the same one-button audio analysis flow in the frontend.

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
cd salesmirror\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

6. Run the backend-only Ollama smoke test:

```powershell
python scripts\test_ollama_analysis.py
```

The script loads `data/samples/price_objection_sales_call.txt`, calls the Ollama provider directly, validates the SalesMirror analysis schema, prints the JSON, and prints `PASS` or `FAIL`.

7. Test from the frontend by uploading a call and clicking `Analyze Audio Call`.

## Comparing Local Ollama Models

Pull the local models you want to compare:

```powershell
ollama pull qwen2.5:7b
ollama pull dolphin-llama3:latest
```

Run the backend-only comparison script:

```powershell
cd salesmirror\backend
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
cd salesmirror\backend
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

## Testing the Full Local AI Pipeline

The app still defaults to mock providers unless you change `backend/.env`. The scripts below call the real local providers directly for testing.

Install local AI dependencies:

```powershell
cd salesmirror\backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements-local-ai.txt
```

Make sure Ollama is running and the recommended model is pulled:

```powershell
ollama pull qwen2.5:7b
ollama serve
```

Recommended `backend/.env` for the app when testing real local AI end to end:

```env
USE_MOCK_TRANSCRIPTION=false
USE_MOCK_LLM=false
WHISPER_MODEL_SIZE=base
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
```

Run the faster-whisper transcription smoke test with a short real audio file:

```powershell
python scripts\test_faster_whisper_transcription.py C:\path\to\short-audio.webm
```

Run the full local AI pipeline smoke test:

```powershell
python scripts\test_local_ai_pipeline.py C:\path\to\short-audio.webm
```

The full pipeline script transcribes the audio with faster-whisper, analyzes the transcript with Ollama, validates the SalesMirror schema, and prints the transcript plus the key coaching report fields.

After the backend-only scripts pass, test from the frontend:

1. Start the backend with the real local AI `.env` values above.
2. Start the frontend.
3. Upload the same short audio file.
4. Click `Analyze Audio Call`.
5. Review the call report after the app opens it automatically.

## Testing Real Local AI From the Frontend

The frontend uses the same one-button audio flow for mock and real local AI. Real local AI can be slower, especially CPU transcription.

Set `backend/.env`:

```env
USE_MOCK_TRANSCRIPTION=false
USE_MOCK_LLM=false
WHISPER_MODEL_SIZE=base
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
```

Start the backend:

```powershell
cd salesmirror\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

Start the frontend:

```powershell
cd salesmirror\frontend
npm run dev
```

Manual test:

1. Open `http://localhost:3000/upload`.
2. Upload a short `.wav`, `.webm`, `.mp3`, or `.m4a` file.
3. Click `Analyze Audio Call`.
4. Wait while the app uploads, transcribes, analyzes, and opens the report.
5. Confirm the report shows scores, mistakes, missed questions, suggested improvements, better example responses, summary, and transcript.
6. Click `Download Report` if analysis is available.

## Sharing Reports

SalesMirror reports can be shared from the call detail page:

- Click `Download Report` to save a polished text report with title, created date, source type, status, overall score, score label, score breakdown, coaching notes, and transcript.
- Click `Print Report` to open browser print. From there, choose `Save as PDF` if you want a PDF copy.
- Reports use the latest saved transcript and latest analysis. If you edit a transcript, click `Re-run Analysis` before sharing so the report reflects the corrected transcript.
- PDF sharing uses browser print/save-as-PDF so the app stays lightweight.

## Finding Calls

The calls page supports local search and filtering as your call history grows:

- Search by call title or transcript text.
- Filter by status, source type, and score range.
- Sort by newest, oldest, highest score, or lowest score.

## Analytics Dashboard

The home dashboard summarizes local coaching activity across calls:

- Averages and category insights use analyzed calls only.
- Calls without analysis still count toward totals and recent activity.
- Score distribution groups analyzed calls into strong, decent, weak, and poor buckets.
- Score trend uses the latest analyzed calls and shows whether scores improved, declined, or stayed unchanged.
- No external analytics provider or charting dependency is used.

## Exporting Local Data

SalesMirror supports local exports without external integrations:

- Calls can be exported as JSON or CSV from the calls page.
- Analytics can be exported as JSON from the dashboard.
- Audio files are not embedded in exports; call exports include metadata and transcript/report data only.
- Exports are useful before clearing local calls or moving data elsewhere.

## Backup and Restore

Use `Download Calls JSON` on the calls page to create a local backup of call records, transcripts, and analyses.

Use `Restore from JSON` on the calls page to import a previous SalesMirror calls JSON export. Restore creates new local call IDs and skips duplicate backups when the same title, creation date, and transcript text are already present.

Uploaded audio files are not embedded in the JSON backup and are not restored. For restored audio calls, SalesMirror keeps safe title/source metadata only and marks the audio file path as not restored.

## Deleting Calls

Use `Delete Call` from the call list or report page to remove one selected local call. This deletes the call record, transcript, analysis, and the uploaded audio file when that file is inside `backend/storage/uploads/`.

`Clear Calls` is kept as a local development utility in the calls page Danger Zone. It should not be the normal cleanup path.

## Backend Endpoints

- `POST /calls/upload`
- `POST /calls/from-transcript`
- `POST /calls/{call_id}/transcribe`
- `POST /calls/{call_id}/analyze`
- `GET /calls`
- `GET /calls/{call_id}`
- `GET /calls/{call_id}/report.txt`
- `DELETE /calls/{call_id}`
- `DELETE /calls` local/dev clear-all utility
- `GET /exports/calls.json`
- `GET /exports/calls.csv`
- `GET /exports/analytics.json`
- `POST /imports/calls.json`
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

## Evaluation Notes

SalesMirror includes lightweight local assets for reviewing analysis quality without collecting private data:

- Synthetic sample transcripts live in `data/samples/`.
- Evaluation examples live in `data/eval/sales_calls_eval.jsonl`.
- `docs/model_review_template.md` gives a manual review rubric for model comparisons.
- Generated model comparison results stay local under `backend/eval_results/` and are ignored by git.

Fine-tuning is intentionally out of scope for this local app. Do not train on evaluation examples.

## Privacy and Security Notes

Real sales call recordings may contain personal data, confidential business details, customer names, phone numbers, email addresses, pricing, or contract terms.

Do not upload real customer calls unless consent, retention policy, deletion policy, and access controls are handled.

Uploaded files are stored locally in `backend/storage/uploads/` and are ignored by git. No API keys are hardcoded.

## Known Limitations

- Speaker diarization is not implemented.
- Talk ratio feedback is qualitative only.
- Ollama JSON quality depends on the local model.
- faster-whisper can be slow on CPU for long calls.
- Text report export is implemented; PDF export is not.
