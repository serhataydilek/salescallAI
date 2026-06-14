from pathlib import Path

from app.schemas import AnalysisBase
from app.services.analysis.calibration import calibrate_analysis
from app.services.assistant_coaching import build_assistant_coaching_cards
from app.services.llm.mock_llm import MockLLMService


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def analyze_sample(name: str) -> tuple[AnalysisBase, str]:
    transcript = (PROJECT_ROOT / "data" / "samples" / name).read_text(encoding="utf-8")
    analysis = calibrate_analysis(transcript, AnalysisBase.model_validate(MockLLMService().analyze_sales_call(transcript)))
    return analysis, transcript


def card_text(analysis: AnalysisBase, transcript: str) -> str:
    cards = build_assistant_coaching_cards(analysis, transcript)
    return " ".join(
        f"{card.issue} {card.why_it_matters} {card.try_saying_this}" for card in cards
    ).lower()


def test_strong_call_returns_constructive_assistant_coaching_without_false_next_step_claim():
    analysis, transcript = analyze_sample("strong_sales_call.txt")
    cards = build_assistant_coaching_cards(analysis, transcript)
    text = card_text(analysis, transcript)

    assert 3 <= len(cards) <= 5
    assert "kapanış zaten iyi" in text or "mevcut metrik" in text
    assert "no concrete next step" not in text
    assert "without a concrete next step" not in text
    assert "somut bir sonraki adım olmadan" not in text


def test_feature_dump_card_recommends_discovery_before_pitching_with_replacement_sentence():
    analysis, transcript = analyze_sample("feature_dump_sales_call.txt")
    text = card_text(analysis, transcript)

    assert "yeterli keşif" in text
    assert "özellikleri anlatmadan önce" in text


def test_weak_price_objection_card_uses_price_roi_and_pilot_value_framing():
    analysis, transcript = analyze_sample("weak_price_objection_sales_call.txt")
    text = card_text(analysis, transcript)

    assert "fiyat itiraz" in text or "fiyat endiş" in text
    assert "roi" in text or "değer" in text
    assert "pilot" in text


def test_catastrophic_card_respects_customer_boundaries_and_does_not_continue_call():
    analysis, transcript = analyze_sample("catastrophic_sales_call.txt")
    text = card_text(analysis, transcript)

    assert "net bir sınır" in text
    assert "sizi tekrar aramayacağım" in text
    assert "schedule" not in text
    assert "pilot" not in text


def test_turkish_transcript_returns_turkish_assistant_coaching_text():
    analysis, transcript = analyze_sample("weak_price_objection_sales_call.txt")
    turkish_transcript = (
        "Satıcı: Merhaba, fiyat endişenizi anlıyorum ama çok yüksek olmaz.\n"
        "Müşteri: Değeri nasıl ölçeceğiz?\n"
        "Satıcı: Sonra konuşuruz."
    )
    turkish_text = card_text(analysis, turkish_transcript)
    english_transcript = """Salesperson: Hi, thanks for joining. SalesMirror has dashboards, exports, trend analysis, and scoring.
Customer: What problem would it solve for us?
Salesperson: It has a lot of features and reports.
Customer: Our managers need better follow-up coaching.
Salesperson: You can check the website later."""
    english_analysis = calibrate_analysis(
        english_transcript,
        AnalysisBase.model_validate(MockLLMService().analyze_sales_call(english_transcript)),
    )
    english_text = card_text(english_analysis, english_transcript)

    assert "fiyat" in turkish_text
    assert "endişenizi anlıyorum" in turkish_text
    assert "walk me through" in english_text or "what happens today" in english_text
