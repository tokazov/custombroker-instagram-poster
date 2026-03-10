"""Cargo Rapido Instagram Post Generator — PIL + Montserrat + fit_text."""

import os
import textwrap
import httpx
import logging
import tempfile
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_BOLD = os.path.join(BASE_DIR, "fonts", "Montserrat-Bold.ttf")
FONT_REGULAR = os.path.join(BASE_DIR, "fonts", "Montserrat-Regular.ttf")
UNSPLASH_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "")

SIZE = 1080
PAD = 60
CONTENT_W = SIZE - PAD * 2  # 960px
CTA_HEIGHT = 70
CTA_COLOR = (59, 130, 246)  # #3b82f6
OVERLAY_OPACITY = 0.65


def fetch_photo(keyword: str) -> str | None:
    """Fetch a random photo from Unsplash."""
    if not UNSPLASH_KEY:
        logger.error("UNSPLASH_ACCESS_KEY not set")
        return None
    try:
        r = httpx.get(
            "https://api.unsplash.com/photos/random",
            params={"query": keyword, "w": 1080},
            headers={"Authorization": f"Client-ID {UNSPLASH_KEY}"},
            timeout=15,
        )
        r.raise_for_status()
        url = r.json()["urls"]["regular"]
        img_r = httpx.get(url, timeout=15)
        path = tempfile.mktemp(suffix=".jpg")
        with open(path, "wb") as f:
            f.write(img_r.content)
        return path
    except Exception as e:
        logger.error(f"Unsplash error: {e}")
        return None


def fit_text(draw, text: str, font_path: str, max_size: int, min_size: int,
             max_width: int, max_lines: int = 99) -> tuple:
    """Auto-fit text: shrink font until it fits. Returns (font, lines)."""
    font_size = max_size
    while font_size >= min_size:
        font = ImageFont.truetype(font_path, font_size)
        avg_char_w = font_size * 0.55
        chars_per_line = max(10, int(max_width / avg_char_w))
        lines = textwrap.wrap(text, width=chars_per_line)
        if len(lines) <= max_lines and all(
            draw.textlength(line, font=font) <= max_width for line in lines
        ):
            return font, lines
        font_size -= 4
    font = ImageFont.truetype(font_path, min_size)
    chars_per_line = max(10, int(max_width / (min_size * 0.55)))
    lines = textwrap.wrap(text, width=chars_per_line)
    return font, lines[:max_lines]


def generate_image(post: dict, photo_path: str = None) -> str | None:
    """Generate a 1080×1080 Cargo Rapido Instagram post.
    
    post keys: title, subtitle, emoji, type, photo_keyword
    Returns: path to image or None
    """
    output_path = tempfile.mktemp(suffix=".png")

    # 1. Background
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
        bg = Image.new("RGB", (SIZE, SIZE), (20, 25, 40))

    # 2. Dark overlay 65%
    overlay = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, int(255 * OVERLAY_OPACITY)))
    bg = bg.convert("RGBA")
    bg = Image.alpha_composite(bg, overlay)
    bg = bg.convert("RGB")

    draw = ImageDraw.Draw(bg)

    # 3. Logo top-left: "CR" badge + "Cargo Rapido"
    _draw_logo(draw)

    # 4. Title — Montserrat Bold, UPPERCASE
    title = post.get("title", "Cargo Rapido").upper()
    title_font, title_lines = fit_text(
        draw, title, FONT_BOLD,
        max_size=80, min_size=48,
        max_width=CONTENT_W, max_lines=2
    )

    # 5. Subtitle — Montserrat Regular
    subtitle = post.get("subtitle", "")
    sub_font, sub_lines = fit_text(
        draw, subtitle, FONT_REGULAR,
        max_size=40, min_size=28,
        max_width=CONTENT_W, max_lines=4
    )

    # 6. Vertical layout
    title_line_h = title_font.size * 1.2
    sub_line_h = sub_font.size * 1.45
    title_block_h = len(title_lines) * title_line_h
    sub_block_h = len(sub_lines) * sub_line_h
    gap = 30

    total_h = title_block_h + gap + sub_block_h
    usable_top = 120
    usable_bottom = SIZE - CTA_HEIGHT - PAD
    y = usable_top + (usable_bottom - usable_top - total_h) / 2

    # Draw title
    for line in title_lines:
        draw.text((PAD, y), line, fill="#FFFFFF", font=title_font)
        y += title_line_h

    # Draw subtitle
    y += gap
    for line in sub_lines:
        draw.text((PAD, y), line, fill="#EEEEEE", font=sub_font)
        y += sub_line_h

    # 7. CTA bar
    _draw_cta(draw)

    bg.save(output_path, quality=95)
    logger.info(f"✅ Post saved: {output_path}")
    return output_path


def _draw_logo(draw):
    """CR badge + Cargo Rapido text."""
    badge_size = 44
    bx, by = PAD, PAD - 10
    draw.rounded_rectangle(
        [bx, by, bx + badge_size, by + badge_size],
        radius=10, fill=CTA_COLOR
    )
    ac_font = ImageFont.truetype(FONT_BOLD, 22)
    ac_w = draw.textlength("CR", font=ac_font)
    draw.text((bx + (badge_size - ac_w) / 2, by + 10), "CR", fill="white", font=ac_font)

    name_font = ImageFont.truetype(FONT_BOLD, 28)
    draw.text((bx + badge_size + 12, by + 8), "Cargo Rapido", fill="white", font=name_font)


def _draw_cta(draw):
    """Blue CTA bar at bottom."""
    y_start = SIZE - CTA_HEIGHT
    draw.rectangle([0, y_start, SIZE, SIZE], fill=CTA_COLOR)
    
    cta_font = ImageFont.truetype(FONT_BOLD, 22)
    left_text = "cargo.rapido  |  Ссылка в шапке"
    draw.text((PAD, y_start + (CTA_HEIGHT - 22) / 2), left_text, fill="white", font=cta_font)

    right_text = "taplink.cc/cargorapido"
    right_font = ImageFont.truetype(FONT_REGULAR, 20)
    rw = draw.textlength(right_text, font=right_font)
    draw.text((SIZE - PAD - rw, y_start + (CTA_HEIGHT - 20) / 2), right_text, fill=(220, 220, 255), font=right_font)
