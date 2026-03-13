"""Topic pool for Cargo Rapido Instagram posts — with repeat prevention."""

import os
import json
import random
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, "post_history.json")
MAX_HISTORY = 30  # помнить последние 30 постов

PHOTO_KEYWORDS = {
    "delivery": ["cargo delivery truck", "delivery van road", "package delivery", "freight transport"],
    "warehouse": ["warehouse logistics", "warehouse packages", "storage facility", "cargo warehouse"],
    "georgia": ["tbilisi city", "georgia caucasus", "batumi city", "georgia landscape"],
    "europe": ["europe highway", "european city street", "europe truck road", "europe logistics"],
    "russia": ["moscow city", "russia highway", "cargo train russia", "russian city"],
    "turkey": ["istanbul bosphorus", "turkey truck highway", "turkish logistics", "istanbul cargo"],
    "moving": ["moving boxes", "relocation moving", "apartment moving", "furniture moving"],
    "packages": ["cardboard boxes", "package shipping", "parcels delivery", "wrapped packages"],
    "road": ["highway truck", "road transport", "mountain road", "cargo truck highway"],
    "documents": ["shipping documents", "customs paperwork", "business documents", "office paperwork"],
    "happy": ["happy customer delivery", "receiving package", "unboxing delivery", "doorstep delivery"],
    "air": ["cargo airplane", "air freight", "airport cargo", "air logistics"],
    "sea": ["cargo ship port", "container ship", "sea freight", "port logistics"],
}

