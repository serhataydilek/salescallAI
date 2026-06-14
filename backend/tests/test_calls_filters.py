from datetime import datetime, timezone

from app.database import SessionLocal
from app.models import Analysis, Call, CallStatus, Transcript
from app.routers.calls import MANUAL_TRANSCRIPT_FILE_PATH


def add_call(
    *,
    filename: str,
    transcript_text: str,
    status: CallStatus = CallStatus.transcribed,
    file_path: str = MANUAL_TRANSCRIPT_FILE_PATH,
    score: int | None = None,
    created_at: datetime,
) -> int:
    with SessionLocal() as db:
        call = Call(filename=filename, file_path=file_path, status=status, created_at=created_at, updated_at=created_at)
        call.transcript = Transcript(text=transcript_text, created_at=created_at)
        if score is not None:
            call.status = CallStatus.analyzed
            call.analysis = Analysis(
                overall_score=score,
                opening_score=score,
                discovery_score=score,
                objection_handling_score=score,
                closing_score=score,
                follow_up_score=score,
                talk_ratio_feedback=f"Talk ratio feedback for {filename}.",
                top_3_mistakes=[f"Mistake for {filename}"],
                missed_questions=[f"Question for {filename}?"],
                suggested_improvements=[f"Improve {filename}."],
                better_example_responses=[f"Better response for {filename}."],
                short_summary=f"Summary for {filename}.",
                created_at=created_at,
            )
        db.add(call)
        db.commit()
        return call.id


def seed_filter_calls() -> dict[str, int]:
    return {
        "alpha": add_call(
            filename="Alpha discovery call",
            transcript_text="Salesperson: Tell me about your onboarding process.\nCustomer: We need cleaner coaching.",
            score=82,
            created_at=datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc),
        ),
        "beta": add_call(
            filename="Beta budget call",
            transcript_text="Salesperson: What budget range are you considering?\nCustomer: Price is a concern.",
            score=45,
            created_at=datetime(2026, 1, 2, 9, 0, tzinfo=timezone.utc),
        ),
        "gamma": add_call(
            filename="Gamma uploaded audio",
            transcript_text="Salesperson: This audio transcript mentions renewal risk.",
            file_path="C:/tmp/gamma.wav",
            status=CallStatus.uploaded,
            created_at=datetime(2026, 1, 3, 9, 0, tzinfo=timezone.utc),
        ),
        "delta": add_call(
            filename="Delta failed call",
            transcript_text="Salesperson: The transcript mentions compliance review.",
            status=CallStatus.failed,
            created_at=datetime(2026, 1, 4, 9, 0, tzinfo=timezone.utc),
        ),
    }


def filenames(response) -> list[str]:
    assert response.status_code == 200, response.text
    return [call["filename"] for call in response.json()]


def test_list_calls_without_filters_preserves_newest_first(client):
    seed_filter_calls()

    assert filenames(client.get("/calls")) == [
        "Delta failed call",
        "Gamma uploaded audio",
        "Beta budget call",
        "Alpha discovery call",
    ]


def test_list_calls_includes_score_fields_for_analyzed_and_unanalyzed_calls(client):
    seed_filter_calls()

    response = client.get("/calls")
    assert response.status_code == 200, response.text
    calls = {call["filename"]: call for call in response.json()}

    analyzed = calls["Alpha discovery call"]
    assert analyzed["overall_score"] == 82
    assert analyzed["opening_score"] == 82
    assert analyzed["discovery_score"] == 82
    assert analyzed["objection_handling_score"] == 82
    assert analyzed["closing_score"] == 82
    assert analyzed["follow_up_score"] == 82

    unanalyzed = calls["Gamma uploaded audio"]
    assert unanalyzed["overall_score"] is None
    assert unanalyzed["opening_score"] is None
    assert unanalyzed["discovery_score"] is None
    assert unanalyzed["objection_handling_score"] is None
    assert unanalyzed["closing_score"] is None
    assert unanalyzed["follow_up_score"] is None


def test_empty_form_filter_values_are_ignored(client):
    seed_filter_calls()

    assert filenames(
        client.get(
            "/calls",
            params={
                "q": "",
                "status": "",
                "source": "",
                "min_score": "",
                "max_score": "",
                "sort": "newest",
            },
        )
    ) == [
        "Delta failed call",
        "Gamma uploaded audio",
        "Beta budget call",
        "Alpha discovery call",
    ]


def test_search_by_title(client):
    seed_filter_calls()

    assert filenames(client.get("/calls", params={"q": "budget"})) == ["Beta budget call"]


def test_search_by_transcript_text(client):
    seed_filter_calls()

    assert filenames(client.get("/calls", params={"q": "renewal risk"})) == ["Gamma uploaded audio"]


def test_filter_by_status(client):
    seed_filter_calls()

    assert filenames(client.get("/calls", params={"status": "failed"})) == ["Delta failed call"]


def test_filter_by_source_transcript_and_audio(client):
    seed_filter_calls()

    assert filenames(client.get("/calls", params={"source": "audio"})) == ["Gamma uploaded audio"]
    assert filenames(client.get("/calls", params={"source": "transcript"})) == [
        "Delta failed call",
        "Beta budget call",
        "Alpha discovery call",
    ]


def test_filter_by_score_range(client):
    seed_filter_calls()

    assert filenames(client.get("/calls", params={"min_score": 40, "max_score": 60})) == ["Beta budget call"]
    assert filenames(client.get("/calls", params={"min_score": 80})) == ["Alpha discovery call"]


def test_sort_oldest_and_newest(client):
    seed_filter_calls()

    assert filenames(client.get("/calls", params={"sort": "oldest"})) == [
        "Alpha discovery call",
        "Beta budget call",
        "Gamma uploaded audio",
        "Delta failed call",
    ]
    assert filenames(client.get("/calls", params={"sort": "newest"})) == [
        "Delta failed call",
        "Gamma uploaded audio",
        "Beta budget call",
        "Alpha discovery call",
    ]


def test_sort_score_descending_and_ascending(client):
    seed_filter_calls()

    assert filenames(client.get("/calls", params={"sort": "score_desc"})) == [
        "Alpha discovery call",
        "Beta budget call",
        "Delta failed call",
        "Gamma uploaded audio",
    ]
    assert filenames(client.get("/calls", params={"sort": "score_asc"})) == [
        "Beta budget call",
        "Alpha discovery call",
        "Delta failed call",
        "Gamma uploaded audio",
    ]


def test_invalid_score_range_returns_error(client):
    seed_filter_calls()

    response = client.get("/calls", params={"min_score": 90, "max_score": 10})
    assert response.status_code == 400
    assert response.json()["detail"] == "min_score cannot be greater than max_score."
