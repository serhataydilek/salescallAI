from pathlib import Path
import sys

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
load_dotenv(ROOT / ".env")

from app.services.transcription.faster_whisper_transcription import (  # noqa: E402
    FasterWhisperTranscriptionService,
)


def main() -> int:
    if len(sys.argv) != 2:
        print("FAIL")
        print("Usage: python scripts\\test_faster_whisper_transcription.py <audio-file-path>")
        return 1

    audio_path = Path(sys.argv[1]).expanduser()

    try:
        transcript = FasterWhisperTranscriptionService().transcribe(str(audio_path))
    except Exception as exc:
        print("FAIL")
        print(exc)
        return 1

    print(transcript)
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

