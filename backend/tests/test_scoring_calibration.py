from pathlib import Path

from app.schemas import AnalysisBase
from app.services.analysis.calibration import calibrate_analysis
from app.services.llm.mock_llm import MockLLMService
from app.services.title_service import generate_call_title


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def analyze_sample(name: str) -> tuple[AnalysisBase, str]:
    transcript = (PROJECT_ROOT / "data" / "samples" / name).read_text(encoding="utf-8")
    analysis = calibrate_analysis(transcript, AnalysisBase.model_validate(MockLLMService().analyze_sales_call(transcript)))
    return analysis, generate_call_title(transcript, "manual transcript")


def test_strong_sales_call_scores_high_and_keeps_report_consistent():
    analysis, title = analyze_sample("strong_sales_call.txt")
    summary = analysis.short_summary.lower()
    mistakes = " ".join(analysis.top_3_mistakes).lower()

    assert 85 <= analysis.overall_score <= 94
    assert 80 <= analysis.opening_score <= 95
    assert 80 <= analysis.discovery_score <= 95
    assert 75 <= analysis.objection_handling_score <= 90
    assert analysis.closing_score >= 80
    assert analysis.follow_up_score >= 80
    assert title != "Price Objection"
    assert "price objection" not in title.lower()
    assert "concrete next step" in summary
    assert "somut bir sonraki ad" not in summary
    assert "no concrete next step" not in summary
    assert "somut bir sonraki ad" not in mistakes
    assert "yeterli m" not in summary


def test_feature_dump_sales_call_is_capped_as_weak_feature_led_pitch():
    analysis, title = analyze_sample("feature_dump_sales_call.txt")
    summary = analysis.short_summary.lower()

    assert 40 <= analysis.overall_score <= 55
    assert analysis.discovery_score <= 55
    assert analysis.closing_score <= 50
    assert analysis.follow_up_score <= 50
    assert title in {"Feature-Led Sales Pitch with Weak Discovery", "Generic Sales Coaching Pitch"}
    assert "feature dumping" in summary
    assert "business-context" in summary
    assert "success measurement" in summary


def test_weak_price_objection_has_mid_score_and_low_objection_close_followup():
    analysis, title = analyze_sample("weak_price_objection_sales_call.txt")
    summary = analysis.short_summary.lower()

    assert 58 <= analysis.overall_score <= 70
    assert 65 <= analysis.discovery_score <= 85
    assert analysis.objection_handling_score <= 50
    assert 35 <= analysis.closing_score <= 55
    assert 35 <= analysis.follow_up_score <= 55
    assert title in {"Weak Price Objection Handling", "Sales Coaching Pitch with Weak ROI Framing"}
    assert "decent discovery" in summary
    assert "price handling is vague" in summary
    assert "roi/value framing" in summary


def test_catastrophic_sales_call_gets_strict_caps_and_brand_damaging_title():
    analysis, title = analyze_sample("catastrophic_sales_call.txt")
    summary = analysis.short_summary.lower()

    assert analysis.overall_score <= 25
    assert analysis.opening_score <= 10
    assert analysis.discovery_score <= 15
    assert analysis.objection_handling_score <= 10
    assert analysis.closing_score <= 5
    assert analysis.follow_up_score <= 5
    assert title != "Price Objection"
    assert title in {"Brand-Damaging Sales Call", "Unprofessional Cold Call and Failed Discovery"}
    assert "customer boundary violation" in summary
    assert "unprofessional preparation" in summary
    assert "weak value proposition" in summary
    assert "quota pressure" in summary
    assert "unknown pricing" in summary
