from pathlib import Path

from app.schemas import AnalysisBase
from app.services.analysis.calibration import calibrate_analysis
from app.services.llm.mock_llm import MockLLMService


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def analyze_sample(name: str) -> AnalysisBase:
    transcript = (PROJECT_ROOT / "data" / "samples" / name).read_text(encoding="utf-8")
    return calibrate_analysis(transcript, AnalysisBase.model_validate(MockLLMService().analyze_sales_call(transcript)))


def test_mock_score_calibration_good_medium_and_catastrophic_samples():
    good = analyze_sample("good_sales_call.txt")
    medium = analyze_sample("medium_sales_call.txt")
    catastrophic = analyze_sample("catastrophic_sales_call.txt")

    assert 80 <= good.overall_score <= 90
    assert 45 <= medium.overall_score <= 70
    assert 10 <= catastrophic.overall_score <= 25
    assert catastrophic.opening_score <= 10
    assert catastrophic.discovery_score <= 15
    assert catastrophic.objection_handling_score <= 10
    assert catastrophic.follow_up_score == 0
    assert catastrophic.closing_score <= 5


def test_turkish_catastrophic_sample_gets_strict_category_caps():
    catastrophic = analyze_sample("catastrophic_turkish_sales_call.txt")

    assert catastrophic.overall_score <= 25
    assert catastrophic.opening_score <= 10
    assert catastrophic.discovery_score <= 15
    assert catastrophic.objection_handling_score <= 10
    assert catastrophic.closing_score <= 5
    assert catastrophic.follow_up_score <= 5
