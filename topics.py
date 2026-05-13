"""Topic pool for Cargo Rapido Instagram posts — weighted distribution + repeat prevention.

Distribution:
  50% — Россия ↔ Грузия
  30% — Европа ↔ Грузия  
  20% — остальные страны + советы/кейсы/промо
"""

import os
import json
import random
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, "post_history.json")
MAX_HISTORY = 30

PHOTO_KEYWORDS = {
    "delivery": [
        "cargo truck highway", "freight truck road", "logistics truck sunset",
        "semi truck highway", "delivery van city", "truck driver road",
        "cargo transport night", "freight highway landscape", "logistics sunset road",
        "truck mountain pass", "cargo truck bridge", "delivery truck city street",
    ],
    "warehouse": [
        "warehouse forklift", "logistics warehouse", "cargo warehouse interior",
        "shipping warehouse", "warehouse workers", "pallet warehouse storage",
        "logistics center aerial", "distribution center", "cargo sorting facility",
        "warehouse shelves", "freight loading dock", "logistics operations",
    ],
    "georgia": [
        "cargo truck mountain road", "caucasus highway truck", "freight transport mountain",
        "truck road mountains", "georgia mountains road", "mountain highway truck",
        "alpine road freight", "scenic mountain highway", "truck winding mountain road",
        "caucasus landscape road", "mountain pass cargo", "high altitude highway",
    ],
    "europe": [
        "european highway truck", "freight truck europe", "logistics europe highway",
        "truck autobahn", "european city logistics", "freight transport bridge",
        "european port cargo", "logistics hub europe", "truck scenic europe",
        "alpine highway truck", "european freight", "truck european countryside",
    ],
    "russia": [
        "freight truck highway winter", "cargo truck road", "logistics truck winter road",
        "semi truck road", "truck snowy highway", "freight winter landscape",
        "cargo truck forest road", "logistics truck sunrise", "truck birch forest road",
        "freight transport plains", "cargo highway russia", "truck long road",
    ],
    "turkey": [
        "truck highway bridge", "freight transport highway", "cargo truck city",
        "logistics highway", "istanbul bridge truck", "bosphorus cargo ship",
        "truck turkey road", "freight mediterranean", "cargo transport port",
        "logistics modern city", "truck highway evening", "freight urban",
    ],
    "moving": [
        "moving truck street", "cargo van moving", "freight van road",
        "moving truck highway", "family moving boxes", "relocation boxes",
        "moving home boxes", "people moving truck", "relocation van city",
        "moving furniture truck", "new home boxes", "relocation service",
    ],
    "packages": [
        "cardboard boxes warehouse", "shipping boxes logistics", "packages freight",
        "boxes cargo", "parcel delivery boxes", "shipping packages",
        "courier boxes", "cargo packages sorted", "parcels warehouse",
        "boxes stacked warehouse", "shipping labels boxes", "freight packages",
    ],
    "road": [
        "semi truck highway", "freight truck road", "cargo truck mountain",
        "truck road transport", "highway sunset truck", "long road truck",
        "truck empty highway", "cargo road journey", "freight transport road",
        "truck aerial highway", "road logistics", "cargo highway aerial",
    ],
    "documents": [
        "logistics clipboard", "freight documents", "shipping invoice",
        "cargo documentation", "customs documents", "logistics paperwork",
        "shipping label close", "freight invoice", "cargo certificate",
        "business logistics documents", "supply chain documents", "shipping contract",
    ],
    "happy": [
        "truck driver delivery", "cargo delivery success", "freight truck success",
        "logistics delivery", "happy delivery driver", "successful shipment",
        "delivery handshake", "logistics team", "freight success business",
        "delivery smile customer", "cargo arrival", "successful logistics",
    ],
    "air": [
        "cargo truck highway international", "freight truck border crossing",
        "logistics truck international route", "semi truck highway sunset",
        "cargo truck long distance", "freight transport international",
        "truck highway europe", "cargo transport modern truck",
        "logistics international highway", "freight truck road journey",
        "modern semi truck road", "cargo delivery truck highway",
    ],
    "sea": [
        "cargo ship container", "container ship port", "freight ship ocean",
        "container vessel port", "container terminal aerial", "port logistics",
        "cargo ship sunset", "container ship loading", "freight port operations",
        "sea freight terminal", "cargo vessel ocean", "port container crane",
    ],
}

