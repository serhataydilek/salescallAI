from dataclasses import dataclass
from typing import Protocol

from app.services.analysis.calibration import detect_critical_failures, detect_sales_quality_signals


class AnalysisLike(Protocol):
    overall_score: int
    discovery_score: int
    objection_handling_score: int
    closing_score: int
    follow_up_score: int
    top_3_mistakes: list[str]
    missed_questions: list[str]
    suggested_improvements: list[str]
    better_example_responses: list[str]
    short_summary: str


@dataclass(frozen=True)
class AssistantCoachingCard:
    issue: str
    why_it_matters: str
    try_saying_this: str


TURKISH_MARKERS = [
    "musteri",
    "müşteri",
    "satici",
    "satıcı",
    "gorusme",
    "görüşme",
    "fiyat",
    "itiraz",
    "deger",
    "değer",
    "sonraki",
    "takip",
    "tekrar aramay",
]


def build_assistant_coaching_cards(
    analysis: AnalysisLike,
    transcript: str | None = None,
    *,
    max_cards: int = 5,
) -> list[AssistantCoachingCard]:
    text = _combined_text(analysis, transcript)
    is_turkish = _is_turkish(text)
    critical = detect_critical_failures(transcript or text)
    quality = detect_sales_quality_signals(transcript or text)

    if critical.is_catastrophic or analysis.overall_score <= 25:
        cards = _turkish_catastrophic_cards(critical) if is_turkish else _english_catastrophic_cards(critical)
    elif quality.is_feature_dump or _contains_any(text, ["feature dumping", "feature-led", "product features"]):
        cards = _turkish_feature_dump_cards() if is_turkish else _english_feature_dump_cards()
    elif quality.is_weak_price_objection or _contains_any(text, ["price handling is vague", "roi/value", "price objection"]):
        cards = _turkish_price_cards() if is_turkish else _english_price_cards()
    elif analysis.overall_score >= 80:
        cards = _turkish_strong_cards() if is_turkish else _english_strong_cards()
    else:
        cards = _turkish_general_cards() if is_turkish else _english_general_cards()

    return _dedupe_cards(cards)[:max(3, min(max_cards, 5))]


def _combined_text(analysis: AnalysisLike, transcript: str | None) -> str:
    parts = [
        transcript or "",
        analysis.short_summary,
        *analysis.top_3_mistakes,
        *analysis.missed_questions,
        *analysis.suggested_improvements,
        *analysis.better_example_responses,
    ]
    return " ".join(parts).lower()


def _is_turkish(text: str) -> bool:
    return any(marker in text for marker in TURKISH_MARKERS)


def _contains_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)


def _dedupe_cards(cards: list[AssistantCoachingCard]) -> list[AssistantCoachingCard]:
    unique: list[AssistantCoachingCard] = []
    seen = set()
    for card in cards:
        key = (card.issue.strip().lower(), card.try_saying_this.strip().lower())
        if key not in seen:
            unique.append(card)
            seen.add(key)
    return unique


def _english_strong_cards() -> list[AssistantCoachingCard]:
    return [
        AssistantCoachingCard(
            issue="The close is already solid; make the decision path a little clearer.",
            why_it_matters="A strong next step is easier to protect when the buyer confirms who else needs to weigh in.",
            try_saying_this=(
                "This sounds worth exploring. Before we meet Tuesday, who else should review the sample report "
                "so the pilot decision is clean?"
            ),
        ),
        AssistantCoachingCard(
            issue="The pilot value could be anchored to a baseline metric.",
            why_it_matters="Even good calls become more persuasive when success is measured against the customer's current state.",
            try_saying_this=(
                "If your current follow-up quality is uneven, let's use that as the baseline and compare the next 10 calls "
                "against it during the pilot."
            ),
        ),
        AssistantCoachingCard(
            issue="The follow-up email can restate the success criteria.",
            why_it_matters="A short recap reduces drift between the call and the next meeting.",
            try_saying_this=(
                "I'll send the sample report today and recap the metric we agreed to test: better discovery notes "
                "and cleaner follow-up after each call."
            ),
        ),
    ]


