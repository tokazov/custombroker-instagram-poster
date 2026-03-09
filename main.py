"""Cargo Rapido Instagram Poster — auto-generates and posts to @cargo.rapido.

Cron: runs once daily (07:00 UTC = 11:00 Tbilisi).
"""

import os
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    logger.info("🚛 Cargo Rapido Instagram Poster starting...")

    from topics import get_random_topic, get_photo_keyword
    from generator import generate_post
    from image_gen import fetch_photo, generate_image
    from instagram import upload_and_post

    # 1. Pick topic
    topic = get_random_topic()
    logger.info(f"📝 Topic: {topic['title_hint']} ({topic['type']}/{topic['niche']})")

    # 2. Generate text
    post = generate_post(topic)
    logger.info(f"✍️ Post text: {len(post['text'])} chars")

    # 3. Fetch themed photo
    keyword = get_photo_keyword(topic["niche"])
    photo_path = fetch_photo(keyword)
    if not photo_path:
        photo_path = fetch_photo("cargo delivery truck")

    if not photo_path:
        logger.error("❌ No photo available")
        sys.exit(1)

    # 4. Generate image
    image_path = generate_image(post, photo_path)
    if not image_path:
        logger.error("❌ Image generation failed")
        sys.exit(1)

    # 5. Post to Instagram
    success = upload_and_post(image_path, post["text"])
    if success:
        logger.info("✅ Posted to Instagram!")
    else:
        logger.error("❌ Failed to post")
        sys.exit(1)

    # Cleanup
    for p in [photo_path, image_path]:
        try:
            os.unlink(p)
        except Exception:
            pass

    logger.info("🏁 Done!")


if __name__ == "__main__":
    main()
