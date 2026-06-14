from pathlib import Path

from app.models import Call
from app.services.assistant_coaching import AssistantCoachingCard, build_assistant_coaching_cards


SECTION_SEPARATOR = "-" * 72


def score_label(score: int) -> str:
    if score >= 80:
        return "Strong call"
    if score >= 60:
        return "Decent call"
    if score >= 40:
        return "Weak call"
    return "Poor call"


class ReportService:
    def build_text_report(self, call: Call) -> str:
        if not call.analysis:
            return "Analysis is not available for this call yet."

        analysis = call.analysis
        transcript = call.transcript.text if call.transcript else "Transcript is not available."
        assistant_cards = build_assistant_coaching_cards(analysis, transcript)
        source_type = self._source_type(call.file_path)
        source_detail = self._source_detail(call.file_path)

        sections = [
            "# SalesMirror Sales Coaching Report",
            SECTION_SEPARATOR,
            f"Title: {call.filename}",
            f"Created: {call.created_at.strftime('%Y-%m-%d %H:%M')}",
            f"Source Type: {source_type}",
            f"Source: {source_detail}",
            f"Status: {call.status.value}",
            "",
            f"Overall Score: {analysis.overall_score}/100",
            f"Score Label: {score_label(analysis.overall_score)}",
            "",
            "## Score Breakdown",
            SECTION_SEPARATOR,
            f"Opening: {analysis.opening_score}/100",
            f"Discovery: {analysis.discovery_score}/100",
            f"Objection Handling: {analysis.objection_handling_score}/100",
            f"Closing: {analysis.closing_score}/100",
            f"Follow Up: {analysis.follow_up_score}/100",
            "",
            "## Analysis Summary",
            SECTION_SEPARATOR,
            analysis.short_summary,
            "",
            "## Talk Ratio Feedback",
            SECTION_SEPARATOR,
            analysis.talk_ratio_feedback,
            "",
            "## Coaching Opportunities",
            SECTION_SEPARATOR,
            *self._numbered_items(analysis.top_3_mistakes),
            "",
            "## Assistant Coaching",
            SECTION_SEPARATOR,
            *self._assistant_card_items(assistant_cards),
            "",
            "## Missed Questions",
            SECTION_SEPARATOR,
            *self._numbered_items(analysis.missed_questions),
            "",
            "## Suggested Improvements",
            SECTION_SEPARATOR,
            *self._numbered_items(analysis.suggested_improvements),
            "",
            "## Better Example Responses",
            SECTION_SEPARATOR,
            *self._numbered_items(analysis.better_example_responses),
            "",
            "## Transcript",
            SECTION_SEPARATOR,
            transcript,
        ]
        return "\n".join(sections)

    def _source_type(self, file_path: str) -> str:
        if file_path == "manual-transcript":
            return "Pasted transcript"
        return "Audio upload"

    def _source_detail(self, file_path: str) -> str:
        if file_path == "manual-transcript":
            return "Pasted transcript"
        stored_name = Path(file_path).name
        if "_" in stored_name:
            return stored_name.split("_", 1)[1]
        return stored_name or "Uploaded audio"

    def _numbered_items(self, items: list[str]) -> list[str]:
        if not items:
            return ["None provided."]
        return [f"{index}. {item}" for index, item in enumerate(items, start=1)]

    def _assistant_card_items(self, cards: list[AssistantCoachingCard]) -> list[str]:
        if not cards:
            return ["None provided."]

        lines: list[str] = []
        for index, card in enumerate(cards, start=1):
            lines.extend(
                [
                    f"{index}. Moment / Issue: {card.issue}",
                    f"   Why it matters: {card.why_it_matters}",
                    f"   Try saying this instead: {card.try_saying_this}",
                ]
            )
        return lines