def _english_feature_dump_cards() -> list[AssistantCoachingCard]:
    return [
        AssistantCoachingCard(
            issue="The pitch moves into features before enough discovery.",
            why_it_matters="Buyers listen more closely when the product is tied to a problem they just described.",
            try_saying_this=(
                "Before I show features, can you walk me through what happens after a rep finishes a sales call today?"
            ),
        ),
        AssistantCoachingCard(
            issue="The product value needs a direct link to the customer's pain.",
            why_it_matters="Listing dashboards and exports can sound generic unless each feature solves a specific workflow problem.",
            try_saying_this=(
                "If managers are spending too much time finding coaching moments, the report can highlight missed questions "
                "and follow-up gaps right after the call."
            ),
        ),
        AssistantCoachingCard(
            issue="Success metrics stay too vague.",
            why_it_matters="A trial is easier to approve when the buyer knows what improvement they are testing.",
            try_saying_this=(
                "For a pilot, should we measure better discovery notes, faster manager review time, or cleaner follow-up completion?"
            ),
        ),
    ]


def _english_price_cards() -> list[AssistantCoachingCard]:
    return [
        AssistantCoachingCard(
            issue="The price objection gets a vague answer.",
            why_it_matters="The customer needs to see what the investment could return; reassurance alone does not build confidence.",
            try_saying_this=(
                "I understand the price concern. Let's start with a low-risk 10-call pilot and measure whether ramp time "
                "or follow-up quality improves before you commit further."
            ),
        ),
        AssistantCoachingCard(
            issue="The response should connect cost to ROI or value.",
            why_it_matters="Price feels more reasonable when it is tied to a measurable business outcome.",
            try_saying_this=(
                "If the pilot shows managers can spot coaching gaps faster and reps improve follow-up quality, "
                "would that make the investment easier to justify?"
            ),
        ),
        AssistantCoachingCard(
            issue="The next step needs a clear success metric.",
            why_it_matters="A concrete metric turns the objection into a practical evaluation instead of a loose follow-up.",
            try_saying_this=(
                "For the next step, let's agree on one success metric now, then review the sample report together next Tuesday."
            ),
        ),
    ]


def _english_catastrophic_cards(critical) -> list[AssistantCoachingCard]:
    cards = [
        AssistantCoachingCard(
            issue="The customer set a clear boundary.",
            why_it_matters="Continuing after a do-not-contact request damages trust and creates avoidable risk.",
            try_saying_this="I understand. I will not contact you again. Thank you for your time.",
        ),
        AssistantCoachingCard(
            issue="The call needs better preparation before outreach.",
            why_it_matters="A rep must be able to explain the product, pricing path, and buyer relevance without guessing.",
            try_saying_this=(
                "Before I called, I noted that your team handles sales coaching. The reason for my call is to see "
                "whether missed follow-ups are costing manager time."
            ),
        ),
        AssistantCoachingCard(
            issue="Quota pressure should stay out of the buyer conversation.",
            why_it_matters="Customers should not feel responsible for the seller's internal targets.",
            try_saying_this="No replacement sentence needed here; remove quota pressure from the call entirely.",
        ),
    ]
    if getattr(critical, "referral_after_rejection", False):
        cards.append(
            AssistantCoachingCard(
                issue="Do not ask for referrals after rejection.",
                why_it_matters="A referral ask after a boundary refusal makes the call feel pushy and disrespectful.",
                try_saying_this="I understand. I will update our notes and close this out. Have a good day.",
            )
        )
    return cards


