"""Topic pool for Custom Broker Georgia Instagram posts — weighted distribution + repeat prevention.

Distribution:
  40% — Таможенное оформление / растаможка
  25% — HS-коды / пошлины / расчёты
  20% — СЭЗ Поти/Кутаиси / спецрежимы
  15% — Кейсы клиентов / советы / новости
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
    "customs": [
        "customs office documents",
        "customs clearance paperwork",
        "border control freight",
        "cargo customs inspection",
        "import export documents",
        "customs broker office",
        "freight customs clearance",
        "logistics documents signing",
        "trade compliance documents",
        "customs declaration paperwork",
    ],
    "logistics": [
        "cargo port shipping",
        "container port logistics",
        "freight warehouse loading",
        "logistics truck highway",
        "cargo ship port",
        "shipping containers port",
        "freight transport road",
        "logistics center warehouse",
        "cargo truck transport",
        "container ship freight",
    ],
    "georgia": [
        "Tbilisi Georgia city",
        "Georgia country landscape",
        "Poti port Georgia",
        "Georgia mountains road",
        "Caucasus mountains Georgia",
        "Georgia trade route",
        "Black Sea port Georgia",
        "Kutaisi Georgia city",
        "Georgia business office",
        "Tbilisi modern office",
    ],
    "business": [
        "business handshake office",
        "import export business",
        "trade business meeting",
        "logistics business partner",
        "supply chain management",
        "international trade meeting",
        "business documents office",
        "trade finance documents",
        "export import company",
        "logistics company office",
    ],
}

TOPIC_POOL = [
    # ── Таможенное оформление (40%) ──────────────────────────────
    {"niche": "customs", "type": "guide",
     "title_hint": "Как растаможить товар в Грузии с нуля",
     "weight": 8},
    {"niche": "customs", "type": "guide",
     "title_hint": "Импорт из Китая в Грузию: таможня шаг за шагом",
     "weight": 7},
    {"niche": "customs", "type": "guide",
     "title_hint": "Таможенное оформление авто в Грузии 2025",
     "weight": 8},
    {"niche": "customs", "type": "tip",
     "title_hint": "3 ошибки при растаможке которые стоят денег",
     "weight": 6},
    {"niche": "customs", "type": "guide",
     "title_hint": "Экспорт из Грузии: 0% пошлина и как это работает",
     "weight": 7},
    {"niche": "customs", "type": "guide",
     "title_hint": "Транзит T1 через Грузию: что это и как работает",
     "weight": 6},
    {"niche": "customs", "type": "tip",
     "title_hint": "Документы для импорта в Грузию: полный список",
     "weight": 5},
    {"niche": "customs", "type": "guide",
     "title_hint": "Растаможка из Турции в Грузию: тарифы и сроки",
     "weight": 6},

    # ── HS-коды / пошлины (25%) ──────────────────────────────────
    {"niche": "business", "type": "education",
     "title_hint": "Что такое HS-код и почему он важен для бизнеса",
     "weight": 6},
    {"niche": "business", "type": "education",
     "title_hint": "Как найти правильный HS-код и сэкономить на пошлинах",
     "weight": 5},
    {"niche": "business", "type": "education",
     "title_hint": "Пошлины в Грузии 2025: ставки 0%, 5%, 12%",
     "weight": 6},
    {"niche": "business", "type": "education",
     "title_hint": "НДС при импорте в Грузию: кто платит и сколько",
     "weight": 5},
    {"niche": "business", "type": "education",
     "title_hint": "Акцизы в Грузии: что облагается и какие ставки",
     "weight": 4},

    # ── СЭЗ / спецрежимы (20%) ──────────────────────────────────
    {"niche": "georgia", "type": "education",
     "title_hint": "СЭЗ Поти: 0% налогов и как стать резидентом",
     "weight": 6},
    {"niche": "georgia", "type": "education",
     "title_hint": "Свободная зона Кутаиси: преимущества для бизнеса",
     "weight": 5},
    {"niche": "georgia", "type": "guide",
     "title_hint": "Реэкспорт через Грузию в СНГ: схема и экономия",
     "weight": 6},
    {"niche": "georgia", "type": "education",
     "title_hint": "FTA соглашения Грузии: 0% пошлин в 50 стран",
     "weight": 4},

    # ── Кейсы / советы (15%) ────────────────────────────────────
    {"niche": "logistics", "type": "case",
     "title_hint": "Клиент из России растаможил 20 тонн оборудования за 2 дня",
     "weight": 5},
    {"niche": "customs", "type": "case",
     "title_hint": "Как мы сэкономили клиенту 30% на пошлинах через правильный HS-код",
     "weight": 5},
    {"niche": "business", "type": "tip",
     "title_hint": "Задержали груз на таможне? Вот что делать",
     "weight": 4},
    {"niche": "georgia", "type": "case",
     "title_hint": "Импорт медтехники в Грузию: разрешения и сертификаты",
     "weight": 4},
]


def _load_history() -> list:
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return []


def _save_history(history: list):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history[-MAX_HISTORY:], f)


def get_random_topic() -> dict:
    history = _load_history()
    used_hints = set(history)

    available = [t for t in TOPIC_POOL if t["title_hint"] not in used_hints]
    if not available:
        # Сброс если все использованы
        available = TOPIC_POOL
        history = []

    weights = [t["weight"] for t in available]
    topic = random.choices(available, weights=weights, k=1)[0]

    history.append(topic["title_hint"])
    _save_history(history)

    logger.info(f"📌 [{topic['niche']}] {topic['title_hint']} (history: {len(history)}/{len(TOPIC_POOL)})")
    return topic


def get_photo_keyword(niche: str) -> str:
    keywords = PHOTO_KEYWORDS.get(niche, PHOTO_KEYWORDS["logistics"])
    return random.choice(keywords)
