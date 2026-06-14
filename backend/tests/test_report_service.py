from datetime import datetime

import pytest

from app.models import Analysis, Call, CallStatus, Transcript
from app.services.report_service import ReportService, score_label


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (100, "Strong call"),
        (80, "Strong call"),
        (79, "Decent call"),
        (60, "Decent call"),
        (59, "Weak call"),
        (40, "Weak call"),
        (39, "Poor call"),
        (0, "Poor call"),
    ],
)
def test_score_label_boundaries(score, expected):
    assert score_label(score) == expected


def test_text_report_includes_major_sections_and_latest_content():
    call = Call(
        filename="Manager coaching report",
        file_path="manual-transcript",
        status=CallStatus.analyzed,
        created_at=datetime(2026, 6, 14, 10, 30),
    )
    call.transcript = Transcript(
        text="Salesperson: What would make this pilot successful?\nCustomer: Better follow-up coaching."
    )
    call.analysis = Analysis(
        overall_score=55,
        opening_score=70,
        discovery_score=45,
        objection_handling_score=60,
        closing_score=50,
        follow_up_score=52,
        talk_ratio_feedback="The salesperson should create more room for the customer.",
        top_3_mistakes=["Discovery was shallow.", "The close was vague.", "Value was not quantified."],
        missed_questions=["Who approves the pilot?", "How do you measure coaching quality?"],
        suggested_improvements=["Ask about decision criteria.", "Confirm a date-owned next step."],
        better_example_responses=["Would a two-week pilot prove the value clearly enough?"],
        short_summary="The call needs clearer discovery and follow-up.",
    )

    report = ReportService().build_text_report(call)

    for expected_text in [
        "# SalesMirror Sales Coaching Report",
        "Title: Manager coaching report",
        "Created: 2026-06-14 10:30",
        "Source Type: Pasted transcript",
        "Source: Pasted transcript",
        "Status: analyzed",
        "Overall Score: 55/100",
        "Score Label: Weak call",
        "## Score Breakdown",
        "Opening: 70/100",
        "Discovery: 45/100",
        "Objection Handling: 60/100",
        "Closing: 50/100",
        "Follow Up: 52/100",
        "## Analysis Summary",
        "The call needs clearer discovery and follow-up.",
        "## Talk Ratio Feedback",
        "The salesperson should create more room for the customer.",
        "## Coaching Opportunities",
        "1. Discovery was shallow.",
        "## Missed Questions",
        "1. Who approves the pilot?",
        "## Suggested Improvements",
        "1. Ask about decision criteria.",
        "## Better Example Responses",
        "1. Would a two-week pilot prove the value clearly enough?",
        "## Transcript",
        "Better follow-up coaching.",
    ]:
        assert expected_text in report
