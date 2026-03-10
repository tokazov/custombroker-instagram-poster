"""Generate post image: Unsplash photo + overlay + text via Playwright."""

import os
import json
import httpx
import logging
import tempfile
import base64
import subprocess

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
        
        # Get regular size URL (1080w)
        url = data["urls"]["regular"]
        author = data["user"]["name"]
        photo_id = data["id"]
        logger.info(f"Unsplash photo: {photo_id} by {author} | query='{keyword}'")
        
        # Download
        img_r = httpx.get(url, timeout=30)
        img_r.raise_for_status()
        
        path = tempfile.mktemp(suffix=".jpg")
        with open(path, "wb") as f:
            f.write(img_r.content)
        
        # Track download for Unsplash guidelines
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
    """Build clean, minimal HTML poster — looks great in Instagram grid."""
    title = post.get("title", "")
    subtitle = post.get("subtitle", "")
    emoji = post.get("emoji", "\U0001F69B")
    post_type = post.get("type", "route")

    accents = {"route": "#f59e0b", "tip": "#10b981", "case": "#3b82f6", "promo": "#ef4444"}
    accent = accents.get(post_type, "#f59e0b")

    labels = {"route": "МАРШРУТ", "tip": "СОВЕТ", "case": "КЕЙС", "promo": "АКЦИЯ"}
    label = labels.get(post_type, "")

    sub_html = ""
    if subtitle:
        sub_html = '<div class="accent-line"></div><div class="sub">' + subtitle + '</div>'

    return (
        '<!DOCTYPE html>\n'
        '<html><head><meta charset="utf-8">\n'
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">\n'
        '<style>\n'
        '* { margin: 0; padding: 0; box-sizing: border-box; }\n'
        f"body {{ width: 1080px; height: 1080px; overflow: hidden; font-family: 'Inter', 'Noto Color Emoji', 'Apple Color Emoji', sans-serif; }}\n"
        '.poster { width: 1080px; height: 1080px; position: relative; display: flex; flex-direction: column; }\n'
        '.bg { position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; }\n'
        '.overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%;\n'
        '  background: linear-gradient(180deg, rgba(0,0,0,0.15) 0%, rgba(0,0,0,0.05) 35%, rgba(0,0,0,0.25) 65%, rgba(0,0,0,0.85) 100%); }\n'
        '.top { position: absolute; top: 0; left: 0; right: 0; z-index: 2;\n'
        '  padding: 36px 48px; display: flex; align-items: center; justify-content: space-between; }\n'
        '.logo { display: flex; align-items: center; gap: 12px; }\n'
        '.logo-mark { width: 40px; height: 40px; border-radius: 10px;\n'
        '  background: linear-gradient(135deg, #f59e0b, #ea580c);\n'
        '  display: flex; align-items: center; justify-content: center;\n'
        '  font-size: 18px; font-weight: 900; color: white; box-shadow: 0 2px 12px rgba(0,0,0,0.3); }\n'
        '.logo-name { font-size: 22px; font-weight: 800; color: white; text-shadow: 0 2px 12px rgba(0,0,0,0.6); }\n'
        f'.logo-name span {{ color: #fbbf24; }}\n'
        f'.tag {{ padding: 6px 16px; border-radius: 6px; font-size: 13px; font-weight: 700;\n'
        f'  letter-spacing: 2px; text-transform: uppercase; background: {accent}; color: white;\n'
        f'  box-shadow: 0 2px 10px rgba(0,0,0,0.3); }}\n'
        '.bottom { position: absolute; bottom: 0; left: 0; right: 0; z-index: 2; padding: 0 56px 80px; }\n'
        '.emoji { font-size: 52px; margin-bottom: 16px; filter: drop-shadow(0 2px 8px rgba(0,0,0,0.4)); }\n'
        '.title { font-size: 48px; font-weight: 900; color: white; line-height: 1.15;\n'
        '  max-width: 900px; word-wrap: break-word; overflow-wrap: break-word;\n'
        '  text-shadow: 0 2px 20px rgba(0,0,0,0.7), 0 1px 4px rgba(0,0,0,0.9); }\n'
        f'.sub {{ font-size: 28px; font-weight: 600; color: {accent}; margin-top: 12px;\n'
        f'  text-shadow: 0 2px 12px rgba(0,0,0,0.7); word-wrap: break-word; max-width: 800px; }}\n'
        f'.accent-line {{ width: 60px; height: 4px; background: {accent}; border-radius: 2px; margin: 20px 0; }}\n'
        '.cta { position: absolute; bottom: 0; left: 0; right: 0; z-index: 3;\n'
        f'  background: rgba(0,0,0,0.7); backdrop-filter: blur(12px); padding: 16px 56px;\n'
        f'  display: flex; align-items: center; justify-content: space-between; border-top: 2px solid {accent}; }}\n'
        '.cta-left { font-size: 18px; font-weight: 700; color: white; }\n'
        '.cta-right { font-size: 16px; font-weight: 600; color: rgba(255,255,255,0.7); }\n'
        '</style></head><body>\n'
        '<div class="poster">\n'
        f'  <img class="bg" src="data:image/jpeg;base64,{photo_b64}" />\n'
        '  <div class="overlay"></div>\n'
        '  <div class="top">\n'
        '    <div class="logo"><div class="logo-mark">CR</div>'
        '<div class="logo-name">Cargo <span>Rapido</span></div></div>\n'
        f'    <div class="tag">{label}</div>\n'
        '  </div>\n'
        '  <div class="bottom">\n'
        f'    <div class="emoji">{emoji}</div>\n'
        f'    <div class="title">{title}</div>\n'
        f'    {sub_html}\n'
        '  </div>\n'
        '  <div class="cta">\n'
        '    <div class="cta-left">@cargo.rapido</div>\n'
        '    <div class="cta-right">taplink.cc/cargorapido</div>\n'
        '  </div>\n'
        '</div></body></html>'
    )


