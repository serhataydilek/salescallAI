from datetime import datetime, timezone

from app.database import SessionLocal
from app.models import Analysis, Call, CallStatus, Transcript
from app.routers.calls import MANUAL_TRANSCRIPT_FILE_PATH


def add_call(
    *,
    title: str,
    status: CallStatus,
    created_at: datetime,
    file_path: str = MANUAL_TRANSCRIPT_FILE_PATH,
    score: int | None = None,
    opening: int = 50,
    discovery: int = 50,
    objection: int = 50,
    closing: int = 50,
    follow_up: int = 50,
) -> int:
    with SessionLocal() as db:
        call = Call(filename=title, file_path=file_path, status=status, created_at=created_at, updated_at=created_at)
        call.transcript = Transcript(text=f"Transcript for {title}", created_at=created_at)
        if score is not None:
            call.status = CallStatus.analyzed
            call.analysis = Analysis(
                overall_score=score,
                opening_score=opening,
                discovery_score=discovery,
                objection_handling_score=objection,
                closing_score=closing,
                follow_up_score=follow_up,
                talk_ratio_feedback="Balanced enough for testing.",
                top_3_mistakes=["Mistake one", "Mistake two", "Mistake three"],
                missed_questions=["Question one?"],
                suggested_improvements=["Improve discovery."],
                better_example_responses=["Try this response."],
                short_summary="Summary.",
                created_at=created_at,
            )
        db.add(call)
        db.commit()
        return call.id


def test_empty_database_returns_zero_and_null_summary(client):
    response = client.get("/analytics/summary")

    assert response.status_code == 200, response.text
    summary = response.json()
    assert summary["total_calls"] == 0
    assert summary["analyzed_calls"] == 0
    assert summary["average_overall_score"] is None
    assert summary["weakest_category"] is None
    assert summary["strongest_category"] is None
    assert summary["score_distribution"] == {"strong": 0, "decent": 0, "weak": 0, "poor": 0}
    assert summary["recent_calls"] == []
    assert summary["score_trend"] == []
    assert summary["improvement_delta"] == {
        "first_score": None,
        "latest_score": None,
        "delta": None,
        "direction": "insufficient_data",
    }


