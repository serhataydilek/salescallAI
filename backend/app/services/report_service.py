from app.models import Call


class ReportService:
    def build_text_report(self, call: Call) -> str:
        if not call.analysis:
            return "Analysis is not available for this call yet."

        analysis = call.analysis
        transcript = call.transcript.text if call.transcript else "Transcript is not available."

        sections = [
            "SalesMirror Coaching Report",
            f"Call: {call.filename}",
            f"Status: {call.status.value}",
            "",
            "Summary",
            analysis.short_summary,
            "",
            "Scores",
            f"Overall: {analysis.overall_score}/100",
            f"Opening: {analysis.opening_score}/100",
            f"Discovery: {analysis.discovery_score}/100",
            f"Objection Handling: {analysis.objection_handling_score}/100",
            f"Closing: {analysis.closing_score}/100",
            f"Follow Up: {analysis.follow_up_score}/100",
            "",
            "Talk Ratio Feedback",
            analysis.talk_ratio_feedback,
            "",
            "Top 3 Mistakes",
            *[f"- {item}" for item in analysis.top_3_mistakes],
            "",
            "Missed Questions",
            *[f"- {item}" for item in analysis.missed_questions],
            "",
            "Suggested Improvements",
            *[f"- {item}" for item in analysis.suggested_improvements],
            "",
            "Better Example Responses",
            *[f"- {item}" for item in analysis.better_example_responses],
            "",
            "Transcript",
            transcript,
        ]
        return "\n".join(sections)

