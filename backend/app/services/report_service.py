from pathlib import Path

from app.models import Call


SECTION_SEPARATOR = "-" * 72


class ReportService:
    def build_text_report(self, call: Call) -> str:
        if not call.analysis:
            return "Analysis is not available for this call yet."

        analysis = call.analysis
        transcript = call.transcript.text if call.transcript else "Transcript is not available."

        sections = [
            "SALESMIRROR SALES COACHING REPORT",
            SECTION_SEPARATOR,
            f"Title: {call.filename}",
            f"Date: {call.created_at.strftime('%Y-%m-%d %H:%M')}",
            f"Source: {self._source_label(call.file_path)}",
            f"Status: {call.status.value}",
            "",
            "OVERALL SCORE",
            SECTION_SEPARATOR,
            f"{analysis.overall_score}/100 - {self._score_label(analysis.overall_score)}",
            "",
            "CATEGORY SCORES",
            SECTION_SEPARATOR,
            f"Opening: {analysis.opening_score}/100",
            f"Discovery: {analysis.discovery_score}/100",
            f"Objection Handling: {analysis.objection_handling_score}/100",
            f"Closing: {analysis.closing_score}/100",
            f"Follow Up: {analysis.follow_up_score}/100",
            "",
            "ANALYSIS SUMMARY",
            SECTION_SEPARATOR,
            analysis.short_summary,
            "",
            "TALK RATIO FEEDBACK",
            SECTION_SEPARATOR,
            analysis.talk_ratio_feedback,
            "",
            "COACHING OPPORTUNITIES",
            SECTION_SEPARATOR,
            *self._bullets(analysis.top_3_mistakes),
            "",
            "MISSED QUESTIONS",
            SECTION_SEPARATOR,
            *self._bullets(analysis.missed_questions),
            "",
            "SUGGESTED IMPROVEMENTS",
            SECTION_SEPARATOR,
            *self._bullets(analysis.suggested_improvements),
            "",
            "BETTER EXAMPLE RESPONSES",
            SECTION_SEPARATOR,
            *self._bullets(analysis.better_example_responses),
            "",
            "TRANSCRIPT",
            SECTION_SEPARATOR,
            transcript,
            "",
            "TODO: Native PDF export is not implemented yet. Use browser print and Save as PDF for now.",
        ]
        return "\n".join(sections)

    def _score_label(self, score: int) -> str:
        if score >= 80:
            return "Strong call"
        if score >= 60:
            return "Decent call"
        if score >= 40:
            return "Weak call"
        return "Poor call"

    def _source_label(self, file_path: str) -> str:
        if file_path == "manual-transcript":
            return "Pasted transcript"

        stored_name = Path(file_path).name
        if "_" in stored_name:
            return stored_name.split("_", 1)[1]
        return stored_name or "Uploaded audio"

    def _bullets(self, items: list[str]) -> list[str]:
        if not items:
            return ["- None provided."]
        return [f"- {item}" for item in items]