# ============================================================
# ГРУППА "russia" — 50% постов
# ============================================================
RUSSIA_TOPICS = [
    # Маршруты
    {"id": "ru-ge-1", "title_hint": "Доставка из России в Грузию за 5-7 дней", "niche": "russia", "type": "route",
     "emoji": "🇷🇺➡️🇬🇪", "subtitle": "Москва → Тбилиси", "fact": "от 5 дней дверь-дверь"},
    {"id": "ge-ru-1", "title_hint": "Доставка из Грузии в Россию", "niche": "russia", "type": "route",
     "emoji": "🇬🇪➡️🇷🇺", "subtitle": "Тбилиси → Москва", "fact": "от 5 дней"},
    {"id": "ru-ge-spb", "title_hint": "Петербург → Тбилиси — доставка грузов", "niche": "russia", "type": "route",
     "emoji": "🇷🇺➡️🇬🇪", "subtitle": "СПб → Тбилиси", "fact": "от 6 дней"},
    {"id": "ru-ge-express", "title_hint": "Экспресс доставка Москва — Тбилиси", "niche": "delivery", "type": "route",
     "emoji": "⚡", "subtitle": "Быстрее всех", "fact": "5 дней дверь-дверь"},
    {"id": "ge-ru-batumi", "title_hint": "Из Батуми в Россию — быстро и надёжно", "niche": "russia", "type": "route",
     "emoji": "🇬🇪➡️🇷🇺", "subtitle": "Батуми → Москва", "fact": "от 6 дней"},
    {"id": "ru-ge-posylki", "title_hint": "Посылки из России в Грузию — любой размер", "niche": "packages", "type": "route",
     "emoji": "📬", "subtitle": "От 3 кг до 20 тонн", "fact": "Любой объём"},
    {"id": "ru-ge-commerce", "title_hint": "Коммерческие грузы Россия → Грузия", "niche": "warehouse", "type": "route",
     "emoji": "🏭", "subtitle": "B2B логистика", "fact": "Таможня под ключ"},
    {"id": "ge-ru-commerce", "title_hint": "Экспорт из Грузии в Россию для бизнеса", "niche": "warehouse", "type": "route",
     "emoji": "📊", "subtitle": "Документы + доставка", "fact": "Полное сопровождение"},

    # Переезды Россия↔Грузия
    {"id": "moving-ru-ge", "title_hint": "Переезд из России в Грузию под ключ", "niche": "moving", "type": "route",
     "emoji": "📦", "subtitle": "Вещи, мебель, техника", "fact": "Упаковка + доставка"},
    {"id": "moving-ge-ru", "title_hint": "Переезд из Грузии в Россию — упакуем всё", "niche": "moving", "type": "route",
     "emoji": "🏠", "subtitle": "Полный сервис", "fact": "Дверь-дверь"},

    # Кейсы Россия↔Грузия
    {"id": "case-msk-tbilisi", "title_hint": "Переехали семью из Москвы в Тбилиси за 8 дней", "niche": "moving", "type": "case",
     "emoji": "🏠", "stats": ["45 коробок", "8 дней", "Мебель + техника"]},
    {"id": "case-msk-batumi", "title_hint": "300 кг личных вещей Москва → Батуми", "niche": "road", "type": "case",
     "emoji": "📦", "stats": ["300 кг", "6 дней", "Дверь-дверь"]},
    {"id": "case-spb-tbilisi", "title_hint": "Переезд из Петербурга в Тбилиси — 60 коробок", "niche": "moving", "type": "case",
     "emoji": "🏗️", "stats": ["60 коробок", "9 дней", "Квартира целиком"]},
    {"id": "case-ru-ge-business", "title_hint": "5 тонн товара из Москвы в Тбилиси", "niche": "warehouse", "type": "case",
     "emoji": "🚛", "stats": ["5 тонн", "7 дней", "Для магазина"]},
]

