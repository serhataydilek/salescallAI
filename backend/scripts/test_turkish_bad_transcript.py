import json
from pathlib import Path
import sys

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
sys.path.append(str(ROOT))
load_dotenv(ROOT / ".env")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.schemas import AnalysisBase  # noqa: E402
from app.services.providers import get_llm_service  # noqa: E402
from app.services.title_service import generate_call_title  # noqa: E402

TURKISH_MARKERS = [
    "satıcı",
    "müşteri",
    "görüşme",
    "fiyat",
    "değer",
    "sonraki",
    "takip",
    "soru",
]


def contains_turkish_text(analysis: AnalysisBase) -> bool:
    combined_text = " ".join(
        [
            analysis.short_summary,
            analysis.talk_ratio_feedback,
            " ".join(analysis.top_3_mistakes),
            " ".join(analysis.missed_questions),
            " ".join(analysis.suggested_improvements),
            " ".join(analysis.better_example_responses),
        ]
    ).lower()
    return any(marker in combined_text for marker in TURKISH_MARKERS)


def main() -> int:
    transcript_path = PROJECT_ROOT / "data" / "samples" / "turkish_bad_sales_call.txt"
    transcript = transcript_path.read_text(encoding="utf-8")

    generated_title = generate_call_title(transcript, "ttttt")
    print(f"Generated title: {generated_title}")
    if generated_title.strip().lower() == "ttttt":
        print("FAIL: generic title was not replaced.")
        return 1

    analysis = AnalysisBase.model_validate(get_llm_service().analyze_sales_call(transcript))
    print(json.dumps(analysis.model_dump(), ensure_ascii=False, indent=2))
    print(f"Overall score: {analysis.overall_score}")

    if not 30 <= analysis.overall_score <= 55:
        print("FAIL: weak Turkish transcript should score between 30 and 55.")
        return 1
    if len(analysis.top_3_mistakes) != 3:
        print("FAIL: top_3_mistakes must contain exactly 3 items.")
        return 1
    if not contains_turkish_text(analysis):
        print("FAIL: report text does not appear to be Turkish.")
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
