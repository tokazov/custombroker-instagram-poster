"""Generate Instagram post text via Claude for Custom Broker Georgia."""

import os
import json
import re
import time
import logging
from anthropic import Anthropic

logger = logging.getLogger(__name__)


def _call_claude_with_retry(client, **kwargs):
    """Call Claude with retry on overload or server errors."""
    for attempt in range(5):
        try:
            return client.messages.create(**kwargs)
        except Exception as e:
            err_str = str(e).lower()
            is_retryable = (
                "529" in str(e) or
                "overloaded" in err_str or
                "500" in str(e) or
                "internal server error" in err_str
            )
            if is_retryable and attempt < 4:
                wait = 30 * (attempt + 1)
                logger.warning(f"Claude error (attempt {attempt+1}/5), retrying in {wait}s: {e}")
                time.sleep(wait)
            else:
                raise
    raise Exception("Anthropic API failed after 5 retries")


def generate_post(topic: dict) -> dict:
    """Generate post text + image params."""
    post_type = topic["type"]
    title_hint = topic["title_hint"]

    base_context = """Ты пишешь Instagram пост для Custom Broker Georgia — таможенный брокер в Тбилиси.
Услуги: растаможка, сертификация, HS-коды, СЭЗ Поти/Кутаиси, транзит T1, споры с таможней.
Работаем с 2018 года. 1200+ грузов оформлено. AI-консультант Ана 24/7.
Сайт: custombroker.ge
Аудитория: импортёры из России, Китая, Турции, Европы; реэкспортёры в СНГ; бизнес в СЭЗ.
Тон: профессиональный, экспертный, конкретный. Без воды. Даём реальную пользу."""

    if post_type in ("guide", "education"):
        prompt = f"""{base_context}

Напиши экспертный пост-руководство: {title_hint}

Формат:
1. Эмоджи + цепляющий заголовок
2. Вступление — почему это важно (1-2 предложения)
3. Полезный контент: конкретные факты, цифры, шаги (3-5 пунктов)
4. CTA: "📩 Нужна помощь с таможней? Пишите — ссылка в профиле" или "Спросите Ану 24/7 на custombroker.ge"
5. Хештеги (6-8 штук: #таможняГрузия #растаможка #импорт #экспорт #таможенныйброкер #Тбилиси и др.)

Длина: 600-900 символов. Конкретика, цифры, реальная польза."""

    elif post_type == "tip":
        prompt = f"""{base_context}

Напиши полезный пост-совет: {title_hint}

Формат:
1. Эмоджи + заголовок (провокационный или с цифрой)
2. Почему это важно (1-2 предложения)
3. Конкретные советы/пункты с пояснениями
4. CTA: "Сохрани этот пост 📌 — пригодится при следующей растаможке"
5. Хештеги (6-8 штук)

Длина: 500-800 символов."""

    elif post_type == "case":
        prompt = f"""{base_context}

Напиши пост-кейс из практики брокера: {title_hint}

Формат:
1. Эмоджи + заголовок (результат или цифра)
2. Ситуация клиента (кто, что везли, откуда)
3. Что мы сделали (конкретные действия)
4. Результат (сроки, экономия, решение)
5. CTA: "📩 Похожая ситуация? Напишите нам — custombroker.ge"
6. Хештеги (6-8 штук)

Длина: 500-800 символов. Пиши как реальную историю."""

    else:  # general tip
        prompt = f"""{base_context}

Напиши экспертный пост: {title_hint}

Формат:
1. Эмоджи + заголовок
2. Суть (2-3 предложения с конкретикой)
3. Полезные детали или пункты
4. CTA: "📩 Вопросы? Ана отвечает 24/7 на custombroker.ge"
5. Хештеги (6-8 штук)

Длина: 500-800 символов."""

    prompt += """

Также верни JSON-блок в конце:
```json
{"title": "заголовок для картинки (макс 35 символов)", "subtitle": "подзаголовок или цифра (макс 28 символов)", "emoji": "один эмоджи"}
```"""

    api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_KEY", "")
    client = Anthropic(api_key=api_key)

    response = _call_claude_with_retry(
        client,
        model="claude-haiku-4-5",
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text

    json_match = re.search(r'```json\s*({.*?})\s*```', raw, re.DOTALL)
    text = raw
    title = topic["title_hint"]
    subtitle = ""
    emoji = "🛃"

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
        "niche": topic.get("niche", "customs"),
        "type": post_type,
    }
