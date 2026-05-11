"""Cargo Rapido Instagram Post Generator — MARKUS-style bold design."""

import os
import re
import textwrap
import httpx
import logging
import tempfile
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_BOLD = os.path.join(BASE_DIR, "fonts", "Montserrat-Bold.ttf")
FONT_REGULAR = os.path.join(BASE_DIR, "fonts", "Montserrat-Regular.ttf")
FONT_EXTRABOLD = os.path.join(BASE_DIR, "fonts", "Montserrat-ExtraBold.ttf")
if not os.path.exists(FONT_EXTRABOLD):
    FONT_EXTRABOLD = FONT_BOLD

PEXELS_KEY = os.getenv("PEXELS_API_KEY", "Jd4ELtMXmSoJq0uPtyW8Z53DPgYOyKp3deucoDVyqt533ne9FfVAz7mx")

SIZE = 1080
PAD = 60
CONTENT_W = SIZE - PAD * 2

# Brand colors — Cargo Rapido
import os as _os
_COLOR_SCHEME = _os.getenv("COLOR_SCHEME", "blue")

if _COLOR_SCHEME == "red":
    ACCENT_BLUE = (220, 38, 38)      # red
    ACCENT_ORANGE = (239, 68, 68)    # light red
    ACCENT_YELLOW = (254, 202, 202)  # very light red
    CTA_COLOR = (185, 28, 28)        # dark red
else:
    ACCENT_BLUE = (59, 130, 246)     # #3b82f6
    ACCENT_ORANGE = (249, 115, 22)   # #f97316 — cargo/logistics vibe
    ACCENT_YELLOW = (250, 204, 21)   # #facc15
    CTA_COLOR = ACCENT_BLUE


def fetch_photo(keyword: str) -> str | None:
    """Fetch a photo from Pexels with random page to avoid repetition."""
    try:
        import random
        page = random.randint(1, 5)  # случайная страница для разнообразия
        r = httpx.get(
            "https://api.pexels.com/v1/search",
            params={"query": keyword, "per_page": 15, "page": page, "orientation": "square"},
            headers={"Authorization": PEXELS_KEY},
            timeout=15,
        )
        r.raise_for_status()
        photos = r.json().get("photos", [])
        if not photos:
            # fallback to page 1
            r2 = httpx.get(
                "https://api.pexels.com/v1/search",
                params={"query": keyword, "per_page": 15, "page": 1, "orientation": "square"},
                headers={"Authorization": PEXELS_KEY},
                timeout=15,
            )
            photos = r2.json().get("photos", [])
        if not photos:
            return None
        photo = random.choice(photos)
        url = photo["src"]["large"]
        img_r = httpx.get(url, timeout=20)
        path = tempfile.mktemp(suffix=".jpg")
        with open(path, "wb") as f:
            f.write(img_r.content)
        return path
    except Exception as e:
        logger.error(f"Pexels error: {e}")
        return None


def fit_text(draw, text: str, font_path: str, max_size: int, min_size: int,
             max_width: int, max_lines: int = 99) -> tuple:
    """Auto-fit text. Returns (font, lines)."""
    font_size = max_size
    while font_size >= min_size:
        font = ImageFont.truetype(font_path, font_size)
        sample = "АБВГДЕЖЗИКЛМНОabcdefghijklmn"
        avg_char_w = draw.textlength(sample, font=font) / len(sample)
        chars_per_line = max(8, int(max_width / avg_char_w))
        lines = textwrap.wrap(text, width=chars_per_line)
        if len(lines) <= max_lines and all(
            draw.textlength(line, font=font) <= max_width for line in lines
        ):
            return font, lines
        font_size -= 4
    font = ImageFont.truetype(font_path, min_size)
    sample = "АБВГДЕЖЗИКЛМНОabcdefghijklmn"
    avg_char_w = draw.textlength(sample, font=font) / len(sample)
    chars_per_line = max(8, int(max_width / avg_char_w))
    lines = textwrap.wrap(text, width=chars_per_line)
    return font, lines[:max_lines]


def _strip_emoji(text: str) -> str:
    emoji_pattern = re.compile(
        "[😀-🙏🌀-🗿🚀-🛿"
        "🇠-🇿✂-➰Ⓜ-🉑"
        "🤀-🧿🨀-🩯🩰-🫿"
        "☀-⛿✀-➿]+", flags=re.UNICODE)
    return emoji_pattern.sub("", text).strip()


