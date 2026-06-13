ANALYSIS_JSON_SCHEMA = {
    "overall_score": 0,
    "opening_score": 0,
    "discovery_score": 0,
    "objection_handling_score": 0,
    "closing_score": 0,
    "follow_up_score": 0,
    "talk_ratio_feedback": "",
    "top_3_mistakes": [],
    "missed_questions": [],
    "suggested_improvements": [],
    "better_example_responses": [],
    "short_summary": "",
}


SALES_ANALYSIS_RUBRIC = """
Evaluate this sales call transcript as a practical sales coach.

Evaluate these areas:
- opening quality: greeting, agenda, rapport, permission, and clear reason for the call
- discovery questions: quality and quantity of open-ended questions
- understanding of customer pain points: pain, urgency, impact, success criteria, and decision context
- objection handling: whether objections are acknowledged, explored, and answered clearly
- price objection handling: whether cost concerns are tied to value, ROI, risk, or a pilot
- product-value fit: whether the rep connects capabilities to the customer's stated needs
- closing attempt: whether the rep asks for commitment or advances the conversation
- follow-up / next step: whether timing, owner, next action, and success criteria are clear
- professionalism: clarity, tone, listening, buyer focus, and credibility
- talk ratio feedback: provide a qualitative estimate only unless speaker timing is available

Scoring scale:
- 80-100: strong call
- 60-79: decent call with clear improvement areas
- 40-59: weak call with major gaps
- 0-39: very poor call

Scoring rules:
- Avoid being too generous. Score based on evidence in the transcript.
- If the salesperson does not ask discovery questions, discovery_score must be low.
- If there is no clear next step, closing_score and follow_up_score must be low.
- If a customer raises a price objection and the salesperson does not address value, ROI, risk, or a pilot, objection_handling_score must be low.
- If the salesperson gives vague answers such as "it uses AI", "it should be reasonable", "you can get back to me", or "check the website later", treat this as weak sales execution.
- If the customer asks important questions and the salesperson answers vaguely, overall_score should usually be 55 or lower.
- If there is weak discovery, vague ROI/value explanation, and no concrete next step, overall_score must not be above 60.
- If the salesperson avoids defining success measurements, closing_score and follow_up_score should be low even if the tone is polite.
- If a price objection is answered with "it is not expensive" or "AI products are usually expensive" without ROI, risk, value, or pilot framing, objection_handling_score must be low.
- If the call is strong, still identify minor but useful coaching improvements instead of inventing severe mistakes.

Output rules:
- Return strict JSON only.
- Do not return markdown.
- Do not return explanations outside JSON.
- Write all human-readable string values in the same primary language as the transcript.
- If the transcript is primarily Turkish, return Turkish coaching text.
- If the transcript is primarily English, return English coaching text.
- Keep JSON keys in English exactly as specified. Only translate string values inside the JSON.
- top_3_mistakes must contain exactly 3 items.
- missed_questions should usually contain 2 to 5 useful questions the salesperson could have asked.
- suggested_improvements must contain at least 3 useful improvements.
- better_example_responses must contain at least 2 useful example responses.
- short_summary must be clear, specific, and grounded in the transcript.

Return this exact JSON shape:
{
  "overall_score": 0,
  "opening_score": 0,
  "discovery_score": 0,
  "objection_handling_score": 0,
  "closing_score": 0,
  "follow_up_score": 0,
  "talk_ratio_feedback": "",
  "top_3_mistakes": [],
  "missed_questions": [],
  "suggested_improvements": [],
  "better_example_responses": [],
  "short_summary": ""
}

All scores must be integers from 0 to 100. Array fields should contain clear coaching points as strings.
"""


def build_analysis_prompt(transcript: str) -> str:
    return f"{SALES_ANALYSIS_RUBRIC}\n\nTranscript:\n{transcript}"
