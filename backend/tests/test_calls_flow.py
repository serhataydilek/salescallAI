from sqlalchemy import select

from app.config import set_upload_dir
from app.database import SessionLocal
from app.models import Analysis, Call, CallStatus, Transcript


VALID_TRANSCRIPT = """Salesperson: Hi, thanks for joining today. What is pushing you to improve coaching now?
Customer: We miss follow-ups and managers need a clean coaching summary.
Salesperson: How are you measuring coaching today? What would make a pilot successful?
Customer: We need better notes and a clear next step.
Salesperson: I can send a sample report today and schedule a follow-up next Tuesday."""

UPDATED_TRANSCRIPT = """Salesperson: Hi, thanks for joining today. What changed since your last sales review?
Customer: We need better follow-up tracking and a pilot plan before buying.
Salesperson: How would you measure pilot success? Who needs to approve the budget?
Customer: Sales leadership needs to see coaching consistency.
Salesperson: I will send a sample report and book a review for next Tuesday."""


def create_transcript_call(client, title: str = "Regression call", transcript: str = VALID_TRANSCRIPT) -> dict:
    response = client.post("/calls/from-transcript", json={"title": title, "transcript": transcript})
    assert response.status_code == 200, response.text
    return response.json()


def test_pasted_transcript_flow_validates_titles_and_length(client):
    generic_response = client.post(
        "/calls/from-transcript",
        json={"title": "ttttt", "transcript": VALID_TRANSCRIPT},
    )
    assert generic_response.status_code == 200, generic_response.text
    generic_call = generic_response.json()
    assert generic_call["status"] == "transcribed"
    assert generic_call["transcript"]["text"] == VALID_TRANSCRIPT
    assert generic_call["filename"] != "ttttt"

    meaningful_call = create_transcript_call(client, title="Enterprise pilot review")
    assert meaningful_call["filename"] == "Enterprise pilot review"

    short_response = client.post(
        "/calls/from-transcript",
        json={"title": "Too short", "transcript": "Salesperson: hi"},
    )
    assert short_response.status_code == 400
    assert "at least 30 characters" in short_response.json()["detail"]


def test_analyze_flow_updates_existing_analysis(client):
    call = create_transcript_call(client)

    first_response = client.post(f"/calls/{call['id']}/analyze")
    assert first_response.status_code == 200, first_response.text
    first_analysis = first_response.json()
    assert first_analysis["call_id"] == call["id"]
    assert first_analysis["overall_score"] >= 0
    for field in [
        "opening_score",
        "discovery_score",
        "objection_handling_score",
        "closing_score",
        "follow_up_score",
        "talk_ratio_feedback",
        "top_3_mistakes",
        "missed_questions",
        "suggested_improvements",
        "better_example_responses",
        "assistant_coaching_cards",
        "short_summary",
    ]:
        assert field in first_analysis
    assert len(first_analysis["assistant_coaching_cards"]) >= 3

    call_response = client.get(f"/calls/{call['id']}")
    assert call_response.status_code == 200
    assert call_response.json()["status"] == "analyzed"

    second_response = client.post(f"/calls/{call['id']}/analyze")
    assert second_response.status_code == 200, second_response.text
    assert second_response.json()["id"] == first_analysis["id"]

    with SessionLocal() as db:
        analyses = list(db.scalars(select(Analysis).where(Analysis.call_id == call["id"])).all())
    assert len(analyses) == 1


def test_transcript_edit_marks_stale_and_reanalysis_reuses_analysis(client):
    call = create_transcript_call(client)
    analysis = client.post(f"/calls/{call['id']}/analyze").json()

    update_response = client.put(f"/calls/{call['id']}/transcript", json={"transcript": UPDATED_TRANSCRIPT})
    assert update_response.status_code == 200, update_response.text
    updated_call = update_response.json()
    assert updated_call["status"] == "transcribed"
    assert updated_call["transcript"]["text"] == UPDATED_TRANSCRIPT
    assert updated_call["analysis"]["id"] == analysis["id"]

    with SessionLocal() as db:
        assert len(list(db.scalars(select(Analysis).where(Analysis.call_id == call["id"])).all())) == 1

    reanalysis_response = client.post(f"/calls/{call['id']}/analyze")
    assert reanalysis_response.status_code == 200, reanalysis_response.text
    assert reanalysis_response.json()["id"] == analysis["id"]

    report_response = client.get(f"/calls/{call['id']}/report.txt")
    assert report_response.status_code == 200
    assert "pilot plan before buying" in report_response.text
    assert "## Assistant Coaching" in report_response.text
    assert "Try saying this instead" in report_response.text