def _english_general_cards() -> list[AssistantCoachingCard]:
    return [
        AssistantCoachingCard(
            issue="Discovery can go one layer deeper before pitching.",
            why_it_matters="The recommendation becomes more useful when it is tied to the customer's current workflow.",
            try_saying_this="What happens today after a sales call ends, and where does the follow-up usually break down?",
        ),
        AssistantCoachingCard(
            issue="The value statement should be more specific.",
            why_it_matters="Specific outcomes are easier for the buyer to repeat internally.",
            try_saying_this=(
                "The main value here is not another dashboard; it is helping managers spot missed questions and coach reps faster."
            ),
        ),
        AssistantCoachingCard(
            issue="The close needs owner, date, and success criteria.",
            why_it_matters="A clear next step makes the call actionable instead of informational.",
            try_saying_this=(
                "I can send the sample report today. Could we review it Tuesday and decide whether a 10-call pilot is useful?"
            ),
        ),
    ]


def _turkish_strong_cards() -> list[AssistantCoachingCard]:
    return [
        AssistantCoachingCard(
            issue="Kapanış zaten iyi; karar sürecini biraz daha netleştirebilirsin.",
            why_it_matters="Güçlü bir sonraki adım, karara kimlerin dahil olduğunu bildiğinde daha kolay ilerler.",
            try_saying_this=(
                "Salı günü örnek raporu incelerken pilot kararına kimlerin dahil olması gerekir?"
            ),
        ),
        AssistantCoachingCard(
            issue="Pilot değeri mevcut metrikle biraz daha net bağlanabilir.",
            why_it_matters="İyi görüşmeler bile başarı ölçütü mevcut durumla karşılaştırıldığında daha ikna edici olur.",
            try_saying_this=(
                "Mevcut follow-up kalitesini başlangıç noktası alalım ve pilotta sonraki 10 çağrıda bunun iyileşip iyileşmediğini ölçelim."
            ),
        ),
        AssistantCoachingCard(
            issue="Takip mesajında başarı kriterini tekrar et.",
            why_it_matters="Kısa bir özet, görüşme ile sonraki toplantı arasında odağı korur.",
            try_saying_this=(
                "Bugün örnek raporu göndereceğim; salı günü discovery notları ve follow-up kalitesi metriği üzerinden birlikte değerlendirelim."
            ),
        ),
    ]


def _turkish_feature_dump_cards() -> list[AssistantCoachingCard]:
    return [
        AssistantCoachingCard(
            issue="Yeterli keşif yapmadan özellik anlatımına geçiliyor.",
            why_it_matters="Müşteri, ürün kendi anlattığı probleme bağlandığında daha dikkatli dinler.",
            try_saying_this=(
                "Özellikleri anlatmadan önce, bir satış görüşmesi bittikten sonra ekibinizde ne olduğunu adım adım anlatır mısınız?"
            ),
        ),
        AssistantCoachingCard(
            issue="Ürün değeri müşteri problemiyle daha doğrudan bağlanmalı.",
            why_it_matters="Dashboard ve export listelemek, belirli bir iş akışı sorununu çözmediğinde genel kalır.",
            try_saying_this=(
                "Eğer yöneticiler koçluk anlarını bulmakta zaman kaybediyorsa, rapor kaçan soruları ve follow-up boşluklarını çağrıdan hemen sonra gösterebilir."
            ),
        ),
        AssistantCoachingCard(
            issue="Başarı metriği çok belirsiz kalıyor.",
            why_it_matters="Pilot, müşteri hangi gelişimi test edeceğini bildiğinde daha kolay onaylanır.",
            try_saying_this=(
                "Pilot için daha iyi discovery notlarını mı, daha hızlı yönetici incelemesini mi, yoksa follow-up tamamlanma oranını mı ölçelim?"
            ),
        ),
    ]


