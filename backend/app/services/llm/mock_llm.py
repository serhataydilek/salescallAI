from typing import Any

from app.services.analysis.calibration import detect_sales_quality_signals
from app.services.llm.base import LLMService


GREETING_TERMS = ["hi", "hello", "thanks for joining", "nice to meet", "good morning", "good afternoon", "merhaba"]
DISCOVERY_TERMS = [
    "what",
    "why",
    "how",
    "tell me",
    "walk me through",
    "problem",
    "challenge",
    "goal",
    "impact",
    "ne",
    "neden",
    "nasıl",
    "nasil",
    "problem",
    "hedef",
]
PRICE_TERMS = ["price", "cost", "expensive", "budget", "pricing", "fiyat", "pahali", "pahalı", "bütçe", "butce"]
VALUE_TERMS = [
    "roi",
    "return",
    "value",
    "impact",
    "save",
    "conversion",
    "pilot",
    "success metric",
    "business case",
    "değer",
    "deger",
    "yatırım getirisi",
    "yatirim getirisi",
    "dönüşüm",
    "donusum",
]
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
    "sonraki adım",
    "sonraki adim",
    "takip",
    "toplantı",
    "toplanti",
]
CONCRETE_NEXT_STEP_TERMS = [
    "next step",
    "schedule",
    "calendar",
    "meet next",
    "review it with",
    "book a review",
    "tomorrow",
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "by the end of today",
    "sonraki adÄ±m",
    "sonraki adim",
    "toplantÄ±",
    "toplanti",
]
SUCCESS_TERMS = [
    "success criteria",
    "success metric",
    "pilot criteria",
    "measure",
    "measurable",
    "criteria",
    "scorecard",
    "baÅŸarÄ± kriteri",
    "basari kriteri",
    "metrik",
    "Ã¶lÃ§",
    "olc",
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
    "çok pahalı değil",
    "cok pahali degil",
    "web sitesine bakarsınız",
    "web sitesine bakarsiniz",
]
DO_NOT_CONTACT_TERMS = [
    "do not call again",
    "please don't call again",
    "don't call this number again",
    "do not contact me",
    "don't contact me",
    "tekrar aramayÄ±n",
    "tekrar aramayin",
    "beni aramayÄ±n",
    "beni aramayin",
]
UNPREPARED_TERMS = [
    "just woke up",
    "haven't had coffee",
    "forgot",
    "forgetting",
    "i keep forgetting",
    "marketing team wrote",
    "i don't know pricing",
    "do not know pricing",
    "have not figured that out",
    "need to get back to you on that",
    "let me google",
    "google it",
    "website up",
]
QUOTA_PRESSURE_TERMS = [
    "hot lead",
    "quota",
    "quota resets",
    "my quota",
]
REFERRAL_TERMS = ["colleagues", "referral", "refer", "anyone else", "might be interested"]
TIME_CONSTRAINT_TERMS = [
    "only have a few minutes",
    "another meeting",
    "meeting in two minutes",
    "don't have much time",
    "sadece birkaÃ§ dakikam var",
    "sadece birkac dakikam var",
]
TURKISH_MARKERS = [
    "merhaba",
    "müşteri",
    "musteri",
    "satıcı",
    "satici",
    "görüşme",
    "gorusme",
    "fiyat",
    "pahalı",
    "pahali",
    "sonraki",
    "takip",
    "değer",
    "deger",
    "ürün",
    "urun",
]


