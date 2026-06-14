import json

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Call
from app.routers.imports import RESTORED_AUDIO_FILE_PATH


def export_payload(title: str = "Restored export call", source: str = "transcript") -> dict:
    return {
        "calls": [
            {
                "id": 999,
                "title": title,
                "filename": title,
                "file_path": "manual-transcript" if source == "transcript" else "C:/private/private-call.wav",
                "source": source,
                "status": "analyzed",
                "created_at": "2026-06-14T12:00:00+00:00",
                "updated_at": "2026-06-14T12:01:00+00:00",
                "transcript": "Salesperson: What would make this useful?\nCustomer: A clear next step.",
                "analysis": {
                    "overall_score": 74,
                    "opening_score": 80,
                    "discovery_score": 70,
                    "objection_handling_score": 75,
                    "closing_score": 72,
                    "follow_up_score": 73,
                    "talk_ratio_feedback": "Balanced enough for import testing.",
                    "top_3_mistakes": ["Ask deeper discovery.", "Clarify value.", "Confirm next step."],
                    "missed_questions": ["Who approves the pilot?"],
                    "suggested_improvements": ["Tie next step to success criteria."],
                    "better_example_responses": ["Would a two-week pilot answer the key risk?"],
                    "short_summary": "Useful call with some coaching gaps.",
                    "created_at": "2026-06-14T12:02:00+00:00",
                },
            }
        ]
    }


def test_dry_run_validates_and_imports_nothing(client):
    response = client.post("/imports/calls.json?dry_run=true", json=export_payload())

    assert response.status_code == 200, response.text
    assert response.json() == {
        "imported_calls": 1,
        "imported_transcripts": 1,
        "imported_analyses": 1,
        "skipped_items": 0,
        "message": "Dry run complete. No calls were imported.",
    }
    with SessionLocal() as db:
        assert db.scalar(select(Call)) is None


def test_importing_valid_export_creates_calls_transcripts_and_analyses(client):
    response = client.post("/imports/calls.json", json=export_payload())

    assert response.status_code == 200, response.text
    assert response.json()["imported_calls"] == 1
    with SessionLocal() as db:
        call = db.scalar(select(Call))
        assert call is not None
        assert call.filename == "Restored export call"
        assert call.transcript is not None
        assert call.transcript.text.startswith("Salesperson:")
        assert call.analysis is not None
        assert call.analysis.overall_score == 74


def test_imported_calls_get_new_ids(client):
    payload = export_payload()

    response = client.post("/imports/calls.json", json=payload)

    assert response.status_code == 200, response.text
    with SessionLocal() as db:
        call = db.scalar(select(Call))
        assert call is not None
        assert call.id != payload["calls"][0]["id"]


def test_duplicate_import_skips_existing_items(client):
    payload = export_payload()
    first = client.post("/imports/calls.json", json=payload)
    second = client.post("/imports/calls.json", json=payload)

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert second.json()["skipped_items"] == 1
    assert second.json()["imported_calls"] == 0
    with SessionLocal() as db:
        assert len(list(db.scalars(select(Call)).all())) == 1


def test_audio_binary_content_is_not_restored(client):
    payload = export_payload(title="private-call.wav", source="audio")
    payload["calls"][0]["transcript"] = "Salesperson: binary audio bytes should stay out.\nCustomer: Yes."

    response = client.post("/imports/calls.json", json=payload)

    assert response.status_code == 200, response.text
    with SessionLocal() as db:
        call = db.scalar(select(Call))
        assert call is not None
        assert call.filename == "private-call.wav"
        assert call.file_path == RESTORED_AUDIO_FILE_PATH


def test_invalid_json_and_invalid_structure_return_validation_error(client):
    invalid_json = client.post(
        "/imports/calls.json",
        content="{not-json",
        headers={"Content-Type": "application/json"},
    )
    invalid_structure = client.post("/imports/calls.json", json={"items": []})

    assert invalid_json.status_code == 422
    assert invalid_structure.status_code == 422


def test_empty_export_imports_zero_items_safely(client):
    response = client.post("/imports/calls.json", json={"calls": []})

    assert response.status_code == 200, response.text
    assert response.json()["imported_calls"] == 0
    assert response.json()["imported_transcripts"] == 0
    assert response.json()["imported_analyses"] == 0
    with SessionLocal() as db:
        assert db.scalar(select(Call)) is None


def test_import_accepts_json_file_upload(client):
    response = client.post(
        "/imports/calls.json?dry_run=true",
        files={"file": ("salesmirror-calls.json", json.dumps(export_payload()), "application/json")},
    )

    assert response.status_code == 200, response.text
    assert response.json()["imported_calls"] == 1
