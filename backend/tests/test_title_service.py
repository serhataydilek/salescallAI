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
    transcript = """Salesperson: Yeah hi, is this Dave?
Customer: It's Sandra.
Salesperson: I just woke up and forgot the product points.
Customer: What does it cost?
Salesperson: I need to get back to you on that. Let me Google the website.
Customer: I have another meeting in two minutes.
Salesperson: Can I mark you as a hot lead? My quota resets Friday.
Customer: Please don't call this number again.
Salesperson: Do you have any colleagues who might be interested?"""

    generated_title = generate_call_title(transcript, "test")

    assert generated_title != "Price Objection"
    assert any(term in generated_title for term in ["Brand", "Unprofessional", "Failed", "No Value"])


def test_weak_price_or_budget_transcript_generates_price_related_title():
    transcript = """Salesperson: Thanks for joining today.
Customer: The price is too expensive and our budget is tight.
Salesperson: I am not sure, but it should be reasonable. I can send info and we can talk later."""

    assert "Price Objection" in generate_call_title(transcript, "untitled")


def test_price_handled_with_value_and_pilot_does_not_default_to_price_objection():
    transcript = """Salesperson: Thanks for joining today. What coaching metric matters most?
Customer: The price is too expensive and our budget is tight.
Salesperson: We can prove value with a low-risk pilot and review ROI next Tuesday."""

    generated_title = generate_call_title(transcript, "Price Objection")

    assert generated_title != "Price Objection"


def test_turkish_catastrophic_transcript_overrides_price_title():
    transcript = """Satıcı: Kahvemi içmeden aradım ve ürün maddelerini unuttum.
Müşteri: Ne işe yarıyor?
Satıcı: Site açılıyor mu diye Google'dan bakmam lazım.
Müşteri: Fiyatı ne kadar?
Satıcı: Bilmiyorum, bakmam lazım. Kotam için sizi hot lead yapabilir miyim?
Müşteri: Bu numarayı tekrar aramayın."""

    generated_title = generate_call_title(transcript, "Price Objection")

    assert generated_title != "Price Objection"
    assert any(term in generated_title for term in ["Brand", "Unprofessional", "Failed", "No Value"])


def test_pilot_or_demo_transcript_generates_pilot_related_title():
    generated_title = generate_call_title(PILOT_TRANSCRIPT, "manual transcript")

    assert "Pilot" in generated_title or "Demo" in generated_title
