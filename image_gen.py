"""Generate post image: Unsplash photo + overlay + text via Playwright."""

import os
import json
import httpx
import logging
import tempfile
import base64
import subprocess
import re as _re
import textwrap

logger = logging.getLogger(__name__)

UNSPLASH_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "")


def fetch_photo(keyword: str) -> str | None:
    """Fetch a random photo from Unsplash. Returns local path or None."""
    if not UNSPLASH_KEY:
        logger.error("UNSPLASH_ACCESS_KEY not set")
        return None

    try:
        r = httpx.get(
            "https://api.unsplash.com/photos/random",
            params={"query": keyword, "orientation": "squarish"},
            headers={"Authorization": f"Client-ID {UNSPLASH_KEY}"},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()

        url = data["urls"]["regular"]
        author = data["user"]["name"]
        photo_id = data["id"]
        logger.info(f"Unsplash photo: {photo_id} by {author} | query='{keyword}'")

        img_r = httpx.get(url, timeout=30)
        img_r.raise_for_status()

        path = tempfile.mktemp(suffix=".jpg")
        with open(path, "wb") as f:
            f.write(img_r.content)

        dl_url = data.get("links", {}).get("download_location")
        if dl_url:
            try:
                httpx.get(dl_url, headers={"Authorization": f"Client-ID {UNSPLASH_KEY}"}, timeout=5)
            except Exception:
                pass

        return path
    except Exception as e:
        logger.error(f"Unsplash fetch failed: {e}")
        return None


def _build_html(post: dict, photo_b64: str) -> str:
    """Build HTML template for the poster."""
    post_type = post["type"]
    title = post.get("title", "")
    subtitle = post.get("subtitle", "")
    emoji = post.get("emoji", "🤖")
    
    # Type-specific colors
    colors = {
        "case": {"badge_bg": "rgba(59,130,246,0.25)", "badge_color": "#93c5fd", "badge_border": "rgba(59,130,246,0.35)",
                 "cta_bg": "linear-gradient(135deg, rgba(59,130,246,0.95), rgba(37,99,235,0.95))", "label": "📊 Кейс"},
        "tip": {"badge_bg": "rgba(16,185,129,0.25)", "badge_color": "#6ee7b7", "badge_border": "rgba(16,185,129,0.35)",
                "cta_bg": "linear-gradient(135deg, rgba(16,185,129,0.95), rgba(5,150,105,0.95))", "label": "💡 Совет"},
        "offer": {"badge_bg": "rgba(239,68,68,0.25)", "badge_color": "#fca5a5", "badge_border": "rgba(239,68,68,0.35)",
                  "cta_bg": "linear-gradient(135deg, rgba(239,68,68,0.95), rgba(220,38,38,0.95))", "label": "🔥 Оффер"},
    }
    c = colors.get(post_type, colors["case"])

    # Build middle section based on type
    middle_html = ""
    if post_type == "case" and post.get("stats"):
        cards = "".join(f'''
        <div class="stat-card">
            <div class="stat-num">{s.split(" ")[0]}</div>
            <div class="stat-label">{" ".join(s.split(" ")[1:])}</div>
        </div>''' for s in post["stats"][:3])
        middle_html = f'<div class="stats-row">{cards}</div>'
    
    elif post_type == "tip" and post.get("points"):
        items = "".join(f'''
        <div class="list-item">
            <div class="item-num">{i+1}</div>
            <div class="item-text">{p}</div>
        </div>''' for i, p in enumerate(post["points"][:5]))
        middle_html = f'<div class="list">{items}</div>'
    
    elif post_type == "offer" and post.get("price"):
        feats = "".join(f'<div class="feature">{f}</div>' for f in post.get("features", [])[:4])
        middle_html = f'''
        <div class="price-card">
            <div class="price-row">
                <div class="price-from">от</div>
                <div class="price-num">{post["price"]}</div>
                <div class="price-per">/месяц</div>
            </div>
            <div class="features">{feats}</div>
        </div>'''

    return f'''<!DOCTYPE html>
<html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ width: 1080px; height: 1080px; overflow: hidden; font-family: 'Inter', 'Noto Color Emoji', 'Apple Color Emoji', sans-serif; }}
.poster {{ width: 1080px; height: 1080px; position: relative; display: flex; flex-direction: column; overflow: hidden; }}
.bg-photo {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; }}
.overlay {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%;
  background: linear-gradient(180deg, rgba(0,0,0,0.45) 0%, rgba(0,0,0,0.15) 30%, rgba(0,0,0,0.15) 60%, rgba(0,0,0,0.55) 100%); }}
.top-bar {{ padding: 48px 90px 0; display: flex; align-items: center; justify-content: space-between; position: relative; z-index: 2; }}
.logo {{ display: flex; align-items: center; gap: 14px; }}
.logo-icon {{ width: 44px; height: 44px; background: linear-gradient(135deg, #f59e0b, #ea580c); border-radius: 12px;
  display: flex; align-items: center; justify-content: center; font-size: 22px; font-weight: 900; color: white;
  box-shadow: 0 4px 15px rgba(59,130,246,0.4); }}
.logo-text {{ font-size: 26px; font-weight: 800; color: white; text-shadow: 0 2px 15px rgba(0,0,0,0.8), 0 1px 4px rgba(0,0,0,0.9); }}
.logo-text span {{ color: #fbbf24; }}
.badge {{ padding: 8px 18px; border-radius: 20px; font-size: 14px; font-weight: 700; letter-spacing: 1.5px;
  text-transform: uppercase; background: {c["badge_bg"]}; color: {c["badge_color"]};
  border: 1px solid {c["badge_border"]}; backdrop-filter: blur(10px); }}
.divider {{ margin: 28px 90px 0; height: 1px; background: linear-gradient(90deg, rgba(255,255,255,0.3), rgba(255,255,255,0.05)); position: relative; z-index: 2; }}
.content {{ flex: 1; padding: 44px 90px; display: flex; flex-direction: column; justify-content: center; position: relative; z-index: 2; }}
.emoji-icon {{ font-size: 64px; margin-bottom: 20px; filter: drop-shadow(0 4px 15px rgba(0,0,0,0.5)); }}
.title {{ font-size: 52px; font-weight: 900; color: #fff; line-height: 1.15; margin-bottom: 20px; max-width: 850px; word-wrap: break-word; overflow-wrap: break-word; white-space: normal; letter-spacing: -0.02em; text-shadow: 0 3px 20px rgba(0,0,0,0.8), 0 1px 5px rgba(0,0,0,0.9); }}
.subtitle {{ font-size: 34px; font-weight: 700; color: #fbbf24; word-wrap: break-word; overflow-wrap: break-word; max-width: 880px; text-shadow: 0 2px 15px rgba(0,0,0,0.8), 0 1px 4px rgba(0,0,0,0.9); margin-bottom: 28px; }}
.stats-row {{ display: flex; gap: 20px; margin-top: 16px; }}
.stat-card {{ background: rgba(0,0,0,0.45); border: 1px solid rgba(255,255,255,0.12); border-radius: 16px; padding: 20px 28px; backdrop-filter: blur(15px); }}
.stat-num {{ font-size: 32px; font-weight: 900; color: #fbbf24; }}
.stat-label {{ font-size: 16px; color: rgba(255,255,255,0.7); margin-top: 4px; }}
.list {{ display: flex; flex-direction: column; gap: 12px; margin-top: 8px; }}
.list-item {{ display: flex; align-items: center; gap: 16px; background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 14px 22px; backdrop-filter: blur(12px); }}
.item-num {{ width: 38px; height: 38px; min-width: 38px; background: linear-gradient(135deg, #10b981, #059669); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: 800; color: white; }}
.item-text {{ font-size: 22px; font-weight: 600; color: #f0f0f0; word-wrap: break-word; overflow-wrap: break-word; }}
.price-card {{ background: rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.1); border-radius: 20px; padding: 32px 36px; max-width: 700px; backdrop-filter: blur(15px); position: relative; overflow: hidden; margin-top: 8px; }}
.price-card::before {{ content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, #ef4444, #f59e0b); }}
.price-row {{ display: flex; align-items: baseline; gap: 12px; margin-bottom: 20px; }}
.price-from {{ font-size: 22px; color: rgba(255,255,255,0.6); font-weight: 600; }}
.price-num {{ font-size: 64px; font-weight: 900; color: #fbbf24; }}
.price-per {{ font-size: 22px; color: rgba(255,255,255,0.5); font-weight: 600; align-self: flex-end; padding-bottom: 12px; }}
.features {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
.feature {{ font-size: 20px; color: #6ee7b7; font-weight: 600; }}
.feature::before {{ content: '✓ '; color: #10b981; font-weight: 800; }}
.cta-bar {{ background: {c["cta_bg"]}; padding: 0 90px; height: 88px; height: 88px; display: flex; align-items: center; justify-content: space-between; position: relative; z-index: 2; }}
.cta-text {{ font-size: 28px; font-weight: 700; color: white; }}
.cta-url {{ font-size: 20px; color: rgba(255,255,255,0.8); font-weight: 600; }}
</style></head><body>
<div class="poster">
  <img class="bg-photo" src="data:image/jpeg;base64,{photo_b64}" />
  <div class="overlay"></div>
  <div class="top-bar">
    <div class="logo"><div class="logo-icon">CR</div><div class="logo-text">Cargo <span>Rapido</span></div></div>
    <div class="badge">{c["label"]}</div>
  </div>
  <div class="divider"></div>
  <div class="content">
    <div class="emoji-icon">{emoji}</div>
    <div class="title">{title}</div>
    {"<div class='subtitle'>" + subtitle + "</div>" if subtitle else ""}
    {middle_html}
  </div>
  <div class="cta-bar">
    <div class="cta-text">cargo.rapido | Ссылка в шапке</div>
    <div class="cta-url">taplink.cc/cargorapido</div>
  </div>
</div></body></html>'''


def generate_image(post: dict, photo_path: str) -> str | None:
    """Generate poster image. Returns path to PNG or None."""
    try:
        with open(photo_path, "rb") as f:
            photo_b64 = base64.b64encode(f.read()).decode()

        html = _build_html(post, photo_b64)
        html_path = tempfile.mktemp(suffix=".html")
        out_path = tempfile.mktemp(suffix=".png")

        with open(html_path, "w") as f:
            f.write(html)

        app_dir = os.path.dirname(os.path.abspath(__file__))
        node_modules = os.path.join(app_dir, "node_modules")
        if not os.path.exists(node_modules):
            subprocess.run(["npm", "install", "playwright"], cwd=app_dir, capture_output=True, timeout=60)

        js_path = os.path.join(app_dir, "_render.js")
        script = f"""
const {{ chromium }} = require('playwright');
(async () => {{
  const browser = await chromium.launch({{args: ['--no-sandbox']}});
  const page = await browser.newPage({{ viewport: {{ width: 1080, height: 1080 }} }});
  await page.goto('file://{html_path}', {{waitUntil: 'domcontentloaded'}});
  await new Promise(r => setTimeout(r, 3000));
  await page.screenshot({{ path: '{out_path}', clip: {{ x: 0, y: 0, width: 1080, height: 1080 }} }});
  await browser.close();
}})();
"""
        with open(js_path, "w") as f:
            f.write(script)

        result = subprocess.run(["node", js_path], capture_output=True, text=True, timeout=30, cwd=app_dir)
        if result.returncode != 0:
            logger.error(f"Playwright render failed: {result.stderr[:200]}")
            logger.info("Trying PIL fallback...")
            return _pil_fallback(post, photo_path)

        logger.info(f"Image generated: {out_path}")
        return out_path

    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        logger.info("Trying PIL fallback...")
        return _pil_fallback(post, photo_path)


# ── PIL fallback with fit_text ──────────────────────────────────────────────

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SAFE_WIDTH = 920  # 1080 - 80px*2


def _fit_text(draw, text, font_path, max_size, min_size=28, max_lines=3):
    """Shrink font until text fits within SAFE_WIDTH with word wrap."""
    font_size = max_size
    font = None
    lines = [text]

    while font_size >= min_size:
        try:
            font = __import__('PIL.ImageFont', fromlist=['ImageFont']).truetype(font_path, font_size)
        except Exception:
            font = __import__('PIL.ImageFont', fromlist=['ImageFont']).load_default()
            break
        avg_char_w = font_size * 0.55
        chars_per_line = max(10, int(SAFE_WIDTH / avg_char_w))
        lines = textwrap.wrap(text, width=chars_per_line)
        if not lines:
            lines = [text]
        fits = all(draw.textlength(line, font=font) <= SAFE_WIDTH for line in lines)
        if fits and len(lines) <= max_lines:
            return font, lines
        font_size -= 4

    # Last resort
    try:
        font = __import__('PIL.ImageFont', fromlist=['ImageFont']).truetype(font_path, min_size)
    except Exception:
        font = __import__('PIL.ImageFont', fromlist=['ImageFont']).load_default()
    avg_char_w = min_size * 0.55
    chars_per_line = max(10, int(SAFE_WIDTH / avg_char_w))
    lines = textwrap.wrap(text, width=chars_per_line)[:max_lines]
    return font, lines


def _pil_fallback(post: dict, photo_path: str) -> str | None:
    """Fallback: render post image with Pillow + fit_text auto-sizing."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        logger.error("Pillow not installed for fallback")
        return None

    try:
        img = Image.open(photo_path).convert("RGB")
        img = img.resize((1080, 1080), Image.LANCZOS)

        # Gradient overlay (darker at bottom)
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw_ov = ImageDraw.Draw(overlay)
        for y in range(1080):
            alpha = int(30 + (y / 1080) ** 1.5 * 200)
            draw_ov.line([(0, y), (1080, y)], fill=(0, 0, 0, min(alpha, 240)))
        img = img.convert("RGBA")
        img = Image.alpha_composite(img, overlay)

        draw = ImageDraw.Draw(img)

        # Strip emoji from text
        title = post.get("title", post.get("title_hint", "Cargo Rapido"))
        title = _re.sub(r'[\U00010000-\U0010ffff]', '', title).strip()
        subtitle = post.get("subtitle", "")
        subtitle = _re.sub(r'[\U00010000-\U0010ffff]', '', subtitle).strip()

        # Auto-fit title
        title_font, title_lines = _fit_text(draw, title, FONT_BOLD, max_size=56, min_size=30, max_lines=3)
        line_h = int(title_font.size * 1.3)
        total_title_h = len(title_lines) * line_h

        # Auto-fit subtitle
        sub_lines = []
        sub_font = None
        sub_h = 0
        if subtitle:
            sub_font, sub_lines = _fit_text(draw, subtitle, FONT_REGULAR, max_size=30, min_size=20, max_lines=2)
            sub_h = len(sub_lines) * int(sub_font.size * 1.3) + 30

        # Position from bottom (above footer)
        footer_h = 60
        y_start = 1080 - footer_h - sub_h - total_title_h - 80

        # Draw title
        for i, line in enumerate(title_lines):
            draw.text((80, y_start + i * line_h), line, fill="white", font=title_font)

        # Draw subtitle
        if sub_lines and sub_font:
            sub_y = y_start + total_title_h + 24
            sub_line_h = int(sub_font.size * 1.3)
            for i, line in enumerate(sub_lines):
                draw.text((80, sub_y + i * sub_line_h), line, fill="#fbbf24", font=sub_font)

        # Footer bar
        draw.rectangle([(0, 1020), (1080, 1080)], fill=(0, 0, 0))
        try:
            font_small = ImageFont.truetype(FONT_REGULAR, 20)
        except Exception:
            font_small = ImageFont.load_default()
        draw.text((80, 1038), "@cargo.rapido", fill="white", font=font_small)
        draw.text((720, 1038), "taplink.cc/cargorapido", fill=(180, 180, 180), font=font_small)

        # Logo top-left
        try:
            font_logo = ImageFont.truetype(FONT_BOLD, 22)
        except Exception:
            font_logo = ImageFont.load_default()
        draw.text((80, 40), "CR  Cargo Rapido", fill="white", font=font_logo)

        out_path = photo_path.replace(".jpg", "_final.png")
        img = img.convert("RGB")
        img.save(out_path, "PNG", quality=95)
        logger.info(f"PIL fallback image: {out_path}")
        return out_path

    except Exception as e:
        logger.error(f"PIL fallback failed: {e}")
        return None