def generate_image(post: dict, photo_path: str) -> str | None:
    """Generate poster image. Returns path to PNG or None."""
    try:
        # Read photo as base64
        with open(photo_path, "rb") as f:
            photo_b64 = base64.b64encode(f.read()).decode()

        html = _build_html(post, photo_b64)

        html_path = tempfile.mktemp(suffix=".html")
        out_path = tempfile.mktemp(suffix=".png")

        with open(html_path, "w") as f:
            f.write(html)

        # Render via Playwright CLI
        # Find playwright module path
        app_dir = os.path.dirname(os.path.abspath(__file__))
        node_modules = os.path.join(app_dir, "node_modules")
        if not os.path.exists(node_modules):
            # Try installing locally
            subprocess.run(["npm", "install", "playwright"], cwd=app_dir, capture_output=True, timeout=60)

        js_path = os.path.join(app_dir, "_render.js")
        script = f"""
const {{ chromium }} = require('playwright');
(async () => {{
  const browser = await chromium.launch({{args: ['--no-sandbox']}});
  const page = await browser.newPage({{ viewport: {{ width: 1080, height: 1080 }} }});
  await page.goto('file://{html_path}', {{waitUntil: 'domcontentloaded'}}); await new Promise(r => setTimeout(r, 2000));
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


def _pil_fallback(post: dict, photo_path: str) -> str | None:
    """Fallback: render post image with Pillow when Playwright fails."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        logger.error("Pillow not installed for fallback")
        return None

    try:
        img = Image.open(photo_path).convert("RGB")
        img = img.resize((1080, 1080), Image.LANCZOS)

        # Dark overlay
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 160))
        img = img.convert("RGBA")
        img = Image.alpha_composite(img, overlay)

        draw = ImageDraw.Draw(img)

        # Try to load a nice font, fallback to default
        try:
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            font_body = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except (IOError, OSError):
            font_title = ImageFont.load_default()
            font_body = font_title
            font_small = font_title

        title = post.get("title", post.get("title_hint", "Cargo Rapido"))

        # Title (skip emoji — PIL can't render them)
        draw.text((80, 80), title, fill="white", font=font_title)

        # Body text (word-wrap, strip emoji)
        import re as _re
        text = post.get("text", "")[:400]
        text = _re.sub(r'[\U00010000-\U0010ffff]', '', text)  # strip emoji
        y = 200
        for line in text.split("\n")[:12]:
            draw.text((80, y), line, fill="white", font=font_body)
            y += 42

        # Footer
        draw.text((80, 980), "CARGO RAPIDO  •  cargo.rapido", fill=(200, 200, 200), font=font_small)

        out_path = photo_path.replace(".jpg", "_final.png")
        img = img.convert("RGB")
        img.save(out_path, "PNG", quality=95)
        logger.info(f"PIL fallback image: {out_path}")
        return out_path

    except Exception as e:
        logger.error(f"PIL fallback failed: {e}")
        return None
