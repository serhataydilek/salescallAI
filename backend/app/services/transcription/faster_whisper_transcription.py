import os
from pathlib import Path

from app.services.transcription.base import TranscriptionService


class FasterWhisperTranscriptionService(TranscriptionService):
    def __init__(self, model_size: str | None = None) -> None:
        self.model_size = model_size or os.getenv("WHISPER_MODEL_SIZE", "base")

    def transcribe(self, file_path: str) -> str:
        audio_path = Path(file_path)
        if not audio_path.exists():
            raise RuntimeError(f"Audio file does not exist: {file_path}")
        if audio_path.stat().st_size == 0:
            raise RuntimeError("Audio file is empty.")

        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError(
                "faster-whisper is not installed. Install local AI dependencies or set USE_MOCK_TRANSCRIPTION=true."
            ) from exc

        try:
            model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
            segments, _ = model.transcribe(str(audio_path))
            transcript = " ".join(segment.text.strip() for segment in segments if segment.text.strip())
        except ValueError as exc:
            raise RuntimeError(f"Unsupported audio or transcription configuration: {exc}") from exc
        except Exception as exc:
            raise RuntimeError(f"Local faster-whisper transcription failed: {exc}") from exc

        if not transcript:
            raise RuntimeError("Local transcription returned an empty transcript.")

        return transcript
