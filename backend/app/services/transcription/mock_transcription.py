from pathlib import Path

from app.services.transcription.base import TranscriptionService


class MockTranscriptionService(TranscriptionService):
    def transcribe(self, file_path: str) -> str:
        filename = Path(file_path).name
        return (
            f"Mock transcript for {filename}.\n\n"
            "Sales Rep: Hi, thanks for taking the time today. I wanted to learn "
            "more about your current sales workflow and see if SalesMirror can help.\n"
            "Prospect: Sure. We are struggling to understand why some demos do not convert.\n"
            "Sales Rep: What happens after a demo today? What are the biggest blockers "
            "for your team? How are you measuring rep performance now?\n"
            "Prospect: Price is a concern, and we are not sure whether the team will use it.\n"
            "Sales Rep: That makes sense. Teams usually start with a small pilot so they "
            "can measure coaching value before expanding.\n"
            "Sales Rep: As a next step, I can send a summary and schedule a follow-up "
            "call next Tuesday to review a sample report."
        )

