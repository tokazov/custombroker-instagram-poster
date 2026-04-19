"""Cargo Rapido Instagram Poster — auto-generates and posts to @cargo.rapido.

Cron: runs twice daily:
  - 04:00 UTC (08:00 Tbilisi) — RED variant
  - 14:00 UTC (18:00 Tbilisi) — BLUE variant
"""

import os
import sys
import logging
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    utc_hour = datetime.now(timezone.utc).hour
    color_scheme = os.getenv("COLOR_SCHEME", "")

    if not color_scheme:
        # 04:00-06:00 UTC = red (morning), rest = blue
        if 4 <= utc_hour <= 6:
            color_scheme = "red"
        else:
            color_scheme = "blue"

    # Set BEFORE any module imports so image_gen.py picks it up correctly
    os.environ["COLOR_SCHEME"] = color_scheme
    logger.info(f"🚛 Cargo Rapido Instagram Poster starting... COLOR={color_scheme} UTC_HOUR={utc_hour}")

    from topics import get_random_topic, get_photo_keyword
    from generator import generate_post
    from image_gen import fetch_photo, generate_image
    from instagram import upload_and_post

    topic = get_random_topic()
    logger.info(f"📝 Topic: {topic['title_hint']} ({topic['type']}/{topic['niche']})")

    post = generate_post(topic)
    logger.info(f"✍️ Post text: {len(post['text'])} chars")

    keyword = get_photo_keyword(topic["niche"])
    photo_path = fetch_photo(keyword)
    if not photo_path:
        photo_path = fetch_photo("cargo delivery truck")

    if not photo_path:
        logger.error("❌ No photo available")
        sys.exit(1)

    image_path = generate_image(post, photo_path)
    if not image_path:
        logger.error("❌ Image generation failed")
        sys.exit(1)

    success = upload_and_post(image_path, post["text"])
    if success:
        logger.info(f"✅ Posted to Instagram! ({color_scheme} variant)")
    else:
        logger.error("❌ Failed to post")
        sys.exit(1)

    for p in [photo_path, image_path]:
        try:
            os.unlink(p)
        except Exception:
            pass

    logger.info("🏁 Done!")


if __name__ == "__main__":
    main()
