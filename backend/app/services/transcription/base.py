from abc import ABC, abstractmethod


class TranscriptionService(ABC):
    @abstractmethod
    def transcribe(self, file_path: str) -> str:
        raise NotImplementedError