def _turkish_price_cards() -> list[AssistantCoachingCard]:
    return [
        AssistantCoachingCard(
            issue="Fiyat itirazına verilen cevap çok genel kalıyor.",
            why_it_matters="Müşteri yatırımın karşılığını görmek ister; sadece güvence vermek yeterli olmaz.",
            try_saying_this=(
                "Fiyat endişenizi anlıyorum. Önce 10 çağrılık düşük riskli bir pilotla değeri ölçelim; "
                "ramp süresi veya follow-up kalitesi artmazsa devam etmeyiz."
            ),
        ),
        AssistantCoachingCard(
            issue="Maliyet ROI veya değerle bağlanmalı.",
            why_it_matters="Fiyat, ölçülebilir bir iş sonucuna bağlandığında daha anlamlı görünür.",
            try_saying_this=(
                "Pilot yöneticilerin koçluk boşluklarını daha hızlı bulduğunu ve temsilcilerin follow-up kalitesini artırdığını gösterirse yatırım daha anlamlı olur mu?"
            ),
        ),
        AssistantCoachingCard(
            issue="Sonraki adım için net başarı metriği gerekiyor.",
            why_it_matters="Somut metrik, itirazı belirsiz takip yerine pratik bir değerlendirmeye çevirir.",
            try_saying_this=(
                "Sonraki adım olarak bir başarı metriği seçelim, sonra örnek raporu salı günü birlikte değerlendirelim."
            ),
        ),
    ]


def _turkish_catastrophic_cards(critical) -> list[AssistantCoachingCard]:
    cards = [
        AssistantCoachingCard(
            issue="Müşteri net bir sınır koyuyor.",
            why_it_matters="Tekrar aramama isteğinden sonra devam etmek güveni zedeler ve gereksiz risk yaratır.",
            try_saying_this="Anlıyorum. Sizi tekrar aramayacağım. Zamanınız için teşekkür ederim.",
        ),
        AssistantCoachingCard(
            issue="Arama öncesi hazırlık güçlendirilmeli.",
            why_it_matters="Satıcı ürünü, fiyat yolunu ve müşteriyle ilgisini tahmin ederek değil net şekilde anlatabilmeli.",
            try_saying_this=(
                "Aramadan önce ekibinizin satış koçluğu sürecine baktım. Görüşme sebebim, kaçan follow-up'ların yönetici zamanını etkileyip etkilemediğini anlamak."
            ),
        ),
        AssistantCoachingCard(
            issue="Kota baskısı müşteri görüşmesine taşınmamalı.",
            why_it_matters="Müşteri, satıcının iç hedeflerinden sorumlu hissetmemeli.",
            try_saying_this="Burada alternatif cümleye gerek yok; kota baskısını görüşmeden tamamen çıkar.",
        ),
    ]
    if getattr(critical, "referral_after_rejection", False):
        cards.append(
            AssistantCoachingCard(
                issue="Reddedildikten sonra referans isteme.",
                why_it_matters="Sınır koyulduktan sonra referans istemek görüşmeyi ısrarcı ve saygısız hissettirir.",
                try_saying_this="Anlıyorum. Notlarımızı güncelleyeceğim ve sizi tekrar rahatsız etmeyeceğim. İyi günler.",
            )
        )
    return cards


def _turkish_general_cards() -> list[AssistantCoachingCard]:
    return [
        AssistantCoachingCard(
            issue="Çözüm anlatmadan önce keşif bir kat daha derinleşebilir.",
            why_it_matters="Öneri, müşterinin mevcut iş akışına bağlandığında daha faydalı olur.",
            try_saying_this="Bugün bir satış görüşmesi bittikten sonra ne oluyor ve follow-up genelde nerede aksıyor?",
        ),
        AssistantCoachingCard(
            issue="Değer cümlesi daha somut olabilir.",
            why_it_matters="Somut sonuçlar müşterinin içeride anlatmasını kolaylaştırır.",
            try_saying_this=(
                "Buradaki ana değer yeni bir dashboard değil; yöneticilerin kaçan soruları görüp temsilcilere daha hızlı koçluk yapması."
            ),
        ),
        AssistantCoachingCard(
            issue="Kapanışta sahip, tarih ve başarı kriteri netleşmeli.",
            why_it_matters="Net sonraki adım, görüşmeyi sadece bilgilendirici olmaktan çıkarıp aksiyona çevirir.",
            try_saying_this=(
                "Bugün örnek raporu gönderebilirim. Salı günü birlikte inceleyip 10 çağrılık pilotun faydalı olup olmadığına karar verelim mi?"
            ),
        ),
    ]