class MockLLMService(LLMService):
    def analyze_sales_call(self, transcript: str) -> dict[str, Any]:
        lower_text = transcript.lower()
        quality_signals = detect_sales_quality_signals(transcript)
        is_turkish = any(marker in lower_text for marker in TURKISH_MARKERS)
        salesperson_lines = [
            line
            for line in transcript.splitlines()
            if line.lower().startswith("salesperson:") or line.lower().startswith("satıcı:") or line.lower().startswith("satici:")
        ]
        question_count = sum(line.count("?") for line in salesperson_lines)

        has_opening = any(term in lower_text for term in GREETING_TERMS)
        has_discovery = quality_signals.strong_discovery or (
            question_count >= 2 and any(term in lower_text for term in DISCOVERY_TERMS)
        )
        has_price_objection = any(term in lower_text for term in PRICE_TERMS)
        has_value_response = quality_signals.value_pilot_framing or any(term in lower_text for term in VALUE_TERMS)
        has_next_step = quality_signals.concrete_next_step or any(term in lower_text for term in CONCRETE_NEXT_STEP_TERMS)
        has_success_criteria = quality_signals.success_metric_question or any(term in lower_text for term in SUCCESS_TERMS)
        has_vague_response = quality_signals.vague_roi_or_pricing or any(term in lower_text for term in VAGUE_RESPONSE_TERMS)
        critical_flags = {
            "do_not_contact": any(term in lower_text for term in DO_NOT_CONTACT_TERMS),
            "unprepared": any(term in lower_text for term in UNPREPARED_TERMS),
            "quota_pressure": any(term in lower_text for term in QUOTA_PRESSURE_TERMS),
            "ignored_time_constraint": any(term in lower_text for term in TIME_CONSTRAINT_TERMS)
            and any(term in lower_text for term in ["this won't take long", "one last thing", "hot lead"]),
        }
        asks_referral_after_rejection = critical_flags["do_not_contact"] and any(
            term in lower_text for term in REFERRAL_TERMS
        )

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

        is_strong_call = (
            has_opening
            and has_discovery
            and has_value_response
            and has_next_step
            and has_success_criteria
            and not quality_signals.weak_price_response
            and not quality_signals.feature_dumping
            and not has_vague_response
            and not any(critical_flags.values())
        )
        if is_strong_call:
            opening_score = max(opening_score, 86)
            discovery_score = max(discovery_score, 88)
            objection_score = max(objection_score, 84)
            closing_score = max(closing_score, 86)
            follow_up_score = max(follow_up_score, 88)

        if quality_signals.is_feature_dump:
            discovery_score = min(discovery_score, 52)
            closing_score = min(closing_score, 48)
            follow_up_score = min(follow_up_score, 45)
        elif quality_signals.is_weak_price_objection:
            objection_score = min(objection_score, 46)
            closing_score = min(closing_score, 52)
            follow_up_score = min(follow_up_score, 52)
        elif has_vague_response:
            discovery_score = min(discovery_score, 50)
            closing_score = min(closing_score, 48)
            follow_up_score = min(follow_up_score, 45)
        if critical_flags["ignored_time_constraint"]:
            closing_score = min(closing_score, 5)
            follow_up_score = min(follow_up_score, 5)
        if asks_referral_after_rejection:
            follow_up_score = 0

        overall_score = round(
            (opening_score + discovery_score + objection_score + closing_score + follow_up_score) / 5
        )
        if is_strong_call:
            overall_score = max(overall_score, 85)
        if not has_discovery or not has_next_step or (has_price_objection and not has_value_response):
            overall_score = min(overall_score, 55)
        if has_vague_response:
            overall_score = min(overall_score, 52)
        if critical_flags["do_not_contact"]:
            overall_score = min(overall_score, 20)
        if critical_flags["unprepared"] or critical_flags["quota_pressure"]:
            overall_score = min(overall_score, 25)
        if sum(1 for flag in critical_flags.values() if flag) >= 2:
            overall_score = min(overall_score, 20)
        overall_score = min(overall_score, 92)
        if not any(critical_flags.values()):
            overall_score = max(30, overall_score)

        if is_turkish:
            return self._turkish_response(
                overall_score,
                opening_score,
                discovery_score,
                objection_score,
                closing_score,
                follow_up_score,
                salesperson_lines,
                transcript,
                has_discovery,
                has_price_objection,
                has_value_response,
                has_next_step,
            )

        return self._english_response(
            overall_score,
            opening_score,
            discovery_score,
            objection_score,
            closing_score,
            follow_up_score,
            salesperson_lines,
            transcript,
            has_discovery,
            has_price_objection,
            has_value_response,
            has_next_step,
        )

    def _english_response(
        self,
        overall_score: int,
        opening_score: int,
        discovery_score: int,
        objection_score: int,
        closing_score: int,
        follow_up_score: int,
        salesperson_lines: list[str],
        transcript: str,
        has_discovery: bool,
        has_price_objection: bool,
        has_value_response: bool,
        has_next_step: bool,
    ) -> dict[str, Any]:
        return {
            "overall_score": overall_score,
            "opening_score": opening_score,
            "discovery_score": discovery_score,
            "objection_handling_score": objection_score,
            "closing_score": closing_score,
            "follow_up_score": follow_up_score,
            "talk_ratio_feedback": self._english_talk_ratio_feedback(salesperson_lines, transcript),
            "top_3_mistakes": self._english_top_mistakes(
                has_discovery, has_price_objection, has_value_response, has_next_step
            ),
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
            "short_summary": self._english_summary(
                overall_score, has_discovery, has_price_objection, has_value_response, has_next_step
            ),
        }

    def _turkish_response(
        self,
        overall_score: int,
        opening_score: int,
        discovery_score: int,
        objection_score: int,
        closing_score: int,
        follow_up_score: int,
        salesperson_lines: list[str],
        transcript: str,
        has_discovery: bool,
        has_price_objection: bool,
        has_value_response: bool,
        has_next_step: bool,
    ) -> dict[str, Any]:
        return {
            "overall_score": overall_score,
            "opening_score": opening_score,
            "discovery_score": discovery_score,
            "objection_handling_score": objection_score,
            "closing_score": closing_score,
            "follow_up_score": follow_up_score,
            "talk_ratio_feedback": self._turkish_talk_ratio_feedback(salesperson_lines, transcript),
            "top_3_mistakes": self._turkish_top_mistakes(
                has_discovery, has_price_objection, has_value_response, has_next_step
            ),
            "missed_questions": [
                "Bugün çözmeye çalıştığınız en önemli satış veya onboarding problemi nedir?",
                "Çağrı koçluğunun işe yaradığını hangi metrikle ölçeceksiniz?",
                "Pilot kararı için başka kimlerin onayı gerekiyor?",
                "Fiyatın makul görünmesi için hangi değeri veya sonucu kanıtlamamız gerekir?",
            ],
            "suggested_improvements": [
                "Ürün özelliklerini anlatmadan önce müşterinin mevcut sürecini ve problemini keşfedin.",
                "Değeri dönüşüm, ramp süresi veya koçluk tutarlılığı gibi ölçülebilir bir iş sonucuna bağlayın.",
                "Fiyat itirazı geldiğinde endişeyi kabul edip ROI, risk azaltma veya düşük riskli pilot çerçevesiyle yanıt verin.",
                "Görüşmeyi sahip, tarih ve başarı kriteri net olan somut bir sonraki adımla bitirin.",
            ],
            "better_example_responses": [
                "Ürünü anlatmadan önce, bir satış görüşmesinden sonra ekibinizde ne olduğunu adım adım paylaşır mısınız?",
                "Fiyat endişenizi anlıyorum. Pilot yeni temsilcilerin ramp süresini kısalttığını gösterirse yatırım daha anlamlı olur mu?",
                "Bugün örnek raporu göndereyim, salı günü onboarding metriğiniz üzerinden birlikte değerlendirelim.",
            ],
            "short_summary": self._turkish_summary(
                overall_score, has_discovery, has_price_objection, has_value_response, has_next_step
            ),
        }

    def _english_talk_ratio_feedback(self, salesperson_lines: list[str], transcript: str) -> str:
        total_lines = len([line for line in transcript.splitlines() if line.strip()])
        if total_lines == 0:
            return "Talk ratio cannot be estimated because the transcript is empty."
        rep_ratio = len(salesperson_lines) / total_lines
        if rep_ratio > 0.6:
            return "The salesperson appears to talk more than the customer. Use more discovery questions to create a better listening balance."
        return "The conversation appears reasonably balanced, but real talk ratio requires speaker timing or diarization."

    def _turkish_talk_ratio_feedback(self, salesperson_lines: list[str], transcript: str) -> str:
        total_lines = len([line for line in transcript.splitlines() if line.strip()])
        if total_lines == 0:
            return "Konuşma oranı tahmin edilemiyor çünkü transkript boş."
        rep_ratio = len(salesperson_lines) / total_lines
        if rep_ratio > 0.6:
            return "Satıcı müşteriden daha fazla konuşuyor gibi görünüyor. Daha iyi denge için daha fazla keşif sorusu sormalı."
        return "Konuşma dengesi makul görünüyor, ancak gerçek konuşma oranı için konuşmacı süreleri veya diarization gerekir."

    def _english_top_mistakes(
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
        return self._fill_three(mistakes, backups)

    def _turkish_top_mistakes(
        self, has_discovery: bool, has_price_objection: bool, has_value_response: bool, has_next_step: bool
    ) -> list[str]:
        mistakes: list[str] = []
        if not has_discovery:
            mistakes.append("Satıcı çözümü konumlandırmadan önce yeterli keşif sorusu sormadı.")
        if has_price_objection and not has_value_response:
            mistakes.append("Fiyat endişesi değer, ROI, risk azaltma veya ölçülebilir bir pilot ile ilişkilendirilmedi.")
        if not has_next_step:
            mistakes.append("Görüşme somut bir sonraki adım, sahip, tarih veya başarı kriteri olmadan bitti.")

        backups = [
            "Ürün anlatımı müşterinin ifade ettiği probleme daha doğrudan bağlanmalı.",
            "Satıcı karar sürecine kimlerin dahil olduğunu sormalı.",
            "Kapanışta müşterinin ilerlemek için ne görmesi gerektiği netleştirilmeli.",
        ]
        return self._fill_three(mistakes, backups)

    def _english_summary(
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

    def _turkish_summary(
        self,
        overall_score: int,
        has_discovery: bool,
        has_price_objection: bool,
        has_value_response: bool,
        has_next_step: bool,
    ) -> str:
        if overall_score <= 55:
            return (
                "Bu zayıf bir satış görüşmesi; satıcı yeterli müşteri bağlamı oluşturmuyor, "
                "net bir iş gerekçesi kurmuyor ve somut bir sonraki adım almıyor."
            )
        if has_price_objection and has_value_response and has_next_step and has_discovery:
            return (
                "Bu görüşmede faydalı keşif ve takip unsurları var, ancak satıcı değer önerisini daha somut hale getirmeli."
            )
        return "Bu görüşmede iyi anlar var, ancak rapor keşif, değer anlatımı ve kapanışta net gelişim alanları gösteriyor."

    def _fill_three(self, primary_items: list[str], backups: list[str]) -> list[str]:
        items = list(primary_items)
        for backup in backups:
            if len(items) == 3:
                break
            if backup not in items:
                items.append(backup)
        return items[:3]
