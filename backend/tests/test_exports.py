import csv
import io
from datetime import datetime, timezone

from app.database import SessionLocal
from app.models import Analysis, Call, CallStatus, Transcript
from app.routers.calls import MANUAL_TRANSCRIPT_FILE_PATH


def add_export_call(*, title: str = "Export call", file_path: str = MANUAL_TRANSCRIPT_FILE_PATH) -> int:
    created_at = datetime(2026, 6, 14, 12, 0, tzinfo=timezone.utc)
    with SessionLocal() as db:
        call = Call(
            filename=title,
            file_path=file_path,
            status=CallStatus.analyzed,
            created_at=created_at,
            updated_at=created_at,
        )
        call.transcript = Transcript(text="Salesperson: What would make this useful?", created_at=created_at)
        call.analysis = Analysis(
            overall_score=74,
            opening_score=80,
            discovery_score=70,
            objection_handling_score=75,
            closing_score=72,
            follow_up_score=73,
            talk_ratio_feedback="Balanced enough for export testing.",
            top_3_mistakes=["Ask deeper discovery.", "Clarify value.", "Confirm next step."],
            missed_questions=["Who approves the pilot?"],
            suggested_improvements=["Tie next step to success criteria."],
            better_example_responses=["Would a two-week pilot answer the key risk?"],
            short_summary="Useful call with some coaching gaps.",
            created_at=created_at,
        )
        db.add(call)
        db.commit()
        return call.id


def test_calls_json_export_includes_calls_transcripts_and_analysis(client):
    call_id = add_export_call(title="Manager export call")

    response = client.get("/exports/calls.json")

    assert response.status_code == 200, response.text
    assert response.headers["content-disposition"] == 'attachment; filename="salesmirror-calls.json"'
    payload = response.json()
    assert len(payload["calls"]) == 1
    exported = payload["calls"][0]
    assert exported["id"] == call_id
    assert exported["title"] == "Manager export call"
    assert exported["source"] == "transcript"
    assert exported["transcript"] == "Salesperson: What would make this useful?"
    assert exported["analysis"]["overall_score"] == 74
    assert exported["analysis"]["short_summary"] == "Useful call with some coaching gaps."
    assert len(exported["analysis"]["assistant_coaching_cards"]) >= 3
    assert exported["analysis"]["assistant_coaching_cards"][0]["try_saying_this"]


def test_calls_csv_export_returns_expected_headers_and_rows(client):
    add_export_call(title="CSV export call")

    response = client.get("/exports/calls.csv")

    assert response.status_code == 200, response.text
    assert response.headers["content-disposition"] == 'attachment; filename="salesmirror-calls.csv"'
    rows = list(csv.DictReader(io.StringIO(response.text)))
    assert rows == [
        {
            "id": "1",
            "title": "CSV export call",
            "filename": "CSV export call",
            "source": "transcript",
            "status": "analyzed",
            "created_at": rows[0]["created_at"],
            "updated_at": rows[0]["updated_at"],
            "overall_score": "74",
            "opening_score": "80",
            "discovery_score": "70",
            "objection_handling_score": "75",
            "closing_score": "72",
            "follow_up_score": "73",
            "short_summary": "Useful call with some coaching gaps.",
        }
    ]


def test_analytics_export_matches_summary_shape(client):
    add_export_call(title="Analytics export call")

    summary = client.get("/analytics/summary").json()
    exported = client.get("/exports/analytics.json")

    assert exported.status_code == 200, exported.text
    assert exported.headers["content-disposition"] == 'attachment; filename="salesmirror-analytics.json"'
    assert exported.json() == summary


def test_empty_database_exports_valid_empty_data(client):
    calls_json = client.get("/exports/calls.json")
    calls_csv = client.get("/exports/calls.csv")
    analytics_json = client.get("/exports/analytics.json")

    assert calls_json.status_code == 200
    assert calls_json.json() == {"calls": []}
    assert calls_csv.status_code == 200
    assert list(csv.DictReader(io.StringIO(calls_csv.text))) == []
    assert analytics_json.status_code == 200
    assert analytics_json.json()["total_calls"] == 0


def test_exports_do_not_include_audio_binary_content(client, tmp_path):
    audio_file = tmp_path / "private-call.wav"
    audio_file.write_bytes(b"binary audio bytes should not be exported")
    add_export_call(title="Audio metadata only", file_path=str(audio_file))

    json_text = client.get("/exports/calls.json").text
    json_payload = client.get("/exports/calls.json").json()
    csv_text = client.get("/exports/calls.csv").text

    assert "binary audio bytes should not be exported" not in json_text
    assert "binary audio bytes should not be exported" not in csv_text
    assert json_payload["calls"][0]["file_path"] == str(audio_file)
    assert str(audio_file) not in csv_text