def test_analytics_summary_counts_sources_averages_distribution_and_recent_calls(client):
    add_call(
        title="Poor call",
        status=CallStatus.analyzed,
        score=30,
        opening=90,
        discovery=20,
        objection=40,
        closing=30,
        follow_up=50,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    add_call(
        title="Weak call",
        status=CallStatus.analyzed,
        score=45,
        opening=80,
        discovery=40,
        objection=50,
        closing=45,
        follow_up=55,
        created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )
    add_call(
        title="Decent call",
        status=CallStatus.analyzed,
        score=65,
        opening=70,
        discovery=60,
        objection=70,
        closing=65,
        follow_up=75,
        created_at=datetime(2026, 1, 3, tzinfo=timezone.utc),
    )
    add_call(
        title="Strong call",
        status=CallStatus.analyzed,
        score=85,
        opening=100,
        discovery=80,
        objection=90,
        closing=85,
        follow_up=95,
        created_at=datetime(2026, 1, 4, tzinfo=timezone.utc),
    )
    add_call(
        title="Uploaded audio",
        status=CallStatus.uploaded,
        file_path="C:/tmp/uploaded.wav",
        created_at=datetime(2026, 1, 5, tzinfo=timezone.utc),
    )
    add_call(
        title="Transcribed only",
        status=CallStatus.transcribed,
        created_at=datetime(2026, 1, 6, tzinfo=timezone.utc),
    )
    add_call(
        title="Failed call",
        status=CallStatus.failed,
        created_at=datetime(2026, 1, 7, tzinfo=timezone.utc),
    )

    response = client.get("/analytics/summary")

    assert response.status_code == 200, response.text
    summary = response.json()
    assert summary["total_calls"] == 7
    assert summary["analyzed_calls"] == 4
    assert summary["transcribed_calls"] == 1
    assert summary["uploaded_calls"] == 1
    assert summary["failed_calls"] == 1
    assert summary["transcript_calls"] == 6
    assert summary["audio_calls"] == 1
    assert summary["average_overall_score"] == 56.2
    assert summary["average_opening_score"] == 85.0
    assert summary["average_discovery_score"] == 50.0
    assert summary["average_objection_handling_score"] == 62.5
    assert summary["average_closing_score"] == 56.2
    assert summary["average_follow_up_score"] == 68.8
    assert summary["weakest_category"] == "Discovery"
    assert summary["strongest_category"] == "Opening"
    assert summary["score_distribution"] == {"strong": 1, "decent": 1, "weak": 1, "poor": 1}
    assert [call["title"] for call in summary["recent_calls"]] == [
        "Failed call",
        "Transcribed only",
        "Uploaded audio",
        "Strong call",
        "Decent call",
    ]
    assert summary["recent_calls"][2]["source"] == "audio"
    assert summary["recent_calls"][3]["overall_score"] == 85
    assert [call["title"] for call in summary["score_trend"]] == [
        "Poor call",
        "Weak call",
        "Decent call",
        "Strong call",
    ]
    assert summary["score_trend"][0]["overall_score"] == 30
    assert summary["score_trend"][0]["discovery_score"] == 20
    assert summary["score_trend"][-1]["follow_up_score"] == 95
    assert summary["improvement_delta"] == {
        "first_score": 30,
        "latest_score": 85,
        "delta": 55,
        "direction": "improved",
    }


def test_score_trend_maxes_at_latest_ten_analyzed_calls(client):
    for index in range(12):
        add_call(
            title=f"Trend call {index + 1}",
            status=CallStatus.analyzed,
            score=40 + index,
            created_at=datetime(2026, 2, index + 1, tzinfo=timezone.utc),
        )

    response = client.get("/analytics/summary")

    assert response.status_code == 200, response.text
    summary = response.json()
    assert len(summary["score_trend"]) == 10
    assert [call["title"] for call in summary["score_trend"]] == [f"Trend call {index}" for index in range(3, 13)]
    assert summary["improvement_delta"] == {
        "first_score": 40,
        "latest_score": 51,
        "delta": 11,
        "direction": "improved",
    }


def test_improvement_delta_declined(client):
    add_call(
        title="First high score",
        status=CallStatus.analyzed,
        score=80,
        created_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
    )
    add_call(
        title="Latest lower score",
        status=CallStatus.analyzed,
        score=65,
        created_at=datetime(2026, 3, 2, tzinfo=timezone.utc),
    )

    assert client.get("/analytics/summary").json()["improvement_delta"] == {
        "first_score": 80,
        "latest_score": 65,
        "delta": -15,
        "direction": "declined",
    }


def test_improvement_delta_unchanged(client):
    add_call(
        title="First equal score",
        status=CallStatus.analyzed,
        score=70,
        created_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
    )
    add_call(
        title="Latest equal score",
        status=CallStatus.analyzed,
        score=70,
        created_at=datetime(2026, 4, 2, tzinfo=timezone.utc),
    )

    assert client.get("/analytics/summary").json()["improvement_delta"] == {
        "first_score": 70,
        "latest_score": 70,
        "delta": 0,
        "direction": "unchanged",
    }


def test_improvement_delta_insufficient_data_with_one_analyzed_call(client):
    add_call(
        title="Only analyzed call",
        status=CallStatus.analyzed,
        score=70,
        created_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
    )

    summary = client.get("/analytics/summary").json()
    assert len(summary["score_trend"]) == 1
    assert summary["improvement_delta"] == {
        "first_score": None,
        "latest_score": None,
        "delta": None,
        "direction": "insufficient_data",
    }