TOPICS = [
    # === МАРШРУТЫ ИЗ ГРУЗИИ ===
    {"id": "ge-ru", "title_hint": "Доставка из Грузии в Россию за 5-7 дней", "niche": "road", "type": "route",
     "emoji": "🇬🇪➡️🇷🇺", "subtitle": "Тбилиси → Москва", "fact": "от 5 дней"},
    {"id": "ge-de", "title_hint": "Грузоперевозки из Грузии в Германию", "niche": "europe", "type": "route",
     "emoji": "🇬🇪➡️🇩🇪", "subtitle": "Тбилиси → Берлин, Мюнхен", "fact": "от 7 дней"},
    {"id": "ge-tr", "title_hint": "Доставка из Грузии в Турцию — быстро и надёжно", "niche": "turkey", "type": "route",
     "emoji": "🇬🇪➡️🇹🇷", "subtitle": "Тбилиси → Стамбул", "fact": "от 3 дней"},
    {"id": "ge-fr", "title_hint": "Грузы из Грузии во Францию", "niche": "europe", "type": "route",
     "emoji": "🇬🇪➡️🇫🇷", "subtitle": "Тбилиси → Париж", "fact": "от 8 дней"},
    {"id": "ge-it", "title_hint": "Доставка из Грузии в Италию", "niche": "europe", "type": "route",
     "emoji": "🇬🇪➡️🇮🇹", "subtitle": "Тбилиси → Рим, Милан", "fact": "от 7 дней"},
    {"id": "ge-kz", "title_hint": "Грузоперевозки из Грузии в Казахстан", "niche": "road", "type": "route",
     "emoji": "🇬🇪➡️🇰🇿", "subtitle": "Тбилиси → Алматы", "fact": "от 10 дней"},
    {"id": "ge-world", "title_hint": "Из Грузии в любую точку мира", "niche": "delivery", "type": "route",
     "emoji": "🌍", "subtitle": "Экспорт без границ", "fact": "200+ стран"},
    {"id": "ge-es", "title_hint": "Доставка из Грузии в Испанию", "niche": "europe", "type": "route",
     "emoji": "🇬🇪➡️🇪🇸", "subtitle": "Тбилиси → Мадрид, Барселона", "fact": "от 8 дней"},
    {"id": "ge-pl", "title_hint": "Грузоперевозки из Грузии в Польшу", "niche": "europe", "type": "route",
     "emoji": "🇬🇪➡️🇵🇱", "subtitle": "Тбилиси → Варшава", "fact": "от 6 дней"},
    {"id": "ge-ua", "title_hint": "Доставка из Грузии в Украину", "niche": "road", "type": "route",
     "emoji": "🇬🇪➡️🇺🇦", "subtitle": "Тбилиси → Киев", "fact": "от 5 дней"},

    # === МАРШРУТЫ В ГРУЗИЮ ===
    {"id": "ru-ge", "title_hint": "Доставка из России в Грузию", "niche": "road", "type": "route",
     "emoji": "🇷🇺➡️🇬🇪", "subtitle": "Москва → Тбилиси", "fact": "от 5 дней дверь-дверь"},
    {"id": "de-ge", "title_hint": "Грузы из Германии в Грузию", "niche": "europe", "type": "route",
     "emoji": "🇩🇪➡️🇬🇪", "subtitle": "Берлин → Тбилиси", "fact": "от 7 дней"},
    {"id": "tr-ge", "title_hint": "Доставка из Турции в Грузию", "niche": "turkey", "type": "route",
     "emoji": "🇹🇷➡️🇬🇪", "subtitle": "Стамбул → Тбилиси", "fact": "от 3 дней"},
    {"id": "fr-ge", "title_hint": "Доставка из Франции в Грузию", "niche": "europe", "type": "route",
     "emoji": "🇫🇷➡️🇬🇪", "subtitle": "Париж → Тбилиси", "fact": "от 8 дней"},
    {"id": "it-ge", "title_hint": "Грузоперевозки из Италии в Грузию", "niche": "europe", "type": "route",
     "emoji": "🇮🇹➡️🇬🇪", "subtitle": "Милан → Тбилиси", "fact": "от 7 дней"},
    {"id": "by-ge", "title_hint": "Грузоперевозки из Беларуси в Грузию", "niche": "road", "type": "route",
     "emoji": "🇧🇾➡️🇬🇪", "subtitle": "Минск → Тбилиси", "fact": "от 7 дней"},
    {"id": "am-ge", "title_hint": "Доставка из Армении в Грузию за 2 дня", "niche": "delivery", "type": "route",
     "emoji": "🇦🇲➡️🇬🇪", "subtitle": "Ереван → Тбилиси", "fact": "от 2 дней"},
    {"id": "uz-ge", "title_hint": "Доставка из Узбекистана в Грузию", "niche": "road", "type": "route",
     "emoji": "🇺🇿➡️🇬🇪", "subtitle": "Ташкент → Тбилиси", "fact": "от 10 дней"},
    {"id": "az-ge", "title_hint": "Доставка из Азербайджана в Грузию", "niche": "road", "type": "route",
     "emoji": "🇦🇿➡️🇬🇪", "subtitle": "Баку → Тбилиси", "fact": "от 2 дней"},
    {"id": "cn-ge", "title_hint": "Доставка из Китая в Грузию", "niche": "sea", "type": "route",
     "emoji": "🇨🇳➡️🇬🇪", "subtitle": "Авиа и морем", "fact": "от 15 дней"},
    {"id": "us-ge", "title_hint": "Доставка из США в Грузию", "niche": "air", "type": "route",
     "emoji": "🇺🇸➡️🇬🇪", "subtitle": "Авиадоставка", "fact": "от 10 дней"},

    # === ЭКСПРЕСС ===
    {"id": "express-tbilisi-msk", "title_hint": "Экспресс доставка Тбилиси — Москва", "niche": "delivery", "type": "route",
     "emoji": "⚡", "subtitle": "Быстрее всех", "fact": "5 дней дверь-дверь"},

    # === ПЕРЕЕЗД ===
    {"id": "moving-to-ge", "title_hint": "Переезд в Грузию под ключ", "niche": "moving", "type": "route",
     "emoji": "📦", "subtitle": "Вещи, мебель, техника", "fact": "Упаковка + доставка"},
    {"id": "moving-from-ge", "title_hint": "Переезд из Грузии — упакуем и доставим", "niche": "moving", "type": "route",
     "emoji": "🏠", "subtitle": "В любую страну", "fact": "Полный сервис"},

    # === СОВЕТЫ ===
    {"id": "tip-packing", "title_hint": "Как правильно упаковать груз для перевозки", "niche": "packages", "type": "tip",
     "emoji": "📋", "points": ["Используйте двойной картон", "Хрупкое — в пузырчатую плёнку", "Заполните пустоты пенопластом", "Маркируйте «Хрупкое» крупно"]},
    {"id": "tip-docs", "title_hint": "Какие документы нужны для отправки груза", "niche": "documents", "type": "tip",
     "emoji": "📄", "points": ["Паспорт отправителя", "Опись вложения", "Инвойс для коммерческих грузов", "Мы поможем с оформлением"]},
    {"id": "tip-mistakes", "title_hint": "5 ошибок при международной доставке", "niche": "warehouse", "type": "tip",
     "emoji": "⚠️", "points": ["Неправильная упаковка", "Нет описи содержимого", "Запрещённые товары", "Неточный адрес получателя", "Нет страховки на ценный груз"]},
    {"id": "tip-banned", "title_hint": "Что нельзя отправлять международной доставкой", "niche": "packages", "type": "tip",
     "emoji": "🚫", "points": ["Аккумуляторы и литиевые батареи", "Скоропортящиеся продукты", "Оружие и боеприпасы", "Наркотические вещества", "Легковоспламеняющиеся жидкости"]},
    {"id": "tip-customs", "title_hint": "Таможня без стресса — 5 советов", "niche": "documents", "type": "tip",
     "emoji": "🛃", "points": ["Заранее уточните пошлины", "Полная опись содержимого", "Сохраняйте чеки на товары", "Не превышайте лимиты без декларации", "Доверьте оформление профессионалам"]},
    {"id": "tip-save", "title_hint": "Как сэкономить на международной доставке", "niche": "delivery", "type": "tip",
     "emoji": "💰", "points": ["Сборные грузы дешевле", "Упакуйте компактно", "Планируйте заранее — без срочности", "Сравните авиа и авто"]},

    # === КЕЙСЫ ===
    {"id": "case-msk-tbilisi", "title_hint": "Переехали семью из Москвы в Тбилиси за 8 дней", "niche": "moving", "type": "case",
     "emoji": "🏠", "stats": ["45 коробок", "8 дней", "Мебель + техника"]},
    {"id": "case-de-ge", "title_hint": "Доставили 2 тонны товара из Германии в Тбилиси", "niche": "europe", "type": "case",
     "emoji": "🇩🇪", "stats": ["2 тонны", "10 дней", "Таможня под ключ"]},
    {"id": "case-msk-batumi", "title_hint": "300 кг личных вещей Москва → Батуми", "niche": "road", "type": "case",
     "emoji": "📦", "stats": ["300 кг", "6 дней", "Дверь-дверь"]},
    {"id": "case-kz-ge", "title_hint": "Сборный груз из Казахстана в Тбилиси", "niche": "road", "type": "case",
     "emoji": "🇰🇿", "stats": ["800 кг", "12 дней", "СНГ → Грузия"]},
    {"id": "case-tr-ge", "title_hint": "Доставили оборудование из Стамбула за 4 дня", "niche": "turkey", "type": "case",
     "emoji": "🇹🇷", "stats": ["500 кг", "4 дня", "Экспресс"]},
    {"id": "case-it-ge", "title_hint": "Мебель из Италии в Тбилиси — 1.5 тонны", "niche": "europe", "type": "case",
     "emoji": "🇮🇹", "stats": ["1.5 тонны", "9 дней", "Премиум упаковка"]},

    # === ПРОМО ===
    {"id": "promo-why", "title_hint": "Почему 4000+ клиентов выбирают Cargo Rapido", "niche": "happy", "type": "promo",
     "emoji": "⭐", "points": ["Работаем с 2015 года", "Доставка дверь-дверь", "Отслеживание 24/7", "Страховка каждого груза"]},
    {"id": "promo-consult", "title_hint": "Бесплатная консультация по доставке", "niche": "delivery", "type": "promo",
     "emoji": "📞", "subtitle": "Ответим за 5 минут", "fact": "WhatsApp / Telegram"},
    {"id": "promo-business", "title_hint": "B2B логистика для вашего бизнеса", "niche": "warehouse", "type": "promo",
     "emoji": "🏭", "points": ["Контракт на регулярные отправки", "Скидки от объёма", "Персональный менеджер", "Полное таможенное сопровождение"]},
    {"id": "promo-georgia", "title_hint": "Грузия — хаб ваших грузов", "niche": "georgia", "type": "promo",
     "emoji": "🇬🇪", "points": ["На перекрёстке Европы и Азии", "Свободная экономическая зона", "Быстрая таможня", "Cargo Rapido — ваш партнёр"]},
]


