import csv
import io
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import Analysis, Call
from app.routers.analytics import build_analytics_summary
from app.routers.calls import MANUAL_TRANSCRIPT_FILE_PATH


router = APIRouter(prefix="/exports", tags=["exports"])

CSV_HEADERS = [
    "id",
    "title",
    "filename",
    "source",
    "status",
    "created_at",
    "updated_at",
    "overall_score",
    "opening_score",
    "discovery_score",
    "objection_handling_score",
    "closing_score",
    "follow_up_score",
    "short_summary",
]


@router.get("/calls.json")
def export_calls_json(db: Session = Depends(get_db)) -> JSONResponse:
    calls = _load_calls(db)
    return JSONResponse(
        content={"calls": [_call_export(call) for call in calls]},
        headers={"Content-Disposition": 'attachment; filename="salesmirror-calls.json"'},
    )


@router.get("/calls.csv")
def export_calls_csv(db: Session = Depends(get_db)) -> StreamingResponse:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_HEADERS, lineterminator="\n")
    writer.writeheader()
    for call in _load_calls(db):
        writer.writerow(_call_csv_row(call))

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="salesmirror-calls.csv"'},
    )


@router.get("/analytics.json")
def export_analytics_json(db: Session = Depends(get_db)) -> JSONResponse:
    return JSONResponse(
        content=build_analytics_summary(db).model_dump(mode="json"),
        headers={"Content-Disposition": 'attachment; filename="salesmirror-analytics.json"'},
    )


def _load_calls(db: Session) -> list[Call]:
    return list(
        db.scalars(
            select(Call)
            .options(selectinload(Call.transcript), selectinload(Call.analysis))
            .order_by(Call.created_at.desc())
        ).all()
    )


def _call_export(call: Call) -> dict[str, Any]:
    return {
        "id": call.id,
        "title": call.filename,
        "filename": call.filename,
        "file_path": call.file_path,
        "source": _source(call),
        "status": call.status.value,
        "created_at": _iso(call.created_at),
        "updated_at": _iso(call.updated_at),
        "transcript": call.transcript.text if call.transcript else None,
        "analysis": _analysis_export(call.analysis) if call.analysis else None,
    }


def _analysis_export(analysis: Analysis) -> dict[str, Any]:
    return {
        "overall_score": analysis.overall_score,
        "opening_score": analysis.opening_score,
        "discovery_score": analysis.discovery_score,
        "objection_handling_score": analysis.objection_handling_score,
        "closing_score": analysis.closing_score,
        "follow_up_score": analysis.follow_up_score,
        "talk_ratio_feedback": analysis.talk_ratio_feedback,
        "top_3_mistakes": analysis.top_3_mistakes,
        "missed_questions": analysis.missed_questions,
        "suggested_improvements": analysis.suggested_improvements,
        "better_example_responses": analysis.better_example_responses,
        "short_summary": analysis.short_summary,
        "created_at": _iso(analysis.created_at),
    }


def _call_csv_row(call: Call) -> dict[str, Any]:
    analysis = call.analysis
    return {
        "id": call.id,
        "title": call.filename,
        "filename": call.filename,
        "source": _source(call),
        "status": call.status.value,
        "created_at": _iso(call.created_at),
        "updated_at": _iso(call.updated_at),
        "overall_score": analysis.overall_score if analysis else "",
        "opening_score": analysis.opening_score if analysis else "",
        "discovery_score": analysis.discovery_score if analysis else "",
        "objection_handling_score": analysis.objection_handling_score if analysis else "",
        "closing_score": analysis.closing_score if analysis else "",
        "follow_up_score": analysis.follow_up_score if analysis else "",
        "short_summary": analysis.short_summary if analysis else "",
    }


def _source(call: Call) -> str:
    return "transcript" if call.file_path == MANUAL_TRANSCRIPT_FILE_PATH else "audio"


def _iso(value: datetime) -> str:
    return value.isoformat()