# ============================================================
# ГРУППА "europe" — 30% постов
# ============================================================
EUROPE_TOPICS = [
    # Маршруты
    {"id": "ge-de", "title_hint": "Грузоперевозки из Грузии в Германию", "niche": "europe", "type": "route",
     "emoji": "🇬🇪➡️🇩🇪", "subtitle": "Тбилиси → Берлин, Мюнхен", "fact": "от 7 дней"},
    {"id": "de-ge", "title_hint": "Доставка из Германии в Грузию", "niche": "europe", "type": "route",
     "emoji": "🇩🇪➡️🇬🇪", "subtitle": "Берлин → Тбилиси", "fact": "от 7 дней"},
    {"id": "ge-fr", "title_hint": "Грузы из Грузии во Францию", "niche": "europe", "type": "route",
     "emoji": "🇬🇪➡️🇫🇷", "subtitle": "Тбилиси → Париж", "fact": "от 8 дней"},
    {"id": "fr-ge", "title_hint": "Доставка из Франции в Грузию", "niche": "europe", "type": "route",
     "emoji": "🇫🇷➡️🇬🇪", "subtitle": "Париж → Тбилиси", "fact": "от 8 дней"},
    {"id": "ge-it", "title_hint": "Доставка из Грузии в Италию", "niche": "europe", "type": "route",
     "emoji": "🇬🇪➡️🇮🇹", "subtitle": "Тбилиси → Рим, Милан", "fact": "от 7 дней"},
    {"id": "it-ge", "title_hint": "Грузоперевозки из Италии в Грузию", "niche": "europe", "type": "route",
     "emoji": "🇮🇹➡️🇬🇪", "subtitle": "Милан → Тбилиси", "fact": "от 7 дней"},
    {"id": "ge-es", "title_hint": "Доставка из Грузии в Испанию", "niche": "europe", "type": "route",
     "emoji": "🇬🇪➡️🇪🇸", "subtitle": "Тбилиси → Мадрид", "fact": "от 8 дней"},
    {"id": "ge-pl", "title_hint": "Грузоперевозки из Грузии в Польшу", "niche": "europe", "type": "route",
     "emoji": "🇬🇪➡️🇵🇱", "subtitle": "Тбилиси → Варшава", "fact": "от 6 дней"},
    {"id": "ge-eu-all", "title_hint": "Грузоперевозки Грузия — вся Европа", "niche": "europe", "type": "route",
     "emoji": "🇪🇺", "subtitle": "Германия, Франция, Италия...", "fact": "от 7 дней"},

    # Кейсы Европа
    {"id": "case-de-ge", "title_hint": "Доставили 2 тонны товара из Германии в Тбилиси", "niche": "europe", "type": "case",
     "emoji": "🇩🇪", "stats": ["2 тонны", "10 дней", "Таможня под ключ"]},
    {"id": "case-it-ge", "title_hint": "Мебель из Италии в Тбилиси — 1.5 тонны", "niche": "europe", "type": "case",
     "emoji": "🇮🇹", "stats": ["1.5 тонны", "9 дней", "Премиум упаковка"]},
]

