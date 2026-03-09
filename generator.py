"""Generate Instagram post text via Claude for Cargo Rapido."""

import os
import json
import re
import logging
from anthropic import Anthropic

logger = logging.getLogger(__name__)


def generate_post(topic: dict) -> dict:
    """Generate post text + image params."""
    post_type = topic["type"]
    title_hint = topic["title_hint"]

    base_context = """Ты пишешь Instagram пост для Cargo Rapido — компания экспресс доставки грузов.
Направления: Грузия ↔ Россия ↔ Европа (Германия, Франция, Италия, Турция).
Услуги: посылки, коммерческие грузы, переезды, деловая почта.
Офис в Тбилиси. Работают с 2015 года. 4000+ клиентов.
Аудитория: русскоязычные в Грузии и СНГ, экспаты, бизнесмены.
Тон: дружелюбный, профессиональный, без воды."""

    if post_type == "route":
        prompt = f"""{base_context}

Напиши пост про маршрут: {title_hint}
Факт: {topic.get('fact', '')}

Формат:
1. Эмоджи + заголовок
2. Что доставляем на этом маршруте (2-3 предложения)
3. Сроки и условия
4. CTA: "📩 Рассчитать стоимость — ссылка в шапке профиля"
5. Хештеги (5-7 штук)

Длина: 500-800 символов."""

    elif post_type == "tip":
        points = topic.get("points", [])
        prompt = f"""{base_context}

Напиши полезный пост-совет: {title_hint}
Пункты: {', '.join(points)}

Формат:
1. Эмоджи + заголовок (привлекающий внимание)
2. Почему это важно (1-2 предложения)
3. Пронумерованные пункты с пояснениями
4. CTA: "Сохраните этот пост 📌 и отправьте тому, кому пригодится"
5. Хештеги (5-7 штук)

Длина: 600-900 символов."""

    elif post_type == "case":
        stats = topic.get("stats", [])
        prompt = f"""{base_context}

Напиши пост-кейс: {title_hint}
Цифры: {', '.join(stats)}

Формат:
1. Эмоджи + заголовок
2. История (кто, откуда, куда, что отправляли)
3. Результат (сроки, как прошло)
4. CTA: "📩 Нужна доставка? Напишите нам — ссылка в шапке профиля"
5. Хештеги (5-7 штук)

Длина: 500-800 символов. Пиши как реальную историю."""

    else:  # promo
        points = topic.get("points", [])
        prompt = f"""{base_context}

Напиши промо-пост: {title_hint}
Преимущества: {', '.join(points)}

Формат:
1. Эмоджи + заголовок
2. Почему мы (2-3 предложения)
3. Преимущества (список с эмоджи)
4. CTA: "📩 Напишите нам для расчёта — ссылка в шапке профиля"
5. Хештеги (5-7 штук)

Длина: 500-800 символов."""

    prompt += """

Также верни JSON-блок в конце:
```json
{"title": "заголовок для картинки (макс 50 символов)", "subtitle": "подзаголовок или факт (макс 35 символов)", "emoji": "один эмоджи"}
```"""

    client = Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        base_url="https://api.anthropic.com",
    )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text

    json_match = re.search(r'```json\s*({.*?})\s*```', raw, re.DOTALL)
    text = raw
    title = topic["title_hint"]
    subtitle = topic.get("subtitle", "")
    emoji = topic.get("emoji", "🚛")

    if json_match:
        text = raw[:json_match.start()].strip()
        try:
            meta = json.loads(json_match.group(1))
            title = meta.get("title", title)
            subtitle = meta.get("subtitle", subtitle)
            emoji = meta.get("emoji", emoji)
        except json.JSONDecodeError:
            pass

    logger.info(f"Generated: {len(text)} chars, title='{title[:40]}', type={post_type}")

    return {
        "text": text,
        "title": title,
        "subtitle": subtitle,
        "emoji": emoji,
        "niche": topic.get("niche", "delivery"),
        "type": post_type,
        "stats": topic.get("stats"),
        "points": topic.get("points"),
    }
