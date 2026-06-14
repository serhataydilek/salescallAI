from pathlib import Path

from app.services.analysis.calibration import detect_critical_failures


GENERIC_TITLES = {
    "asd",
    "asdf",
    "audio",
    "call",
    "deneme",
    "manual transcript",
    "recording",
    "sample",
    "sales call",
    "test",
    "transcript",
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

    compact = normalized.replace(" ", "")
    if normalized in GENERIC_TITLES or compact in GENERIC_TITLES:
        return True
    if compact.startswith("test") and compact[4:].isdigit():
        return True
    if len(compact) <= 6 and len(set(compact)) == 1:
        return True

    return False


def generate_call_title(transcript: str, current_title: str | None = None) -> str:
    critical_signals = detect_critical_failures(transcript)
    if critical_signals.is_catastrophic:
        if critical_signals.unprepared or critical_signals.quota_pressure or critical_signals.do_not_contact:
            return "Brand-Damaging Sales Call"
        if critical_signals.product_uncertainty:
            return "Failed CRM Pitch with No Value Proposition"
        return "Unprofessional Cold Call and Failed Discovery"

    if current_title and not is_generic_call_title(current_title):
        return current_title[:255]

    lower_text = transcript.lower()
    title_parts: list[str] = []

    if _contains_any(lower_text, ["price", "cost", "expensive", "budget", "fiyat", "pahali", "pahalı"]):
        title_parts.append("Price Objection")
    if _contains_any(lower_text, ["pilot", "trial", "demo", "deneme"]):
        title_parts.append("Sales Coaching Pilot Discussion")
    if _contains_any(
        lower_text,
        ["onboarding", "training", "new reps", "new hires", "yeni", "eğitim", "egitim", "oryantasyon"],
    ):
        title_parts.append("New Rep Training Workflow Call")

    has_next_step = _contains_any(
        lower_text,
        [
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
            "sonraki adım",
            "sonraki adim",
            "takip",
            "toplantı",
            "toplanti",
            "görüşelim",
            "goruselim",
        ],
    )
    vague_follow_up = _contains_any(
        lower_text,
        [
            "you can check the website later",
            "you can get back to me",
            "get back to me",
            "siz donersiniz",
            "siz dönersiniz",
            "sonra bakariz",
            "sonra bakarız",
            "web sitesine bakarsınız",
            "web sitesine bakarsiniz",
        ],
    )
    if not has_next_step or vague_follow_up:
        title_parts.append("Weak Follow-up")

    question_count = transcript.count("?")
    if question_count <= 1 or _contains_any(lower_text, ["what kind of problem", "hangi problemi"]):
        title_parts.append("Discovery Gap in Sales Call")

    if not title_parts:
        title_parts.append("Sales Call Analysis")

    unique_parts = list(dict.fromkeys(title_parts))
    if len(unique_parts) == 1:
        return unique_parts[0][:255]
    return " and ".join(unique_parts[:2])[:255]


def _contains_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)