# ============================================================
# ГРУППА "other" — 20% постов
# ============================================================
OTHER_TOPICS = [
    # Турция
    {"id": "ge-tr", "title_hint": "Доставка из Грузии в Турцию — быстро и надёжно", "niche": "turkey", "type": "route",
     "emoji": "🇬🇪➡️🇹🇷", "subtitle": "Тбилиси → Стамбул", "fact": "от 3 дней"},
    {"id": "tr-ge", "title_hint": "Доставка из Турции в Грузию", "niche": "turkey", "type": "route",
     "emoji": "🇹🇷➡️🇬🇪", "subtitle": "Стамбул → Тбилиси", "fact": "от 3 дней"},

    # СНГ
    {"id": "ge-kz", "title_hint": "Грузоперевозки из Грузии в Казахстан", "niche": "road", "type": "route",
     "emoji": "🇬🇪➡️🇰🇿", "subtitle": "Тбилиси → Алматы", "fact": "от 10 дней"},
    {"id": "by-ge", "title_hint": "Грузоперевозки из Беларуси в Грузию", "niche": "road", "type": "route",
     "emoji": "🇧🇾➡️🇬🇪", "subtitle": "Минск → Тбилиси", "fact": "от 7 дней"},
    {"id": "am-ge", "title_hint": "Доставка из Армении в Грузию за 2 дня", "niche": "delivery", "type": "route",
     "emoji": "🇦🇲➡️🇬🇪", "subtitle": "Ереван → Тбилиси", "fact": "от 2 дней"},
    {"id": "uz-ge", "title_hint": "Доставка из Узбекистана в Грузию", "niche": "road", "type": "route",
     "emoji": "🇺🇿➡️🇬🇪", "subtitle": "Ташкент → Тбилиси", "fact": "от 10 дней"},
    {"id": "az-ge", "title_hint": "Доставка из Азербайджана в Грузию", "niche": "road", "type": "route",
     "emoji": "🇦🇿➡️🇬🇪", "subtitle": "Баку → Тбилиси", "fact": "от 2 дней"},
    {"id": "ge-ua", "title_hint": "Доставка из Грузии в Украину", "niche": "road", "type": "route",
     "emoji": "🇬🇪➡️🇺🇦", "subtitle": "Тбилиси → Киев", "fact": "от 5 дней"},

    # Дальние
    {"id": "cn-ge", "title_hint": "Доставка из Китая в Грузию", "niche": "sea", "type": "route",
     "emoji": "🇨🇳➡️🇬🇪", "subtitle": "Авиа и морем", "fact": "от 15 дней"},
    {"id": "us-ge", "title_hint": "Доставка из США в Грузию", "niche": "sea", "type": "route",
     "emoji": "🇺🇸➡️🇬🇪", "subtitle": "Авиадоставка", "fact": "от 10 дней"},
    {"id": "ge-world", "title_hint": "Из Грузии в любую точку мира", "niche": "delivery", "type": "route",
     "emoji": "🌍", "subtitle": "Экспорт без границ", "fact": "200+ стран"},

    # Кейсы
    {"id": "case-kz-ge", "title_hint": "Сборный груз из Казахстана в Тбилиси", "niche": "road", "type": "case",
     "emoji": "🇰🇿", "stats": ["800 кг", "12 дней", "СНГ → Грузия"]},
    {"id": "case-tr-ge", "title_hint": "Доставили оборудование из Стамбула за 4 дня", "niche": "turkey", "type": "case",
     "emoji": "🇹🇷", "stats": ["500 кг", "4 дня", "Экспресс"]},

    # Советы (полезный контент)
    {"id": "tip-packing", "title_hint": "Как правильно упаковать груз для перевозки", "niche": "packages", "type": "tip",
     "emoji": "📋", "points": ["Используйте двойной картон", "Хрупкое — в пузырчатую плёнку", "Заполните пустоты пенопластом", "Маркируйте «Хрупкое» крупно"]},
    {"id": "tip-docs", "title_hint": "Какие документы нужны для отправки груза", "niche": "documents", "type": "tip",
     "emoji": "📄", "points": ["Паспорт отправителя", "Опись вложения", "Инвойс для коммерческих грузов", "Мы поможем с оформлением"]},
    {"id": "tip-mistakes", "title_hint": "5 ошибок при международной доставке", "niche": "warehouse", "type": "tip",
     "emoji": "⚠️", "points": ["Неправильная упаковка", "Нет описи содержимого", "Запрещённые товары", "Неточный адрес получателя", "Нет страховки на ценный груз"]},
    {"id": "tip-customs", "title_hint": "Таможня без стресса — 5 советов", "niche": "documents", "type": "tip",
     "emoji": "🛃", "points": ["Заранее уточните пошлины", "Полная опись содержимого", "Сохраняйте чеки на товары", "Не превышайте лимиты без декларации", "Доверьте оформление профессионалам"]},
    {"id": "tip-save", "title_hint": "Как сэкономить на международной доставке", "niche": "delivery", "type": "tip",
     "emoji": "💰", "points": ["Сборные грузы дешевле", "Упакуйте компактно", "Планируйте заранее", "Сравните авиа и авто"]},

    # Промо
    {"id": "promo-why", "title_hint": "Почему 4000+ клиентов выбирают Cargo Rapido", "niche": "happy", "type": "promo",
     "emoji": "⭐", "points": ["Работаем с 2015 года", "Доставка дверь-дверь", "Отслеживание 24/7", "Страховка каждого груза"]},
    {"id": "promo-consult", "title_hint": "Бесплатная консультация по доставке", "niche": "delivery", "type": "promo",
     "emoji": "📞", "subtitle": "Ответим за 5 минут", "fact": "WhatsApp / Telegram"},
    {"id": "promo-business", "title_hint": "B2B логистика для вашего бизнеса", "niche": "warehouse", "type": "promo",
     "emoji": "🏭", "points": ["Контракт на регулярные отправки", "Скидки от объёма", "Персональный менеджер", "Полное таможенное сопровождение"]},
    {"id": "promo-georgia", "title_hint": "Грузия — хаб ваших грузов", "niche": "georgia", "type": "promo",
     "emoji": "🇬🇪", "points": ["На перекрёстке Европы и Азии", "Свободная экономическая зона", "Быстрая таможня", "Cargo Rapido — ваш партнёр"]},
]

