from typing import Any

from app.services.llm.base import LLMService


GREETING_TERMS = ["hi", "hello", "thanks for joining", "nice to meet", "good morning", "good afternoon"]
DISCOVERY_TERMS = ["what", "why", "how", "tell me", "walk me through", "problem", "challenge", "goal", "impact"]
PRICE_TERMS = ["price", "cost", "expensive", "budget", "pricing", "fiyat", "pahali", "pahalı"]
VALUE_TERMS = ["roi", "return", "value", "impact", "save", "conversion", "pilot", "success metric", "business case"]
NEXT_STEP_TERMS = [
    "next step",
    "follow up",
    "follow-up",
    "schedule",
    "calendar",
    "send you",
    "meet next",
    "tomorrow",
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
]
VAGUE_RESPONSE_TERMS = [
    "it uses ai",
    "ai products usually expensive",
    "not expensive",
    "should be reasonable",
    "you can check the website later",
    "you can get back to me",
    "get back to me",
    "sonra bakariz",
    "sonra bakarız",
    "siz donersiniz",
    "siz dönersiniz",
    "buyuk ihtimalle",
    "büyük ihtimalle",
    "ai oldugu icin buluyor",
    "ai olduğu için buluyor",
]


class MockLLMService(LLMService):
    def analyze_sales_call(self, transcript: str) -> dict[str, Any]:
        lower_text = transcript.lower()
        salesperson_lines = [line for line in transcript.splitlines() if line.lower().startswith("salesperson:")]
        question_count = sum(line.count("?") for line in salesperson_lines)

        has_opening = any(term in lower_text for term in GREETING_TERMS)
        has_discovery = question_count >= 2 and any(term in lower_text for term in DISCOVERY_TERMS)
        has_price_objection = any(term in lower_text for term in PRICE_TERMS)
        has_value_response = any(term in lower_text for term in VALUE_TERMS)
        has_next_step = any(term in lower_text for term in NEXT_STEP_TERMS)
        has_vague_response = any(term in lower_text for term in VAGUE_RESPONSE_TERMS)

        opening_score = 82 if has_opening else 45
        discovery_score = 78 if has_discovery else 35
        objection_score = 78
        if has_price_objection and not has_value_response:
            objection_score = 35
        elif has_price_objection and has_vague_response:
            objection_score = 42
        elif has_price_objection:
            objection_score = 68

        closing_score = 76 if has_next_step else 38
        follow_up_score = 78 if has_next_step else 35

        if has_vague_response:
            discovery_score = min(discovery_score, 50)
            closing_score = min(closing_score, 48)
            follow_up_score = min(follow_up_score, 45)

        overall_score = round(
            (opening_score + discovery_score + objection_score + closing_score + follow_up_score) / 5
        )
        if not has_discovery or not has_next_step or (has_price_objection and not has_value_response):
            overall_score = min(overall_score, 55)
        if has_vague_response:
            overall_score = min(overall_score, 52)
        overall_score = max(30, min(overall_score, 92))

        return {
            "overall_score": overall_score,
            "opening_score": opening_score,
            "discovery_score": discovery_score,
            "objection_handling_score": objection_score,
            "closing_score": closing_score,
            "follow_up_score": follow_up_score,
            "talk_ratio_feedback": self._talk_ratio_feedback(salesperson_lines, transcript),
            "top_3_mistakes": self._top_mistakes(has_discovery, has_price_objection, has_value_response, has_next_step),
            "missed_questions": [
                "What specific sales or onboarding problem are you trying to solve first?",
                "How are you measuring whether call coaching is working today?",
                "Who else needs to be involved before you can approve a pilot?",
                "What would make the price feel justified for your team?",
            ],
            "suggested_improvements": [
                "Ask discovery questions before explaining product features.",
                "Tie the product value to a measurable business outcome such as conversion, ramp time, or coaching consistency.",
                "When price comes up, acknowledge the concern and connect the cost to ROI or a low-risk pilot.",
                "End with a specific next step that includes owner, date, and success criteria.",
            ],
            "better_example_responses": [
                "Before I explain the product, can you walk me through what happens after a rep finishes a sales call today?",
                "I understand the price concern. If a pilot showed faster ramp time for new reps, would that make the investment easier to justify?",
                "I will send a sample report today, and we can review it Tuesday with your onboarding metric in mind.",
            ],
            "short_summary": self._summary(overall_score, has_discovery, has_price_objection, has_value_response, has_next_step),
        }

    def _talk_ratio_feedback(self, salesperson_lines: list[str], transcript: str) -> str:
        total_lines = len([line for line in transcript.splitlines() if line.strip()])
        if total_lines == 0:
            return "Talk ratio cannot be estimated because the transcript is empty."
        rep_ratio = len(salesperson_lines) / total_lines
        if rep_ratio > 0.6:
            return "The salesperson appears to talk more than the customer. Use more discovery questions to create a better listening balance."
        return "The conversation appears reasonably balanced, but real talk ratio requires speaker timing or diarization."

    def _top_mistakes(
        self, has_discovery: bool, has_price_objection: bool, has_value_response: bool, has_next_step: bool
    ) -> list[str]:
        mistakes: list[str] = []
        if not has_discovery:
            mistakes.append("The salesperson did not ask enough discovery questions before positioning the solution.")
        if has_price_objection and not has_value_response:
            mistakes.append("The price concern was not tied to value, ROI, risk reduction, or a measurable pilot.")
        if not has_next_step:
            mistakes.append("The call ended without a concrete next step, owner, date, or success criteria.")

        backups = [
            "The product explanation should connect more directly to the customer's stated pain.",
            "The salesperson should ask who is involved in the decision process.",
            "The close should confirm what the customer needs to see before moving forward.",
        ]
        for backup in backups:
            if len(mistakes) == 3:
                break
            if backup not in mistakes:
                mistakes.append(backup)
        return mistakes[:3]

    def _summary(
        self,
        overall_score: int,
        has_discovery: bool,
        has_price_objection: bool,
        has_value_response: bool,
        has_next_step: bool,
    ) -> str:
        if overall_score <= 55:
            return (
                "This is a weak sales call because the salesperson does not build enough customer context, "
                "does not create a clear business case, and does not secure a concrete next step."
            )
        if has_price_objection and has_value_response and has_next_step and has_discovery:
            return (
                "This is a decent sales call with useful discovery and follow-up, but the salesperson can make the value case more specific."
            )
        return "This call has useful moments, but the report highlights clear opportunities to improve discovery, value framing, and closing."