def _load_history() -> list[str]:
    """Load list of recently used topic IDs."""
    try:
        with open(HISTORY_FILE, "r") as f:
            data = json.load(f)
            return data.get("used", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_history(used: list[str]):
    """Save used topic IDs, keep last MAX_HISTORY."""
    used = used[-MAX_HISTORY:]
    with open(HISTORY_FILE, "w") as f:
        json.dump({"used": used, "updated": datetime.utcnow().isoformat()}, f, indent=2)


def get_random_topic() -> dict:
    """Pick a random topic, avoiding recent repeats."""
    used = _load_history()

    # Filter out recently used
    available = [t for t in TOPICS if t.get("id", t["title_hint"]) not in used]

    # If all used up, reset history but avoid last 5
    if not available:
        logger.info("♻️ All topics used, resetting history (keeping last 5)")
        used = used[-5:]
        available = [t for t in TOPICS if t.get("id", t["title_hint"]) not in used]
        if not available:
            available = TOPICS  # fallback

    topic = random.choice(available)

    # Save to history
    topic_id = topic.get("id", topic["title_hint"])
    used.append(topic_id)
    _save_history(used)

    logger.info(f"📌 Selected topic: {topic_id} (history: {len(used)}/{len(TOPICS)})")
    return topic


def get_photo_keyword(niche: str) -> str:
    keywords = PHOTO_KEYWORDS.get(niche, PHOTO_KEYWORDS["delivery"])
    return random.choice(keywords)
