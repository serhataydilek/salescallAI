from pathlib import Path
import sys

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
load_dotenv(ROOT / ".env")

from app.schemas import AnalysisBase  # noqa: E402
from app.services.llm.ollama_llm import OllamaLLMService  # noqa: E402
from app.services.transcription.faster_whisper_transcription import (  # noqa: E402
    FasterWhisperTranscriptionService,
)


def print_list(title: str, items: list[str]) -> None:
    print(title)
    for item in items:
        print(f"- {item}")


def main() -> int:
    if len(sys.argv) != 2:
        print("FAIL")
        print("Usage: python scripts\\test_local_ai_pipeline.py <audio-file-path>")
        return 1

    audio_path = Path(sys.argv[1]).expanduser()
    if not audio_path.exists():
        print("FAIL")
        print(f"Audio file does not exist: {audio_path}")
        return 1
    if audio_path.stat().st_size == 0:
        print("FAIL")
        print(f"Audio file is empty: {audio_path}")
        return 1

    try:
        transcript = FasterWhisperTranscriptionService().transcribe(str(audio_path))
        analysis = AnalysisBase.model_validate(OllamaLLMService().analyze_sales_call(transcript))
    except Exception as exc:
        print("FAIL")
        print(exc)
        return 1

    print("Transcript")
    print(transcript)
    print(f"\nTranscript length: {len(transcript)} characters")
    print(f"\nOverall score: {analysis.overall_score}")
    print_list("\nTop 3 mistakes", analysis.top_3_mistakes)
    print_list("\nSuggested improvements", analysis.suggested_improvements)
    print(f"\nShort summary: {analysis.short_summary}")
    print("\nPASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
