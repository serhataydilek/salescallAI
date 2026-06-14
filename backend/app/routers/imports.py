from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import Analysis, Call, CallStatus, Transcript
from app.routers.calls import MANUAL_TRANSCRIPT_FILE_PATH
from app.schemas import AnalysisBase, ImportCallsResponse


router = APIRouter(prefix="/imports", tags=["imports"])

RESTORED_AUDIO_FILE_PATH = "restored-audio-file-not-included"


class ImportAnalysis(AnalysisBase):
    created_at: datetime | None = None


class ImportCall(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int | None = None
    title: str | None = None
    filename: str | None = None
    file_path: str | None = None
    source: Literal["audio", "transcript"] | None = None
    status: Literal["uploaded", "transcribed", "analyzed", "failed"]
    created_at: datetime
    updated_at: datetime | None = None
    transcript: str | None = None
    analysis: ImportAnalysis | None = None

    @field_validator("title", "filename", "file_path", "transcript", mode="before")
    @classmethod
    def coerce_strings(cls, value: Any) -> Any:
        if value is None or isinstance(value, str):
            return value
        raise ValueError("must be a string or null")


class ImportCallsPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    calls: list[ImportCall]


@router.post("/calls.json", response_model=ImportCallsResponse)
async def import_calls_json(
    request: Request,
    dry_run: bool = False,
    file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
) -> ImportCallsResponse:
    payload = await _load_payload(request, file)
    existing_keys = _existing_duplicate_keys(db)
    summary = _build_summary(payload, existing_keys)

    if dry_run:
        return ImportCallsResponse(
            **summary,
            message="Dry run complete. No calls were imported.",
        )

    try:
        for imported in payload.calls:
            duplicate_key = _duplicate_key(imported.title or imported.filename, imported.created_at, imported.transcript)
            if duplicate_key in existing_keys:
                continue

            call = Call(
                filename=_safe_title(imported),
                file_path=_restored_file_path(imported),
                status=CallStatus(imported.status),
                created_at=imported.created_at,
                updated_at=imported.updated_at or imported.created_at,
            )
            if imported.transcript is not None:
                call.transcript = Transcript(text=imported.transcript, created_at=imported.created_at)
            if imported.analysis is not None:
                analysis_data = imported.analysis.model_dump(exclude={"created_at"})
                call.analysis = Analysis(
                    **analysis_data,
                    created_at=imported.analysis.created_at or imported.updated_at or imported.created_at,
                )
            db.add(call)
            existing_keys.add(duplicate_key)

        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Could not import calls.") from exc

    return ImportCallsResponse(
        **summary,
        message="Import complete. Audio files were not restored.",
    )


async def _load_payload(request: Request, file: UploadFile | None) -> ImportCallsPayload:
    try:
        if file is not None:
            raw = await file.read()
            if not raw:
                raise HTTPException(status_code=422, detail="Import file is empty.")
            return ImportCallsPayload.model_validate_json(raw)

        content_type = request.headers.get("content-type", "")
        if "application/json" not in content_type.lower():
            raise HTTPException(status_code=422, detail="Expected JSON body or multipart JSON file.")
        return ImportCallsPayload.model_validate(await request.json())
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid JSON import payload.") from exc


def _build_summary(payload: ImportCallsPayload, existing_keys: set[tuple[str, str, str]]) -> dict[str, int]:
    imported_calls = 0
    imported_transcripts = 0
    imported_analyses = 0
    skipped_items = 0
    seen_keys = set(existing_keys)

    for imported in payload.calls:
        duplicate_key = _duplicate_key(imported.title or imported.filename, imported.created_at, imported.transcript)
        if duplicate_key in seen_keys:
            skipped_items += 1
            continue
        seen_keys.add(duplicate_key)
        imported_calls += 1
        if imported.transcript is not None:
            imported_transcripts += 1
        if imported.analysis is not None:
            imported_analyses += 1

    return {
        "imported_calls": imported_calls,
        "imported_transcripts": imported_transcripts,
        "imported_analyses": imported_analyses,
        "skipped_items": skipped_items,
    }


def _existing_duplicate_keys(db: Session) -> set[tuple[str, str, str]]:
    calls = db.scalars(select(Call).options(selectinload(Call.transcript))).all()
    return {
        _duplicate_key(call.filename, call.created_at, call.transcript.text if call.transcript else None)
        for call in calls
    }


def _duplicate_key(title: str | None, created_at: datetime, transcript: str | None) -> tuple[str, str, str]:
    return ((_clean_title(title)).lower(), _datetime_key(created_at), (transcript or "").strip())


def _datetime_key(value: datetime) -> str:
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value.isoformat()


def _safe_title(imported: ImportCall) -> str:
    raw_title = (imported.title or imported.filename or "Restored SalesMirror Call").strip()
    if imported.source == "audio":
        raw_title = Path(raw_title).name
    return _clean_title(raw_title)[:255]


def _clean_title(value: str | None) -> str:
    cleaned = (value or "").strip().replace("\x00", "")
    return cleaned or "Restored SalesMirror Call"


def _restored_file_path(imported: ImportCall) -> str:
    if imported.source == "transcript" or imported.file_path == MANUAL_TRANSCRIPT_FILE_PATH:
        return MANUAL_TRANSCRIPT_FILE_PATH
    return RESTORED_AUDIO_FILE_PATH
