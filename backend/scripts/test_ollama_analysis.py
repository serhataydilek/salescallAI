import json
from pathlib import Path
import sys

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
sys.path.append(str(ROOT))
load_dotenv(ROOT / ".env")

from app.schemas import AnalysisBase  # noqa: E402
from app.services.llm.ollama_llm import OllamaLLMService  # noqa: E402


def quality_warnings(analysis: AnalysisBase) -> list[str]:
    warnings: list[str] = []
    if len(analysis.top_3_mistakes) != 3:
        warnings.append("top_3_mistakes should contain exactly 3 items.")
    if len(analysis.missed_questions) == 0:
        warnings.append("missed_questions is empty.")
    if len(analysis.suggested_improvements) < 3:
        warnings.append("suggested_improvements should contain at least 3 items.")
    if len(analysis.better_example_responses) < 2:
        warnings.append("better_example_responses should contain at least 2 items.")
    return warnings


def main() -> int:
    transcript_path = PROJECT_ROOT / "data" / "samples" / "price_objection_sales_call.txt"

    try:
        transcript = transcript_path.read_text(encoding="utf-8")
        result = OllamaLLMService().analyze_sales_call(transcript)
        validated = AnalysisBase.model_validate(result)
    except Exception as exc:
        print("FAIL")
        print(exc)
        return 1

    print(json.dumps(validated.model_dump(), indent=2))
    warnings = quality_warnings(validated)
    for warning in warnings:
        print(f"WARNING: {warning}")
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
