import os

from app.services.llm.base import LLMService
from app.services.llm.mock_llm import MockLLMService
from app.services.llm.ollama_llm import OllamaLLMService
from app.services.transcription.base import TranscriptionService
from app.services.transcription.faster_whisper_transcription import FasterWhisperTranscriptionService
from app.services.transcription.mock_transcription import MockTranscriptionService


def env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_transcription_service() -> TranscriptionService:
    if env_flag("USE_MOCK_TRANSCRIPTION", True):
        return MockTranscriptionService()
    return FasterWhisperTranscriptionService()


def get_llm_service() -> LLMService:
    if env_flag("USE_MOCK_LLM", True):
        return MockLLMService()
    return OllamaLLMService()

