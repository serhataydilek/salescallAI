from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import Analysis, Call, CallStatus, Transcript
from app.schemas import (
    AnalysisBase,
    AnalysisOut,
    CallDetailOut,
    CallOut,
    ClearCallsResponse,
    CreateTranscriptCallRequest,
    DeleteCallResponse,
    TranscriptOut,
    UploadResponse,
)
from app.services.providers import get_llm_service, get_transcription_service
from app.services.report_service import ReportService
from app.services.title_service import generate_call_title

router = APIRouter(prefix="/calls", tags=["calls"])

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "storage" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".webm"}
MAX_UPLOAD_CHUNK_SIZE = 1024 * 1024
MIN_TRANSCRIPT_LENGTH = 30
MANUAL_TRANSCRIPT_FILE_PATH = "manual-transcript"


def get_call_with_related(db: Session, call_id: int) -> Call | None:
    return db.execute(
        select(Call).options(selectinload(Call.transcript), selectinload(Call.analysis)).where(Call.id == call_id)
    ).scalar_one_or_none()


def validate_upload_filename(filename: str | None) -> str:
    if not filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a filename.")

    safe_filename = Path(filename).name
    extension = Path(safe_filename).suffix.lower()
    if extension not in ALLOWED_AUDIO_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_AUDIO_EXTENSIONS))
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed extensions: {allowed}.")

    return safe_filename


def remove_local_upload(file_path: str) -> bool:
    if file_path == MANUAL_TRANSCRIPT_FILE_PATH:
        return False

    try:
        upload_root = UPLOAD_DIR.resolve()
        target = Path(file_path).resolve(strict=False)
    except OSError:
        return False

    if upload_root != target.parent and upload_root not in target.parents:
        return False
    if not target.exists() or not target.is_file():
        return False

    target.unlink()
    return True


@router.post("/upload", response_model=UploadResponse)
async def upload_call(file: UploadFile = File(...), db: Session = Depends(get_db)) -> UploadResponse:
    safe_filename = validate_upload_filename(file.filename)
    stored_filename = f"{uuid4().hex}_{safe_filename}"
    file_path = UPLOAD_DIR / stored_filename

    total_bytes = 0
    with file_path.open("wb") as output:
        while chunk := await file.read(MAX_UPLOAD_CHUNK_SIZE):
            total_bytes += len(chunk)
            output.write(chunk)

    if total_bytes == 0:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    call = Call(filename=safe_filename, file_path=str(file_path), status=CallStatus.uploaded)
    try:
        db.add(call)
        db.commit()
        db.refresh(call)
    except Exception as exc:
        db.rollback()
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="Could not create call record.") from exc

    return UploadResponse(call_id=call.id, filename=call.filename, status=call.status.value)


@router.post("/from-transcript", response_model=CallDetailOut)
def create_call_from_transcript(
    request: CreateTranscriptCallRequest, db: Session = Depends(get_db)
) -> CallDetailOut:
    transcript_text = request.transcript.strip()
    if not transcript_text:
        raise HTTPException(status_code=400, detail="Transcript cannot be empty.")
    if len(transcript_text) < MIN_TRANSCRIPT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Transcript must be at least {MIN_TRANSCRIPT_LENGTH} characters.",
        )

    title = generate_call_title(transcript_text, (request.title or "").strip())
    call = Call(filename=title[:255], file_path=MANUAL_TRANSCRIPT_FILE_PATH, status=CallStatus.transcribed)
    transcript = Transcript(text=transcript_text)
    call.transcript = transcript

    try:
        db.add(call)
        db.commit()
        db.refresh(call)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Could not create transcript call.") from exc

    created_call = get_call_with_related(db, call.id)
    if not created_call:
        raise HTTPException(status_code=500, detail="Created call could not be loaded.")
    return created_call


