from dataclasses import dataclass

from app.schemas import AnalysisBase


DO_NOT_CONTACT_TERMS = [
    "do not call again",
    "please don't call again",
    "don't call this number again",
    "do not contact",
    "please don't contact",
    "tekrar aramayÄ±n",
    "tekrar aramayın",
    "tekrar aramayin",
    "bu numarayÄ± tekrar aramayÄ±n",
    "bu numarayı tekrar aramayın",
    "bu numarayi tekrar aramayin",
]
QUOTA_TERMS = ["hot lead", "quota", "kota"]
UNPREPARED_TERMS = [
    "just woke up",
    "haven't had coffee",
    "no coffee",
    "kahvemi iÃ§meden",
    "kahvemi içmeden",
    "kahvemi icmeden",
    "uykusuzum",
    "forgot",
    "forgetting",
    "i keep forgetting",
    "marketing team wrote",
]
PRODUCT_UNCERTAINTY_TERMS = [
    "software for businesses",
    "does a lot of stuff",
    "ne iÅŸe yarÄ±yor",
    "ne işe yarıyor",
    "ne ise yariyor",
    "can't explain",
    "cannot explain",
    "probably",
]
PRICE_UNKNOWN_TERMS = [
    "what does it cost",
    "price",
    "pricing",
    "fiyat",
    "bilmiyorum",
    "bakmam lazÄ±m",
    "bakmam lazım",
    "bakmam lazim",
    "get back to you",
    "need to get back",
    "have not figured that out",
]
WEBSITE_FAILURE_TERMS = [
    "google it",
    "let me google",
    "website down",
    "website up",
    "site aÃ§Ä±lÄ±yor mu",
    "site açılıyor mu",
    "site aciliyor mu",
]
TIME_CONSTRAINT_TERMS = [
    "another meeting",
    "two minutes",
    "only have a few minutes",
    "toplantÄ±m var",
    "toplantım var",
    "toplantim var",
]
IGNORES_TIME_TERMS = ["this won't take long", "perfect, this will not take long", "one last thing", "hot lead"]
REFERRAL_TERMS = ["colleagues", "referral", "refer", "might be interested", "anyone else"]
VALUE_TERMS = ["roi", "value", "pilot", "risk", "return", "deÄŸer", "deger"]


@dataclass(frozen=True)
class CriticalFailureSignals:
    do_not_contact: bool
    quota_pressure: bool
    unprepared: bool
    product_uncertainty: bool
    price_unknown: bool
    website_failure: bool
    ignored_time_constraint: bool
    referral_after_rejection: bool

    @property
    def count(self) -> int:
        return sum(
            [
                self.do_not_contact,
                self.quota_pressure,
                self.unprepared,
                self.product_uncertainty,
                self.price_unknown,
                self.website_failure,
                self.ignored_time_constraint,
                self.referral_after_rejection,
            ]
        )

    @property
    def is_catastrophic(self) -> bool:
        return self.count >= 2 or self.do_not_contact


def detect_critical_failures(transcript: str) -> CriticalFailureSignals:
    lower_text = transcript.lower()
    do_not_contact = _contains_any(lower_text, DO_NOT_CONTACT_TERMS)
    price_unknown = _contains_any(lower_text, PRICE_UNKNOWN_TERMS) and not _contains_any(lower_text, VALUE_TERMS)
    ignored_time_constraint = _contains_any(lower_text, TIME_CONSTRAINT_TERMS) and _contains_any(
        lower_text, IGNORES_TIME_TERMS
    )

    return CriticalFailureSignals(
        do_not_contact=do_not_contact,
        quota_pressure=_contains_any(lower_text, QUOTA_TERMS),
        unprepared=_contains_any(lower_text, UNPREPARED_TERMS),
        product_uncertainty=_contains_any(lower_text, PRODUCT_UNCERTAINTY_TERMS),
        price_unknown=price_unknown,
        website_failure=_contains_any(lower_text, WEBSITE_FAILURE_TERMS),
        ignored_time_constraint=ignored_time_constraint,
        referral_after_rejection=do_not_contact and _contains_any(lower_text, REFERRAL_TERMS),
    )


