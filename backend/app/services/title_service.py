from pathlib import Path


GENERIC_FILENAMES = {
    "audio",
    "call",
    "recording",
    "sample",
    "test",
    "untitled",
    "upload",
    "voice",
}


def is_generic_call_title(title: str | None) -> bool:
    if not title:
        return True

    stem = Path(title).stem.lower().strip()
    normalized = "".join(character for character in stem if character.isalnum() or character.isspace()).strip()
    if not normalized:
        return True

    return normalized in GENERIC_FILENAMES or normalized.startswith("test")


def generate_call_title(transcript: str, current_title: str | None = None) -> str:
    if current_title and not is_generic_call_title(current_title):
        return current_title[:255]

    lower_text = transcript.lower()
    title_parts: list[str] = []

    if any(term in lower_text for term in ["price", "cost", "expensive", "budget", "fiyat", "pahali", "pahalı"]):
        title_parts.append("Price Objection")
    if any(term in lower_text for term in ["pilot", "trial", "demo", "deneme"]):
        title_parts.append("Pilot Discussion")
    if any(term in lower_text for term in ["onboarding", "training", "new reps", "new hires", "yeni"]):
        title_parts.append("Sales Training")

    has_next_step = any(
        term in lower_text
        for term in [
            "next step",
            "follow up",
            "follow-up",
            "meet next",
            "schedule",
            "calendar",
            "send you",
            "tomorrow",
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
        ]
    )
    vague_follow_up = any(
        term in lower_text
        for term in [
            "you can check the website later",
            "you can get back to me",
            "get back to me",
            "siz donersiniz",
            "siz dönersiniz",
            "sonra bakariz",
            "sonra bakarız",
        ]
    )
    if not has_next_step or vague_follow_up:
        title_parts.append("Weak Follow-up")

    question_count = transcript.count("?")
    if question_count <= 1 or "what kind of problem" in lower_text:
        title_parts.append("Discovery Gap")

    if not title_parts:
        title_parts.append("Sales Call Analysis")

    unique_parts = list(dict.fromkeys(title_parts))
    return " and ".join(unique_parts[:2])[:255]
