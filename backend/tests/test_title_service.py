import pytest

from app.services.title_service import generate_call_title, is_generic_call_title


PILOT_TRANSCRIPT = """Salesperson: Thanks for joining today. What would make a pilot useful?
Customer: We need a demo and a low-risk trial for managers.
Salesperson: I can send a sample report and schedule a follow-up next Tuesday."""


@pytest.mark.parametrize(
    "title",
    [
        "test",
        "test1",
        "ttttt",
        "deneme",
        "asd",
        "call",
        "sales call",
        "untitled",
        "transcript",
        "manual transcript",
    ],
)
def test_generic_titles_are_ignored(title):
    assert is_generic_call_title(title) is True
    assert generate_call_title(PILOT_TRANSCRIPT, title) != title


def test_meaningful_titles_are_preserved():
    title = "Acme onboarding pilot review"
    assert is_generic_call_title(title) is False
    assert generate_call_title(PILOT_TRANSCRIPT, title) == title


@pytest.mark.parametrize("title", ["aaaaaa", "xxxxx", "111111"])
def test_repeated_character_short_titles_are_generic(title):
    assert is_generic_call_title(title) is True


def test_catastrophic_transcript_does_not_default_to_price_objection():
    transcript = """Salesperson: This is not worth discussing.
Customer: I need help with coaching.
Salesperson: Just check the website later."""

    generated_title = generate_call_title(transcript, "test")

    assert generated_title != "Price Objection"
    assert "Weak Follow-up" in generated_title or "Discovery Gap" in generated_title


def test_price_or_budget_transcript_generates_price_related_title():
    transcript = """Salesperson: Thanks for joining today.
Customer: The price is too expensive and our budget is tight.
Salesperson: We can discuss ROI and a pilot next Tuesday."""

    assert "Price Objection" in generate_call_title(transcript, "untitled")


def test_pilot_or_demo_transcript_generates_pilot_related_title():
    generated_title = generate_call_title(PILOT_TRANSCRIPT, "manual transcript")

    assert "Pilot" in generated_title or "Demo" in generated_title
