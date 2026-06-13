import json
from pathlib import Path
import sys
from typing import Any

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
SAMPLES_DIR = PROJECT_ROOT / "data" / "samples"
RESULTS_DIR = ROOT / "eval_results"
RESULTS_PATH = RESULTS_DIR / "ollama_model_comparison.json"

sys.path.append(str(ROOT))
load_dotenv(ROOT / ".env")

from app.schemas import AnalysisBase  # noqa: E402
from app.services.llm.ollama_llm import OllamaLLMService  # noqa: E402


def quality_warnings(transcript_file: str, analysis: AnalysisBase) -> list[str]:
    warnings: list[str] = []

    if len(analysis.top_3_mistakes) != 3:
        warnings.append("top_3_mistakes does not contain exactly 3 items")
    if not analysis.missed_questions:
        warnings.append("missed_questions is empty")
    if len(analysis.suggested_improvements) < 3:
        warnings.append("suggested_improvements has fewer than 3 items")
    if len(analysis.better_example_responses) < 2:
        warnings.append("better_example_responses has fewer than 2 items")
    if not analysis.short_summary.strip():
        warnings.append("short_summary is empty")

    if transcript_file == "bad_sales_call.txt":
        if analysis.overall_score >= 75:
            warnings.append("overall_score looks suspiciously high for bad_sales_call.txt")
        if analysis.discovery_score >= 75:
            warnings.append("discovery_score looks suspiciously high for bad_sales_call.txt")
        if analysis.closing_score >= 70 or analysis.follow_up_score >= 70:
            warnings.append("closing/follow_up scores look suspiciously high for bad_sales_call.txt")

    return warnings


def empty_result(model_name: str, transcript_file: str, error_message: str) -> dict[str, Any]:
    return {
        "model_name": model_name,
        "transcript_file": transcript_file,
        "success": False,
        "error_message": error_message,
        "overall_score": None,
        "opening_score": None,
        "discovery_score": None,
        "objection_handling_score": None,
        "closing_score": None,
        "follow_up_score": None,
        "top_3_mistakes": [],
        "missed_questions": [],
        "suggested_improvements": [],
        "better_example_responses": [],
        "short_summary": "",
        "warnings": [],
        "raw_analysis": None,
    }


def result_from_analysis(model_name: str, transcript_file: str, analysis: AnalysisBase) -> dict[str, Any]:
    raw_analysis = analysis.model_dump()
    return {
        "model_name": model_name,
        "transcript_file": transcript_file,
        "success": True,
        "error_message": "",
        "overall_score": analysis.overall_score,
        "opening_score": analysis.opening_score,
        "discovery_score": analysis.discovery_score,
        "objection_handling_score": analysis.objection_handling_score,
        "closing_score": analysis.closing_score,
        "follow_up_score": analysis.follow_up_score,
        "top_3_mistakes": analysis.top_3_mistakes,
        "missed_questions": analysis.missed_questions,
        "suggested_improvements": analysis.suggested_improvements,
        "better_example_responses": analysis.better_example_responses,
        "short_summary": analysis.short_summary,
        "warnings": quality_warnings(transcript_file, analysis),
        "raw_analysis": raw_analysis,
    }


def print_result(result: dict[str, Any]) -> None:
    status = "PASS" if result["success"] else "FAIL"
    print(f"\n[{status}] {result['model_name']} -> {result['transcript_file']}")

    if not result["success"]:
        print(f"  Error: {result['error_message']}")
        return

    print(
        "  Scores: "
        f"overall={result['overall_score']}, "
        f"opening={result['opening_score']}, "
        f"discovery={result['discovery_score']}, "
        f"objections={result['objection_handling_score']}, "
        f"closing={result['closing_score']}, "
        f"follow_up={result['follow_up_score']}"
    )
    print(f"  Summary: {result['short_summary']}")

    if result["warnings"]:
        for warning in result["warnings"]:
            print(f"  WARNING: {warning}")
    else:
        print("  Warnings: none")


def summarize(results: list[dict[str, Any]]) -> None:
    print("\n=== Model Summary ===")
    model_names = sorted({result["model_name"] for result in results})
    for model_name in model_names:
        model_results = [result for result in results if result["model_name"] == model_name]
        successes = [result for result in model_results if result["success"]]
        warning_count = sum(len(result["warnings"]) for result in successes)
        if successes:
            average_score = sum(result["overall_score"] for result in successes) / len(successes)
            print(
                f"{model_name}: {len(successes)}/{len(model_results)} succeeded, "
                f"avg overall={average_score:.1f}, warnings={warning_count}"
            )
        else:
            print(f"{model_name}: 0/{len(model_results)} succeeded, warnings={warning_count}")


def main() -> int:
    model_names = sys.argv[1:]
    if not model_names:
        print("Usage: python scripts\\compare_ollama_models.py <model> [<model> ...]")
        return 1

    transcript_paths = sorted(SAMPLES_DIR.glob("*.txt"))
    if not transcript_paths:
        print(f"No transcripts found in {SAMPLES_DIR}")
        return 1

    results: list[dict[str, Any]] = []
    for model_name in model_names:
        service = OllamaLLMService(model=model_name)
        for transcript_path in transcript_paths:
            transcript_file = transcript_path.name
            transcript = transcript_path.read_text(encoding="utf-8")
            try:
                raw_analysis = service.analyze_sales_call(transcript)
                analysis = AnalysisBase.model_validate(raw_analysis)
                result = result_from_analysis(model_name, transcript_file, analysis)
            except Exception as exc:
                result = empty_result(model_name, transcript_file, str(exc))

            results.append(result)
            print_result(result)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
    summarize(results)
    print(f"\nSaved results to {RESULTS_PATH}")

    return 0 if all(result["success"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())

