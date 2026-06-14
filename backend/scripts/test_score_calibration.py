from pathlib import Path
import sys

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
sys.path.append(str(ROOT))
load_dotenv(ROOT / ".env")

from app.schemas import AnalysisBase  # noqa: E402
from app.services.providers import env_flag, get_llm_service  # noqa: E402


SAMPLES = [
    ("good", PROJECT_ROOT / "data" / "samples" / "good_sales_call.txt", 75, 100),
    ("medium", PROJECT_ROOT / "data" / "samples" / "medium_sales_call.txt", 45, 75),
    ("catastrophic", PROJECT_ROOT / "data" / "samples" / "catastrophic_sales_call.txt", 0, 25),
]


def main() -> int:
    service = get_llm_service()
    using_mock = env_flag("USE_MOCK_LLM", True)
    failures: list[str] = []

    for label, path, minimum, maximum in SAMPLES:
        transcript = path.read_text(encoding="utf-8")
        analysis = AnalysisBase.model_validate(service.analyze_sales_call(transcript))
        score = analysis.overall_score
        print(f"{label}: overall={score}, discovery={analysis.discovery_score}, closing={analysis.closing_score}, follow_up={analysis.follow_up_score}")

        if score < minimum or score > maximum:
            failures.append(f"{label} score {score} outside expected range {minimum}-{maximum}")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1

    mode = "mock" if using_mock else "configured local LLM"
    print(f"PASS: score calibration is within expected ranges using {mode}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
