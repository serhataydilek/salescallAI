from pathlib import Path
import sys

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
sys.path.append(str(ROOT))
load_dotenv(ROOT / ".env")

from app.schemas import AnalysisBase  # noqa: E402
from app.services.analysis.calibration import calibrate_analysis  # noqa: E402
from app.services.providers import env_flag, get_llm_service  # noqa: E402
from app.services.title_service import generate_call_title  # noqa: E402


SAMPLES = [
    (
        "strong",
        PROJECT_ROOT / "data" / "samples" / "strong_sales_call.txt",
        {"overall": (85, 94), "opening": (80, 95), "discovery": (80, 95), "objection": (75, 90), "closing": (80, 95), "follow_up": (80, 95)},
    ),
    (
        "feature_dump",
        PROJECT_ROOT / "data" / "samples" / "feature_dump_sales_call.txt",
        {"overall": (40, 55), "discovery": (0, 55), "closing": (0, 50), "follow_up": (0, 50)},
    ),
    (
        "weak_price_objection",
        PROJECT_ROOT / "data" / "samples" / "weak_price_objection_sales_call.txt",
        {"overall": (58, 70), "discovery": (65, 85), "objection": (25, 50), "closing": (35, 55), "follow_up": (35, 55)},
    ),
    (
        "catastrophic",
        PROJECT_ROOT / "data" / "samples" / "catastrophic_sales_call.txt",
        {"overall": (0, 25), "opening": (0, 10), "discovery": (0, 15), "objection": (0, 10), "closing": (0, 5), "follow_up": (0, 5)},
    ),
]


def main() -> int:
    service = get_llm_service()
    using_mock = env_flag("USE_MOCK_LLM", True)
    failures: list[str] = []

    for label, path, ranges in SAMPLES:
        transcript = path.read_text(encoding="utf-8")
        analysis = calibrate_analysis(transcript, AnalysisBase.model_validate(service.analyze_sales_call(transcript)))
        title = generate_call_title(transcript, "manual transcript")
        scores = {
            "overall": analysis.overall_score,
            "opening": analysis.opening_score,
            "discovery": analysis.discovery_score,
            "objection": analysis.objection_handling_score,
            "closing": analysis.closing_score,
            "follow_up": analysis.follow_up_score,
        }
        status = "PASS"
        for score_name, (minimum, maximum) in ranges.items():
            if not minimum <= scores[score_name] <= maximum:
                status = "FAIL"
                failures.append(f"{label} {score_name} score {scores[score_name]} outside {minimum}-{maximum}")

        print(
            f"{status}: {label}: title={title!r}, overall={analysis.overall_score}, "
            f"opening={analysis.opening_score}, discovery={analysis.discovery_score}, "
            f"objection={analysis.objection_handling_score}, closing={analysis.closing_score}, "
            f"follow_up={analysis.follow_up_score}"
        )

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1

    mode = "mock" if using_mock else "configured local LLM"
    print(f"PASS: score calibration is within expected ranges using {mode}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