def calibrate_analysis(transcript: str, analysis: AnalysisBase) -> AnalysisBase:
    signals = detect_critical_failures(transcript)
    if not signals.is_catastrophic:
        return analysis

    data = analysis.model_dump()

    if signals.count >= 2:
        data["overall_score"] = min(data["overall_score"], 20)
        data["opening_score"] = min(data["opening_score"], 10)
        data["discovery_score"] = min(data["discovery_score"], 15)
        data["objection_handling_score"] = min(data["objection_handling_score"], 10)
        data["closing_score"] = min(data["closing_score"], 5)
        data["follow_up_score"] = min(data["follow_up_score"], 5)

    if signals.do_not_contact:
        data["overall_score"] = min(data["overall_score"], 20)
        data["closing_score"] = min(data["closing_score"], 5)
        data["follow_up_score"] = min(data["follow_up_score"], 5)
    if signals.quota_pressure:
        data["overall_score"] = min(data["overall_score"], 25)
        data["closing_score"] = min(data["closing_score"], 5)
    if signals.unprepared and signals.product_uncertainty:
        data["opening_score"] = min(data["opening_score"], 10)
        data["discovery_score"] = min(data["discovery_score"], 15)
    if signals.price_unknown:
        data["objection_handling_score"] = min(data["objection_handling_score"], 10)
    if signals.referral_after_rejection:
        data["follow_up_score"] = min(data["follow_up_score"], 5)

    data["top_3_mistakes"] = _prioritized_items(
        _critical_mistakes(signals),
        data["top_3_mistakes"],
        size=3,
    )
    data["suggested_improvements"] = _prioritized_items(
        _critical_improvements(signals),
        data["suggested_improvements"],
        size=max(3, len(data["suggested_improvements"])),
    )
    data["short_summary"] = _critical_summary(signals)

    return AnalysisBase.model_validate(data)


def _critical_mistakes(signals: CriticalFailureSignals) -> list[str]:
    mistakes: list[str] = []
    if signals.do_not_contact:
        mistakes.append("The salesperson violated a clear customer boundary after being told not to call again.")
    if signals.unprepared or signals.product_uncertainty:
        mistakes.append("The salesperson sounded unprepared and failed to explain a credible value proposition.")
    if signals.quota_pressure:
        mistakes.append("The salesperson introduced quota pressure instead of focusing on the customer's problem.")
    if signals.referral_after_rejection:
        mistakes.append("The salesperson asked for referrals after the customer rejected further contact.")
    if signals.price_unknown:
        mistakes.append("The salesperson did not know pricing and gave no ROI, value, or pilot-based response.")
    return mistakes


def _critical_improvements(signals: CriticalFailureSignals) -> list[str]:
    improvements: list[str] = []
    if signals.do_not_contact:
        improvements.append("Respect customer boundaries immediately and end the call professionally when contact is refused.")
    if signals.unprepared or signals.product_uncertainty:
        improvements.append("Prepare a concise product explanation and customer-specific value proposition before calling.")
    if signals.quota_pressure:
        improvements.append("Never make quota pressure part of the buyer conversation; keep the call centered on customer value.")
    if signals.price_unknown:
        improvements.append("Answer pricing concerns with clear ranges, ROI logic, or a low-risk pilot instead of uncertainty.")
    if signals.referral_after_rejection:
        improvements.append("Do not ask for referrals after rejection; close respectfully and update contact preferences.")
    return improvements


def _critical_summary(signals: CriticalFailureSignals) -> str:
    reasons = []
    if signals.do_not_contact:
        reasons.append("customer boundary violation")
    if signals.unprepared or signals.product_uncertainty:
        reasons.append("unprofessional preparation and weak value proposition")
    if signals.quota_pressure:
        reasons.append("quota pressure")
    if signals.referral_after_rejection:
        reasons.append("referral ask after rejection")
    if signals.price_unknown:
        reasons.append("unknown pricing without value framing")

    reason_text = ", ".join(reasons[:4]) or "multiple professionalism failures"
    return f"This is a brand-damaging sales call because of {reason_text}. The conversation requires fundamental coaching before another customer call."


def _prioritized_items(primary_items: list[str], existing_items: list[str], *, size: int) -> list[str]:
    items = []
    for item in [*primary_items, *existing_items]:
        if item and item not in items:
            items.append(item)
        if len(items) == size:
            break
    return items


def _contains_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)
