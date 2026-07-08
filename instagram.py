"""Post to Instagram via Graph API."""

import os
import time
import uuid
import base64
import logging
import httpx

logger = logging.getLogger(__name__)

PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN", "")
IG_ACCOUNT_ID = os.getenv("IG_ACCOUNT_ID", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO = "tokazov/cargo-ig-uploads"  # PUBLIC repo for Instagram-accessible images


def upload_and_post(image_path: str, caption: str) -> bool:
    """Upload image to public URL, then post to Instagram."""
    if not PAGE_TOKEN or not IG_ACCOUNT_ID:
        logger.error("FB_PAGE_TOKEN or IG_ACCOUNT_ID not set")
        return False

    image_url = _upload_image(image_path)
    if not image_url:
        logger.error("Failed to upload image to public URL")
        return False

    logger.info(f"Image URL: {image_url}")

    client = httpx.Client(timeout=60)

    try:
        # Step 1: Create media container
        r = client.post(
            f"https://graph.facebook.com/v21.0/{IG_ACCOUNT_ID}/media",
            data={
                "image_url": image_url,
                "caption": caption,
                "access_token": PAGE_TOKEN,
            },
        )
        result = r.json()
        container_id = result.get("id")

        if not container_id:
            logger.error(f"Container creation failed: {result}")
            return False

        logger.info(f"Container created: {container_id}")

        # Step 2: Wait for media to be ready
        for attempt in range(30):
            time.sleep(5)
            r = client.get(
                f"https://graph.facebook.com/v21.0/{container_id}",
                params={
                    "fields": "status_code,status",
                    "access_token": PAGE_TOKEN,
                },
            )
            status = r.json()
            status_code = status.get("status_code", "UNKNOWN")
            logger.info(f"Media status (attempt {attempt+1}): {status_code}")

            if status_code == "FINISHED":
                break
            elif status_code == "ERROR":
                logger.error(f"Media processing error: {status}")
                return False
        else:
            logger.error("Media processing timeout (150s)")
            return False

        # Step 3: Publish
        r = client.post(
            f"https://graph.facebook.com/v21.0/{IG_ACCOUNT_ID}/media_publish",
            data={
                "creation_id": container_id,
                "access_token": PAGE_TOKEN,
            },
        )
        pub_result = r.json()

        if "id" in pub_result:
            logger.info(f"✅ Published to Instagram! Post ID: {pub_result['id']}")
            return True
        else:
            logger.error(f"Publish failed: {pub_result}")
            return False

    except Exception as e:
        logger.error(f"Instagram post failed: {e}")
        return False


def _upload_image(image_path: str) -> str | None:
    """Upload image and return public URL accessible by Instagram Graph API.

    Priority: GitHub raw (jsDelivr CDN) → imgbb → catbox.moe
    NOTE: Imgur and raw.githubusercontent.com are BLOCKED by Instagram (error 2207052).
    jsDelivr CDN (cdn.jsdelivr.net/gh/...) serves GitHub content and is Instagram-compatible.
    """

    # 1. GitHub + jsDelivr CDN — most reliable for Instagram
    if GITHUB_TOKEN:
        try:
            filename = f"temp_{uuid.uuid4().hex[:8]}.png"
            with open(image_path, "rb") as f:
                content_b64 = base64.b64encode(f.read()).decode()
            r = httpx.put(
                f"https://api.github.com/repos/{GITHUB_REPO}/contents/uploads/{filename}",
                headers={
                    "Authorization": f"token {GITHUB_TOKEN}",
                    "Accept": "application/vnd.github.v3+json",
                },
                json={
                    "message": f"Upload post image {filename}",
                    "content": content_b64,
                },
                timeout=60,
            )
            if r.status_code in (200, 201):
                # Use raw.githubusercontent.com — works for PUBLIC repos
                cdn_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/uploads/{filename}"
                logger.info(f"✅ Image uploaded to GitHub (public): {cdn_url}")
                time.sleep(2)
                return cdn_url
            else:
                logger.warning(f"GitHub upload failed: {r.status_code} {r.text[:100]}")
        except Exception as e:
            logger.warning(f"GitHub upload failed: {e}")

    # 2. imgbb (if key configured)
    imgbb_key = os.getenv("IMGBB_API_KEY", "")
    if imgbb_key:
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        try:
            r = httpx.post(
                "https://api.imgbb.com/1/upload",
                data={"key": imgbb_key, "image": b64},
                timeout=30,
            )
            result = r.json()
            if result.get("success"):
                url = result["data"]["url"]
                logger.info(f"✅ Image uploaded to imgbb: {url}")
                return url
        except Exception as e:
            logger.warning(f"imgbb failed: {e}")

    # 3. catbox.moe — free public CDN
    try:
        with open(image_path, "rb") as f:
            r = httpx.post(
                "https://catbox.moe/user/api.php",
                data={"reqtype": "fileupload"},
                files={"fileToUpload": ("image.png", f, "image/png")},
                timeout=30,
            )
        url = r.text.strip()
        if url.startswith("https://"):
            logger.info(f"✅ Image uploaded to catbox.moe: {url}")
            return url
        else:
            logger.warning(f"catbox.moe failed: {r.text[:100]}")
    except Exception as e:
        logger.warning(f"catbox.moe failed: {e}")

    logger.error("All image upload methods failed")
    return None