def generate_image(post: dict, photo_path: str = None) -> str | None:
    """Generate 1080×1080 Cargo Rapido post — bold MARKUS-style design.
    
    Style:
    - Big ExtraBold headline (white) with text shadow
    - Subtitle in yellow accent
    - Gradient overlay — top light, bottom dark for readability
    - Orange accent line before subtitle
    - Blue decorative stripe on left edge
    - CTA bar at bottom with branding
    """
    output_path = tempfile.mktemp(suffix=".png")

    # 1. Background photo
    if not photo_path:
        keyword = post.get("photo_keyword", "cargo delivery truck logistics")
        photo_path = fetch_photo(keyword)

    if photo_path and os.path.exists(photo_path):
        bg = Image.open(photo_path).convert("RGB")
        w, h = bg.size
        side = min(w, h)
        left = (w - side) // 2
        top = (h - side) // 2
        bg = bg.crop((left, top, left + side, top + side))
        bg = bg.resize((SIZE, SIZE), Image.LANCZOS)
    else:
        bg = Image.new("RGB", (SIZE, SIZE), (15, 20, 40))

    # 2. Gradient overlay (lighter top, heavy bottom for text)
    bg = bg.convert("RGBA")
    overlay = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    for y in range(SIZE // 3):
        alpha = int(80 + (y / (SIZE // 3)) * 60)
        overlay_draw.line([(0, y), (SIZE, y)], fill=(0, 0, 0, alpha))

    for y in range(SIZE // 3, SIZE):
        progress = (y - SIZE // 3) / (SIZE * 2 // 3)
        alpha = int(140 + progress * 90)
        overlay_draw.line([(0, y), (SIZE, y)], fill=(0, 0, 0, min(alpha, 235)))

    bg = Image.alpha_composite(bg, overlay)
    bg = bg.convert("RGB")
    draw = ImageDraw.Draw(bg)

    # 3. Logo top-left — CR badge
    _draw_logo(draw)

    # 4. Main title — BIG, EXTRABOLD, UPPERCASE
    title = _strip_emoji(post.get("title", "Cargo Rapido")).upper()
    title_font, title_lines = fit_text(
        draw, title, FONT_EXTRABOLD,
        max_size=90, min_size=52,
        max_width=CONTENT_W, max_lines=3
    )

    # 5. Subtitle — Bold, yellow accent
    subtitle = post.get("subtitle", "")
    sub_font, sub_lines = fit_text(
        draw, subtitle, FONT_BOLD,
        max_size=36, min_size=24,
        max_width=CONTENT_W, max_lines=3
    )

    # 6. Layout — text in bottom 60%, above CTA
    title_line_h = title_font.size * 1.25
    sub_line_h = sub_font.size * 1.45
    title_block_h = len(title_lines) * title_line_h
    sub_block_h = len(sub_lines) * sub_line_h
    gap = 20
    cta_h = 70

    total_text_h = title_block_h + gap + sub_block_h
    text_area_top = SIZE * 0.35
    text_area_bottom = SIZE - cta_h - 30
    y = text_area_top + (text_area_bottom - text_area_top - total_text_h) / 2

    # Draw title with text shadow
    for line in title_lines:
        draw.text((PAD + 2, y + 2), line, fill=(0, 0, 0), font=title_font)
        draw.text((PAD, y), line, fill="#FFFFFF", font=title_font)
        y += title_line_h

    y += gap

    # Orange accent line before subtitle
    if sub_lines:
        draw.rectangle([PAD, y - 8, PAD + 60, y - 4], fill=ACCENT_ORANGE)

    # Draw subtitle in yellow
    for line in sub_lines:
        draw.text((PAD, y), line, fill="#FACC15", font=sub_font)
        y += sub_line_h

    # 7. CTA bar at bottom
    _draw_cta(draw, cta_h)

    # 8. Decorative blue accent stripe on left edge
    draw.rectangle([0, SIZE // 3, 5, SIZE - cta_h], fill=ACCENT_BLUE)

    bg.save(output_path, quality=95)
    logger.info(f"✅ Post saved: {output_path}")
    return output_path


def _draw_logo(draw):
    """CR badge + Cargo Rapido text — top left."""
    badge_size = 44
    bx, by = PAD, PAD - 10
    draw.rounded_rectangle(
        [bx, by, bx + badge_size, by + badge_size],
        radius=10, fill=ACCENT_ORANGE,
    )
    cr_font = ImageFont.truetype(FONT_BOLD, 22)
    cr_w = draw.textlength("CR", font=cr_font)
    draw.text((bx + (badge_size - cr_w) / 2, by + 10), "CR", fill="white", font=cr_font)

    name_font = ImageFont.truetype(FONT_BOLD, 28)
    draw.text((bx + badge_size + 12, by + 8), "Cargo Rapido", fill="white", font=name_font)


def _draw_cta(draw, height: int = 70):
    """CTA bar — bottom of image."""
    y_start = SIZE - height
    draw.rectangle([0, y_start, SIZE, SIZE], fill=CTA_COLOR)

    cta_font = ImageFont.truetype(FONT_BOLD, 26)
    left_text = "🚛 Доставка грузов по всему миру"
    draw.text((PAD, y_start + (height - 26) / 2), left_text, fill="white", font=cta_font)

    handle = "taplink.cc/cargorapido"
    handle_font = ImageFont.truetype(FONT_REGULAR, 22)
    hw = draw.textlength(handle, font=handle_font)
    draw.text((SIZE - PAD - hw, y_start + (height - 22) / 2), handle, fill=(220, 220, 255), font=handle_font)
