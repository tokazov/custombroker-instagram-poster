"""Post to Instagram via Graph API."""

import os
import time
import logging
import httpx

logger = logging.getLogger(__name__)

PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN", "")
IG_ACCOUNT_ID = os.getenv("IG_ACCOUNT_ID", "")


def upload_and_post(image_path: str, caption: str) -> bool:
    """Upload image to public URL, then post to Instagram.
    
    Instagram API requires a public URL for the image.
    We upload to imgbb (free) then use that URL.
    """
    if not PAGE_TOKEN or not IG_ACCOUNT_ID:
        logger.error("FB_PAGE_TOKEN or IG_ACCOUNT_ID not set")
        return False

    # Upload image to get a public URL (use imgbb free API or GitHub)
    image_url = _upload_image(image_path)
    if not image_url:
        logger.error("Failed to upload image to public URL")
        return False

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
        for attempt in range(12):  # max 60 seconds
            r = client.get(
                f"https://graph.facebook.com/v21.0/{container_id}",
                params={
                    "fields": "status_code,status",
                    "access_token": PAGE_TOKEN,
                },
            )
            status = r.json()
            
            if status.get("status_code") == "FINISHED":
                break
            elif status.get("status_code") == "ERROR":
                logger.error(f"Media processing error: {status}")
                return False
            
            time.sleep(5)
        else:
            logger.error("Media processing timeout")
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
    """Upload image to imgbb and return public URL."""
    import base64
    
    imgbb_key = os.getenv("IMGBB_API_KEY", "")
    
    if imgbb_key:
        # Use imgbb
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        
        r = httpx.post(
            "https://api.imgbb.com/1/upload",
            data={"key": imgbb_key, "image": b64},
            timeout=30,
        )
        result = r.json()
        if result.get("success"):
            url = result["data"]["url"]
            logger.info(f"Image uploaded to imgbb: {url}")
            return url
    
    # Fallback: upload to GitHub repo as temp file
    github_token = os.getenv("GITHUB_TOKEN", "")
    if github_token:
        import hashlib
        with open(image_path, "rb") as f:
            content = f.read()
            b64 = base64.b64encode(content).decode()
            fname = f"temp_{hashlib.md5(content).hexdigest()[:8]}.png"
        
        r = httpx.put(
            f"https://api.github.com/repos/tokazov/cargo-instagram-poster/contents/uploads/{fname}",
            headers={"Authorization": f"token {github_token}"},
            json={
                "message": f"Upload {fname}",
                "content": b64,
            },
            timeout=30,
        )
        if r.status_code in (200, 201):
            url = r.json()["content"]["download_url"]
            logger.info(f"Image uploaded to GitHub: {url}")
            return url
    
    logger.error("No image upload method available")
    return None