# Weighted groups: (topics_list, weight)
GROUPS = [
    (RUSSIA_TOPICS, 50),   # 50%
    (EUROPE_TOPICS, 30),   # 30%
    (OTHER_TOPICS, 20),    # 20%
]

# Flat list for fallback
ALL_TOPICS = RUSSIA_TOPICS + EUROPE_TOPICS + OTHER_TOPICS


def _load_history() -> list[str]:
    try:
        with open(HISTORY_FILE, "r") as f:
            data = json.load(f)
            return data.get("used", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_history(used: list[str]):
    used = used[-MAX_HISTORY:]
    with open(HISTORY_FILE, "w") as f:
        json.dump({"used": used, "updated": datetime.utcnow().isoformat()}, f, indent=2)


def get_random_topic() -> dict:
    """Pick topic with weighted group distribution + repeat prevention."""
    used = _load_history()

    # 1. Pick group by weight
    group_lists, weights = zip(*GROUPS)
    available_groups = []
    available_weights = []

    for topics, weight in GROUPS:
        remaining = [t for t in topics if t["id"] not in used]
        if remaining:
            available_groups.append(remaining)
            available_weights.append(weight)

    # If all groups exhausted, reset (keep last 5)
    if not available_groups:
        logger.info("♻️ All topics used, resetting history")
        used = used[-5:]
        for topics, weight in GROUPS:
            remaining = [t for t in topics if t["id"] not in used]
            if remaining:
                available_groups.append(remaining)
                available_weights.append(weight)
        if not available_groups:
            available_groups = [ALL_TOPICS]
            available_weights = [1]

    # 2. Weighted random group selection
    chosen_group = random.choices(available_groups, weights=available_weights, k=1)[0]

    # 3. Random topic from chosen group
    topic = random.choice(chosen_group)

    # 4. Save
    used.append(topic["id"])
    _save_history(used)

    group_name = "russia" if chosen_group[0] in RUSSIA_TOPICS or topic in RUSSIA_TOPICS else \
                 "europe" if chosen_group[0] in EUROPE_TOPICS or topic in EUROPE_TOPICS else "other"
    logger.info(f"📌 [{group_name}] {topic['id']} (history: {len(used)}/{len(ALL_TOPICS)})")
    return topic


def get_photo_keyword(niche: str) -> str:
    keywords = PHOTO_KEYWORDS.get(niche, PHOTO_KEYWORDS["delivery"])
    return random.choice(keywords)
