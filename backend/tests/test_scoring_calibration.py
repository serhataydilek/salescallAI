from pathlib import Path

from app.schemas import AnalysisBase
from app.services.llm.mock_llm import MockLLMService


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def analyze_sample(name: str) -> AnalysisBase:
    transcript = (PROJECT_ROOT / "data" / "samples" / name).read_text(encoding="utf-8")
    return AnalysisBase.model_validate(MockLLMService().analyze_sales_call(transcript))


def test_mock_score_calibration_good_medium_and_catastrophic_samples():
    good = analyze_sample("good_sales_call.txt")
    medium = analyze_sample("medium_sales_call.txt")
    catastrophic = analyze_sample("catastrophic_sales_call.txt")

    assert 80 <= good.overall_score <= 90
    assert 45 <= medium.overall_score <= 70
    assert 10 <= catastrophic.overall_score <= 25
    assert catastrophic.follow_up_score == 0
    assert catastrophic.closing_score <= 5
