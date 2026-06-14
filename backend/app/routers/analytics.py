from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import Call, CallStatus
from app.routers.calls import MANUAL_TRANSCRIPT_FILE_PATH
from app.schemas import AnalyticsSummaryOut, RecentCallSummaryOut, ScoreDistributionOut


router = APIRouter(prefix="/analytics", tags=["analytics"])

CATEGORY_LABELS = {
    "average_opening_score": "Opening",
    "average_discovery_score": "Discovery",
    "average_objection_handling_score": "Objection Handling",
    "average_closing_score": "Closing",
    "average_follow_up_score": "Follow Up",
}


@router.get("/summary", response_model=AnalyticsSummaryOut)
def analytics_summary(db: Session = Depends(get_db)) -> AnalyticsSummaryOut:
    calls = list(
        db.scalars(
            select(Call)
            .options(selectinload(Call.analysis), selectinload(Call.transcript))
            .order_by(Call.created_at.desc())
        ).all()
    )
    analyzed = [call for call in calls if call.analysis is not None]

    averages = _score_averages(analyzed)
    weakest_category = None
    strongest_category = None
    category_scores = {key: value for key, value in averages.items() if key != "average_overall_score" and value is not None}
    if category_scores:
        weakest_category = CATEGORY_LABELS[min(category_scores, key=category_scores.get)]
        strongest_category = CATEGORY_LABELS[max(category_scores, key=category_scores.get)]

    return AnalyticsSummaryOut(
        total_calls=len(calls),
        analyzed_calls=sum(1 for call in calls if call.status == CallStatus.analyzed),
        transcribed_calls=sum(1 for call in calls if call.status == CallStatus.transcribed),
        uploaded_calls=sum(1 for call in calls if call.status == CallStatus.uploaded),
        failed_calls=sum(1 for call in calls if call.status == CallStatus.failed),
        transcript_calls=sum(1 for call in calls if call.file_path == MANUAL_TRANSCRIPT_FILE_PATH),
        audio_calls=sum(1 for call in calls if call.file_path != MANUAL_TRANSCRIPT_FILE_PATH),
        score_distribution=_score_distribution(analyzed),
        weakest_category=weakest_category,
        strongest_category=strongest_category,
        recent_calls=[
            RecentCallSummaryOut(
                id=call.id,
                title=call.filename,
                status=call.status.value,
                source="transcript" if call.file_path == MANUAL_TRANSCRIPT_FILE_PATH else "audio",
                overall_score=call.analysis.overall_score if call.analysis else None,
                created_at=call.created_at,
            )
            for call in calls[:5]
        ],
        **averages,
    )


def _score_averages(calls: list[Call]) -> dict[str, float | None]:
    if not calls:
        return {
            "average_overall_score": None,
            "average_opening_score": None,
            "average_discovery_score": None,
            "average_objection_handling_score": None,
            "average_closing_score": None,
            "average_follow_up_score": None,
        }

    return {
        "average_overall_score": _average([call.analysis.overall_score for call in calls if call.analysis]),
        "average_opening_score": _average([call.analysis.opening_score for call in calls if call.analysis]),
        "average_discovery_score": _average([call.analysis.discovery_score for call in calls if call.analysis]),
        "average_objection_handling_score": _average(
            [call.analysis.objection_handling_score for call in calls if call.analysis]
        ),
        "average_closing_score": _average([call.analysis.closing_score for call in calls if call.analysis]),
        "average_follow_up_score": _average([call.analysis.follow_up_score for call in calls if call.analysis]),
    }


def _average(values: list[int]) -> float:
    return round(sum(values) / len(values), 1)


def _score_distribution(calls: list[Call]) -> ScoreDistributionOut:
    distribution = {"strong": 0, "decent": 0, "weak": 0, "poor": 0}
    for call in calls:
        if not call.analysis:
            continue
        score = call.analysis.overall_score
        if score >= 80:
            distribution["strong"] += 1
        elif score >= 60:
            distribution["decent"] += 1
        elif score >= 40:
            distribution["weak"] += 1
        else:
            distribution["poor"] += 1
    return ScoreDistributionOut(**distribution)