@router.post("/{call_id}/transcribe", response_model=TranscriptOut)
def transcribe_call(call_id: int, db: Session = Depends(get_db)) -> TranscriptOut:
    call = get_call_with_related(db, call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found.")
    if not Path(call.file_path).exists():
        call.status = CallStatus.failed
        db.commit()
        raise HTTPException(status_code=400, detail="Uploaded audio file is missing from local storage.")

    try:
        transcript_text = get_transcription_service().transcribe(call.file_path)
        transcript = call.transcript or Transcript(call_id=call.id, text=transcript_text)
        transcript.text = transcript_text
        call.filename = generate_call_title(transcript_text, call.filename)
        call.status = CallStatus.transcribed

        db.add(transcript)
        db.commit()
        db.refresh(transcript)
    except Exception as exc:
        db.rollback()
        call.status = CallStatus.failed
        db.commit()
        raise HTTPException(status_code=500, detail=str(exc) or "Could not transcribe call.") from exc

    return transcript


@router.post("/{call_id}/analyze", response_model=AnalysisOut)
def analyze_call(call_id: int, db: Session = Depends(get_db)) -> AnalysisOut:
    call = get_call_with_related(db, call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found.")
    if not call.transcript:
        raise HTTPException(status_code=400, detail="Transcribe the call before analyzing it.")

    try:
        result = AnalysisBase.model_validate(get_llm_service().analyze_sales_call(call.transcript.text))
        result_data = result.model_dump()
        analysis = call.analysis or Analysis(call_id=call.id, **result_data)
        for key, value in result_data.items():
            setattr(analysis, key, value)
        call.status = CallStatus.analyzed

        db.add(analysis)
        db.commit()
        db.refresh(analysis)
    except Exception as exc:
        db.rollback()
        call.status = CallStatus.failed
        db.commit()
        raise HTTPException(status_code=500, detail=str(exc) or "Could not analyze call.") from exc

    return analysis


@router.get("", response_model=list[CallOut])
def list_calls(db: Session = Depends(get_db)) -> list[CallOut]:
    return list(db.scalars(select(Call).order_by(Call.created_at.desc())).all())


@router.delete("", response_model=ClearCallsResponse)
def clear_calls(db: Session = Depends(get_db)) -> ClearCallsResponse:
    calls = list(
        db.scalars(
            select(Call).options(selectinload(Call.transcript), selectinload(Call.analysis)).order_by(Call.id)
        ).all()
    )
    file_paths = [call.file_path for call in calls]

    try:
        for call in calls:
            db.delete(call)
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Could not clear calls.") from exc

    deleted_files = 0
    for file_path in file_paths:
        try:
            if remove_local_upload(file_path):
                deleted_files += 1
        except OSError:
            continue

    return ClearCallsResponse(deleted_count=len(calls), deleted_files=deleted_files)


@router.delete("/{call_id}", response_model=DeleteCallResponse)
def delete_call(call_id: int, db: Session = Depends(get_db)) -> DeleteCallResponse:
    call = get_call_with_related(db, call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found.")

    file_path = call.file_path
    try:
        db.delete(call)
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Could not delete call.") from exc

    deleted_file = False
    try:
        deleted_file = remove_local_upload(file_path)
    except OSError:
        deleted_file = False

    return DeleteCallResponse(
        deleted_call_id=call_id,
        deleted_file=deleted_file,
        message="Call deleted successfully.",
    )


@router.get("/{call_id}", response_model=CallDetailOut)
def get_call(call_id: int, db: Session = Depends(get_db)) -> CallDetailOut:
    call = get_call_with_related(db, call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found.")
    return call


@router.get("/{call_id}/report.txt", response_class=PlainTextResponse)
def download_report(call_id: int, db: Session = Depends(get_db)) -> PlainTextResponse:
    call = get_call_with_related(db, call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found.")

    report = ReportService().build_text_report(call)
    return PlainTextResponse(
        report,
        headers={"Content-Disposition": f'attachment; filename="salesmirror-call-{call.id}-report.txt"'},
    )
