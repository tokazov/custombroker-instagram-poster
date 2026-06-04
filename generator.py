"""Generate Instagram post text via Gemini for Cargo Rapido."""

import os
import json
import re
import time
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)


def _call_gemini_with_retry(prompt: str) -> str:
    """Call Gemini with retry on transient errors."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_KEY", "")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    for attempt in range(5):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            err_str = str(e).lower()
            is_retryable = (
                "429" in str(e) or
                "quota" in err_str or
                "500" in str(e) or
                "503" in str(e) or
                "internal" in err_str
            )
            if is_retryable and attempt < 4:
                wait = 20 * (attempt + 1)
                logger.warning(f"Gemini error (attempt {attempt+1}/5), retrying in {wait}s: {e}")
                time.sleep(wait)
            else:
                raise
    raise Exception("Gemini API failed after 5 retries")


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
{"title": "заголовок для картинки (макс 40 символов, чтобы влез в 1-2 строки)", "subtitle": "подзаголовок или факт (макс 30 символов)", "emoji": "один эмоджи"}
```"""

    raw = _call_gemini_with_retry(prompt)

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
