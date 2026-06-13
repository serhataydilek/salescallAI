from typing import Any

from app.services.llm.base import LLMService


class MockLLMService(LLMService):
    def analyze_sales_call(self, transcript: str) -> dict[str, Any]:
        has_next_step = "next step" in transcript.lower() or "follow-up" in transcript.lower()
        return {
            "overall_score": 84 if has_next_step else 72,
            "opening_score": 88,
            "discovery_score": 86,
            "objection_handling_score": 78,
            "closing_score": 86 if has_next_step else 58,
            "follow_up_score": 88 if has_next_step else 55,
            "talk_ratio_feedback": (
                "Mock estimate: the rep appears to talk slightly more than ideal. "
                "Use diarization later for measured talk ratio."
            ),
            "top_3_mistakes": [
                "The price objection is acknowledged but could be tied more directly to business impact.",
                "Discovery questions are present, but decision process and urgency are not fully explored.",
                "The next step could include clearer success criteria for the follow-up.",
            ],
            "missed_questions": [
                "Who else needs to approve a coaching workflow?",
                "What conversion metric would make this project successful?",
                "What happens if the team does not fix this demo conversion issue?",
            ],
            "suggested_improvements": [
                "Quantify the business cost of missed conversions before discussing product value.",
                "Ask one question about decision criteria and one about implementation risk.",
                "Confirm the exact follow-up owner, date, and expected artifact.",
            ],
            "better_example_responses": [
                "I understand price matters. If the pilot improves demo conversion by even a few points, would that justify expanding it?",
                "Before I suggest a workflow, can you walk me through what happens after a demo today?",
                "I will send the sample report today, and we can review it Tuesday with the conversion metric in mind.",
            ],
            "short_summary": "Mock local analysis: the call has a solid opening and discovery, with room to improve business impact framing and closing specificity.",
        }