def test_delete_selected_call_cascades_and_keeps_other_calls(client):
    first_call = create_transcript_call(client, title="First call")
    second_call = create_transcript_call(client, title="Second call")
    client.post(f"/calls/{first_call['id']}/analyze")
    client.post(f"/calls/{second_call['id']}/analyze")

    delete_response = client.delete(f"/calls/{first_call['id']}")
    assert delete_response.status_code == 200, delete_response.text
    assert delete_response.json()["deleted_call_id"] == first_call["id"]
    assert delete_response.json()["deleted_file"] is False

    assert client.get(f"/calls/{first_call['id']}").status_code == 404
    remaining_response = client.get(f"/calls/{second_call['id']}")
    assert remaining_response.status_code == 200
    assert remaining_response.json()["filename"] == "Second call"

    with SessionLocal() as db:
        assert db.get(Call, first_call["id"]) is None
        assert db.scalar(select(Transcript).where(Transcript.call_id == first_call["id"])) is None
        assert db.scalar(select(Analysis).where(Analysis.call_id == first_call["id"])) is None
        assert db.get(Call, second_call["id"]) is not None


def test_delete_uploaded_call_removes_file_inside_configured_upload_dir(client, tmp_path):
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    set_upload_dir(upload_dir)
    uploaded_file = upload_dir / "fake-call.wav"
    uploaded_file.write_text("not real audio")

    untouched_call = create_transcript_call(client, title="Untouched call")
    client.post(f"/calls/{untouched_call['id']}/analyze")

    with SessionLocal() as db:
        call = Call(filename="fake-call.wav", file_path=str(uploaded_file), status=CallStatus.transcribed)
        call.transcript = Transcript(text=VALID_TRANSCRIPT)
        call.analysis = Analysis(
            overall_score=55,
            opening_score=70,
            discovery_score=45,
            objection_handling_score=60,
            closing_score=50,
            follow_up_score=52,
            talk_ratio_feedback="The salesperson should ask more discovery questions.",
            top_3_mistakes=["Discovery was shallow.", "Value was vague.", "Close was weak."],
            missed_questions=["Who approves the pilot?"],
            suggested_improvements=["Confirm a specific next step."],
            better_example_responses=["Would a two-week pilot prove the value?"],
            short_summary="The call needs clearer discovery and follow-up.",
        )
        db.add(call)
        db.commit()
        call_id = call.id

    response = client.delete(f"/calls/{call_id}")
    assert response.status_code == 200, response.text
    assert response.json()["deleted_call_id"] == call_id
    assert response.json()["deleted_file"] is True
    assert not uploaded_file.exists()
    assert client.get(f"/calls/{call_id}").status_code == 404

    with SessionLocal() as db:
        assert db.get(Call, call_id) is None
        assert db.scalar(select(Transcript).where(Transcript.call_id == call_id)) is None
        assert db.scalar(select(Analysis).where(Analysis.call_id == call_id)) is None
        assert db.get(Call, untouched_call["id"]) is not None


def test_delete_does_not_remove_files_outside_upload_dir(client, tmp_path):
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    set_upload_dir(upload_dir)
    outside_upload_file = tmp_path / "outside-upload.wav"
    outside_upload_file.write_text("not real audio")

    with SessionLocal() as db:
        call = Call(
            filename="outside-upload.wav",
            file_path=str(outside_upload_file),
            status=CallStatus.uploaded,
        )
        db.add(call)
        db.commit()
        call_id = call.id

    response = client.delete(f"/calls/{call_id}")
    assert response.status_code == 200, response.text
    assert response.json()["deleted_file"] is False
    assert outside_upload_file.exists()
