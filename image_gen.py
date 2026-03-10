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
    """Build clean, minimal HTML poster with responsive text."""
    title = post.get("title", "")
    subtitle = post.get("subtitle", "")
    emoji = post.get("emoji", "\U0001F69B")
    post_type = post.get("type", "route")

    accents = {"route": "#f59e0b", "tip": "#10b981", "case": "#3b82f6", "promo": "#ef4444"}
    accent = accents.get(post_type, "#f59e0b")

    labels = {"route": "\u041C\u0410\u0420\u0428\u0420\u0423\u0422", "tip": "\u0421\u041E\u0412\u0415\u0422", "case": "\u041A\u0415\u0419\u0421", "promo": "\u0410\u041A\u0426\u0418\u042F"}
    label = labels.get(post_type, "")

    sub_html = ""
    if subtitle:
        sub_html = '<div class="accent-line"></div><div class="sub">' + subtitle + '</div>'

    css = f"""* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ width: 1080px; height: 1080px; overflow: hidden; font-family: 'Inter', 'Noto Color Emoji', 'Apple Color Emoji', sans-serif; }}
.poster {{ width: 1080px; height: 1080px; position: relative; display: flex; flex-direction: column; }}
.bg {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; }}
.overlay {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%;
  background: linear-gradient(180deg, rgba(0,0,0,0.2) 0%, rgba(0,0,0,0.05) 30%, rgba(0,0,0,0.35) 55%, rgba(0,0,0,0.92) 100%); }}
.top {{ position: absolute; top: 0; left: 0; right: 0; z-index: 2;
  padding: 40px 72px; display: flex; align-items: center; justify-content: space-between; }}
.logo {{ display: flex; align-items: center; gap: 12px; }}
.logo-mark {{ width: 40px; height: 40px; border-radius: 10px;
  background: linear-gradient(135deg, #f59e0b, #ea580c);
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; font-weight: 900; color: white; box-shadow: 0 2px 12px rgba(0,0,0,0.3); }}
.logo-name {{ font-size: 22px; font-weight: 800; color: white; text-shadow: 0 2px 12px rgba(0,0,0,0.6); }}
.logo-name span {{ color: #fbbf24; }}
.tag {{ padding: 6px 16px; border-radius: 6px; font-size: 13px; font-weight: 700;
  letter-spacing: 2px; text-transform: uppercase; background: {accent}; color: white;
  box-shadow: 0 2px 10px rgba(0,0,0,0.3); }}
.bottom {{ position: absolute; bottom: 60px; left: 72px; right: 72px; z-index: 2; }}
.emoji {{ font-size: 52px; margin-bottom: 16px; filter: drop-shadow(0 2px 8px rgba(0,0,0,0.4)); }}
.title {{ font-size: 52px; font-weight: 900; color: white; line-height: 1.2;
  word-wrap: break-word; overflow-wrap: break-word; white-space: normal;
  text-shadow: 0 2px 20px rgba(0,0,0,0.7), 0 1px 4px rgba(0,0,0,0.9); }}
.sub {{ font-size: 28px; font-weight: 600; color: {accent}; margin-top: 14px;
  text-shadow: 0 2px 12px rgba(0,0,0,0.7); word-wrap: break-word; overflow-wrap: break-word; white-space: normal; }}
.accent-line {{ width: 60px; height: 4px; background: {accent}; border-radius: 2px; margin: 20px 0; }}
.cta {{ position: absolute; bottom: 0; left: 0; right: 0; z-index: 3;
  background: rgba(0,0,0,0.7); backdrop-filter: blur(12px); padding: 18px 72px;
  display: flex; align-items: center; justify-content: space-between; border-top: 2px solid {accent}; }}
.cta-left {{ font-size: 18px; font-weight: 700; color: white; }}
.cta-right {{ font-size: 16px; font-weight: 600; color: rgba(255,255,255,0.7); }}"""

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
<style>{css}</style></head><body>
<div class="poster">
  <img class="bg" src="data:image/jpeg;base64,{photo_b64}" />
  <div class="overlay"></div>
  <div class="top">
    <div class="logo"><div class="logo-mark">CR</div><div class="logo-name">Cargo <span>Rapido</span></div></div>
    <div class="tag">{label}</div>
  </div>
  <div class="bottom">
    <div class="emoji">{emoji}</div>
    <div class="title">{title}</div>
    {sub_html}
  </div>
  <div class="cta">
    <div class="cta-left">@cargo.rapido</div>
    <div class="cta-right">taplink.cc/cargorapido</div>
  </div>
</div></body></html>"""
    return html


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
