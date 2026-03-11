"""Topic pool for Cargo Rapido Instagram posts."""

import random

PHOTO_KEYWORDS = {
    "delivery": ["cargo delivery truck", "delivery van road", "package delivery", "freight transport"],
    "warehouse": ["warehouse logistics", "warehouse packages", "storage facility", "cargo warehouse"],
    "georgia": ["tbilisi city", "georgia caucasus", "batumi city", "georgia landscape"],
    "europe": ["europe highway", "european city street", "europe truck road", "europe logistics"],
    "russia": ["moscow city", "russia highway", "cargo train russia", "russian city"],
    "moving": ["moving boxes", "relocation moving", "apartment moving", "furniture moving"],
    "packages": ["cardboard boxes", "package shipping", "parcels delivery", "wrapped packages"],
    "road": ["highway truck", "road transport", "mountain road", "cargo truck highway"],
    "documents": ["shipping documents", "customs paperwork", "business documents", "office paperwork"],
    "happy": ["happy customer delivery", "receiving package", "unboxing delivery", "doorstep delivery"],
}

TOPICS = [
    # МАРШРУТЫ
    {"title_hint": "Доставка из Грузии в Россию за 5-7 дней", "niche": "road", "type": "route",
     "emoji": "🚛", "subtitle": "Тбилиси → Москва", "fact": "от 5 дней"},
    {"title_hint": "Грузоперевозки Грузия — Европа", "niche": "europe", "type": "route",
     "emoji": "🇪🇺", "subtitle": "Германия, Франция, Италия", "fact": "от 7 дней"},
    {"title_hint": "Экспресс доставка Тбилиси — Москва", "niche": "delivery", "type": "route",
     "emoji": "⚡", "subtitle": "Быстрее всех", "fact": "5 дней дверь-дверь"},
    {"title_hint": "Переезд в Грузию под ключ", "niche": "moving", "type": "route",
     "emoji": "📦", "subtitle": "Вещи, мебель, техника", "fact": "Упаковка + доставка"},
    {"title_hint": "Доставка посылок из России в Тбилиси", "niche": "packages", "type": "route",
     "emoji": "📬", "subtitle": "Любой размер и вес", "fact": "от 3 кг"},
    {"title_hint": "Коммерческие грузы Грузия ↔ Европа", "niche": "warehouse", "type": "route",
     "emoji": "🏭", "subtitle": "B2B логистика", "fact": "Таможенное оформление"},

    # СОВЕТЫ
    {"title_hint": "Как правильно упаковать груз для перевозки", "niche": "packages", "type": "tip",
     "emoji": "📋", "points": ["Используйте двойной картон", "Хрупкое — в пузырчатую плёнку", "Заполните пустоты пенопластом", "Маркируйте «Хрупкое» крупно"]},
    {"title_hint": "Какие документы нужны для отправки груза", "niche": "documents", "type": "tip",
     "emoji": "📄", "points": ["Паспорт отправителя", "Опись вложения", "Инвойс для коммерческих грузов", "Мы поможем с оформлением"]},
    {"title_hint": "5 ошибок при международной доставке", "niche": "warehouse", "type": "tip",
     "emoji": "⚠️", "points": ["Неправильная упаковка", "Нет описи содержимого", "Запрещённые товары", "Неточный адрес получателя", "Нет страховки на ценный груз"]},
    {"title_hint": "Что нельзя отправлять международной доставкой", "niche": "packages", "type": "tip",
     "emoji": "🚫", "points": ["Аккумуляторы и литиевые батареи", "Скоропортящиеся продукты", "Оружие и боеприпасы", "Наркотические вещества", "Легковоспламеняющиеся жидкости"]},

    # КЕЙСЫ
    {"title_hint": "Переехали семью из Москвы в Тбилиси за 8 дней", "niche": "moving", "type": "case",
     "emoji": "🏠", "stats": ["45 коробок", "8 дней", "Мебель + техника"]},
    {"title_hint": "Доставили 2 тонны товара из Германии в Тбилиси", "niche": "europe", "type": "case",
     "emoji": "🇩🇪", "stats": ["2 тонны", "10 дней", "Таможня под ключ"]},
    {"title_hint": "300 кг личных вещей Москва → Батуми", "niche": "road", "type": "case",
     "emoji": "📦", "stats": ["300 кг", "6 дней", "Дверь-дверь"]},
    {"title_hint": "Сборный груз из Казахстана в Тбилиси", "niche": "road", "type": "case",
     "emoji": "🇰🇿", "stats": ["800 кг", "12 дней", "СНГ → Грузия"]},

    # ПРЕИМУЩЕСТВА
    {"title_hint": "Почему 4000+ клиентов выбирают Cargo Rapido", "niche": "happy", "type": "promo",
     "emoji": "⭐", "points": ["Работаем с 2015 года", "Доставка дверь-дверь", "Отслеживание 24/7", "Страховка каждого груза"]},
    {"title_hint": "Бесплатная консультация по доставке", "niche": "delivery", "type": "promo",
     "emoji": "📞", "subtitle": "Ответим за 5 минут", "fact": "WhatsApp / Telegram"},

    # СНГ
    {"title_hint": "Доставка из Узбекистана в Грузию", "niche": "road", "type": "route",
     "emoji": "🇺🇿", "subtitle": "Ташкент → Тбилиси", "fact": "от 10 дней"},
    {"title_hint": "Грузоперевозки из Беларуси в Грузию", "niche": "road", "type": "route",
     "emoji": "🇧🇾", "subtitle": "Минск → Тбилиси", "fact": "от 7 дней"},
    {"title_hint": "Из Грузии в любую точку мира", "niche": "delivery", "type": "route",
     "emoji": "🌍", "subtitle": "Экспорт без границ", "fact": "200+ стран"},
    {"title_hint": "Доставка из Армении в Грузию за 2 дня", "niche": "delivery", "type": "route",
     "emoji": "🇦🇲", "subtitle": "Ереван → Тбилиси", "fact": "от 2 дней"},
]


def get_random_topic() -> dict:
    return random.choice(TOPICS)


def get_photo_keyword(niche: str) -> str:
    keywords = PHOTO_KEYWORDS.get(niche, PHOTO_KEYWORDS["delivery"])
    return random.choice(keywords)
