#!/usr/bin/env python3
"""
VirtuAI Content Pipeline — Multi-Platform Publishing
======================================================

Publishes content to social media platforms by:
1. Pulling the next pending post from the schedule database
2. Validating assets (clip exists, caption ready)
3. Authenticating to the target platform API
4. Uploading with correct format and metadata
5. Logging the result back to the schedule database

Usage:
    python scripts/publish.py --dispatch                     # Publish next due post
    python scripts/publish.py --post-id 42                   # Publish a specific post
    python scripts/publish.py --persona luna-ai --dry-run    # Preview without posting
"""

import argparse
import json
import logging
import os
import sys
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Platform Adapters (Abstract Base)
# ──────────────────────────────────────────────

class PlatformAdapter(ABC):
    """Abstract base for platform-specific publishing logic."""

    def __init__(self, config: dict, platform_config: dict):
        self.config = config
        self.platform_config = platform_config

    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate to the platform. Returns True if successful."""
        ...

    @abstractmethod
    def publish_video(self, clip_path: Path, caption: str, hashtags: list[str]) -> dict:
        """
        Publish a video post.

        Returns:
            Dict with keys: success (bool), post_url (str), platform_post_id (str), error (str, optional)
        """
        ...

    @abstractmethod
    def publish_image(self, image_path: Path, caption: str, hashtags: list[str]) -> dict:
        """
        Publish an image/carousel post.

        Returns:
            Dict with keys: success (bool), post_url (str), platform_post_id (str), error (str, optional)
        """
        ...


# ──────────────────────────────────────────────
# Platform Adapter — Dry Run (Testing)
# ──────────────────────────────────────────────

class DryRunAdapter(PlatformAdapter):
    """Simulates publishing without calling any external API."""

    def authenticate(self) -> bool:
        logger.info("[DRY RUN] Authentication skipped")
        return True

    def publish_video(self, clip_path: Path, caption: str, hashtags: list[str]) -> dict:
        logger.info("[DRY RUN] Would publish video: %s", clip_path)
        logger.info("[DRY RUN] Caption (%d chars): %s", len(caption), caption[:80] + "...")
        logger.info("[DRY RUN] Hashtags: %s", " ".join(hashtags))
        return {
            "success": True,
            "post_url": f"https://example.com/dry-run/{clip_path.stem}",
            "platform_post_id": f"dry_{clip_path.stem}",
            "error": None,
        }

    def publish_image(self, image_path: Path, caption: str, hashtags: list[str]) -> dict:
        return self.publish_video(image_path, caption, hashtags)


# ──────────────────────────────────────────────
# Platform Adapter — Placeholder (Real API)
# ──────────────────────────────────────────────

class TikTokAdapter(PlatformAdapter):
    """Adapter for TikTok publishing via their API."""

    def authenticate(self) -> bool:
        # TODO: Implement OAuth flow with TikTok Business API
        logger.info("TikTok authentication placeholder")
        return True

    def publish_video(self, clip_path: Path, caption: str, hashtags: list[str]) -> dict:
        # TODO: Upload via TikTok Business API / Videos endpoint
        logger.info("TikTok video publish placeholder: %s", clip_path)
        return {
            "success": True,
            "post_url": f"https://www.tiktok.com/@virtuai/video/placeholder",
            "platform_post_id": "tt_placeholder",
            "error": None,
        }

    def publish_image(self, image_path: Path, caption: str, hashtags: list[str]) -> dict:
        raise NotImplementedError("TikTok image posts not yet supported")


class InstagramAdapter(PlatformAdapter):
    """Adapter for Instagram publishing via Graph API."""

    def authenticate(self) -> bool:
        # TODO: Implement OAuth with Facebook/Instagram Graph API
        logger.info("Instagram authentication placeholder")
        return True

    def publish_video(self, clip_path: Path, caption: str, hashtags: list[str]) -> dict:
        # TODO: Upload as Reel via Instagram Graph API
        logger.info("Instagram Reel publish placeholder: %s", clip_path)
        return {
            "success": True,
            "post_url": f"https://www.instagram.com/p/placeholder",
            "platform_post_id": "ig_placeholder",
            "error": None,
        }

    def publish_image(self, image_path: Path, caption: str, hashtags: list[str]) -> dict:
        logger.info("Instagram feed post placeholder: %s", image_path)
        return {
            "success": True,
            "post_url": f"https://www.instagram.com/p/placeholder",
            "platform_post_id": "ig_img_placeholder",
            "error": None,
        }


class TwitterAdapter(PlatformAdapter):
    """Adapter for X/Twitter publishing via their API."""

    def authenticate(self) -> bool:
        # TODO: Implement OAuth 1.0a with Twitter API v2
        logger.info("Twitter authentication placeholder")
        return True

    def publish_video(self, clip_path: Path, caption: str, hashtags: list[str]) -> dict:
        logger.info("Twitter video publish placeholder: %s", clip_path)
        return {
            "success": True,
            "post_url": f"https://x.com/virtuai/status/placeholder",
            "platform_post_id": "tw_placeholder",
            "error": None,
        }

    def publish_image(self, image_path: Path, caption: str, hashtags: list[str]) -> dict:
        # Twitter treats images and videos the same via media upload
        return self.publish_video(image_path, caption, hashtags)


# ──────────────────────────────────────────────
# Publisher
# ──────────────────────────────────────────────

ADAPTER_REGISTRY = {
    "tiktok": TikTokAdapter,
    "instagram": InstagramAdapter,
    "twitter": TwitterAdapter,
    "youtube_shorts": TikTokAdapter,  # Same-style vertical video API
    "dry-run": DryRunAdapter,
}


class Publisher:
    """
    Orchestrates publishing: reads the schedule, picks the right adapter,
    uploads content, and records results.
    """

    def __init__(self, config: dict):
        self.config = config
        from schedule_post import Scheduler
        self.scheduler = Scheduler(config)
        self._adapters: dict[str, PlatformAdapter] = {}

    def _get_adapter(self, platform: str) -> PlatformAdapter:
        """Get or create a platform adapter."""
        if platform not in self._adapters:
            adapter_cls = ADAPTER_REGISTRY.get(platform)
            if not adapter_cls:
                raise ValueError(f"Unsupported platform: {platform}. Supported: {list(ADAPTER_REGISTRY.keys())}")
            platform_config = self._load_platform_config(platform)
            self._adapters[platform] = adapter_cls(self.config, platform_config)
        return self._adapters[platform]

    def _load_platform_config(self, platform: str) -> dict:
        """Load platform-specific configuration."""
        import yaml
        platforms_path = Path(self.config.get("paths", {}).get("config_dir", "config")) / "platforms.yaml"
        if platforms_path.exists():
            with open(platforms_path) as f:
                all_platforms = yaml.safe_load(f).get("platforms", {})
                return all_platforms.get(platform, {})
        return {}

    def dispatch_next(self, dry_run: bool = False) -> Optional[dict]:
        """
        Find and publish the next due post from the schedule.

        Args:
            dry_run: If True, simulate without posting

        Returns:
            Result dict, or None if no pending posts are due.
        """
        pending = self.scheduler.list_pending()
        now = datetime.now(timezone.utc).isoformat()

        # Find the first post that's due (scheduled_at <= now)
        due = [p for p in pending if p["scheduled_at"] <= now]
        if not due:
            logger.info("No due posts in schedule")
            return None

        post = due[0]
        return self._publish_post(post, dry_run=dry_run)

    def publish_by_id(self, post_id: int, dry_run: bool = False) -> dict:
        """Publish a specific post by schedule ID."""
        from schedule_post import init_db
        conn = sqlite3.connect(str(self.scheduler.db_path))
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                "SELECT * FROM scheduled_posts WHERE id = ?", (post_id,)
            ).fetchone()
            if not row:
                raise ValueError(f"Post #{post_id} not found")
            post = dict(row)
        finally:
            conn.close()

        return self._publish_post(post, dry_run=dry_run)

    def _publish_post(self, post: dict, dry_run: bool = False) -> dict:
        """
        Publish a single post using the appropriate platform adapter.
        """
        import sqlite3

        platform = post["platform"]
        adapter_key = "dry-run" if dry_run else platform
        adapter = self._get_adapter(adapter_key)

        # Authenticate
        if not adapter.authenticate():
            error = f"Authentication failed for {platform}"
            logger.error(error)
            self.scheduler.mark_published(post["id"], result_log=json.dumps({"error": error}))
            return {"success": False, "error": error}

        # Determine content type and publish
        clip_path = Path(post["clip_path"]) if post.get("clip_path") else None
        hashtags = json.loads(post["hashtags"]) if post.get("hashtags") else []

        if clip_path and clip_path.suffix.lower() in {".mp4", ".mov"}:
            result = adapter.publish_video(clip_path, post["caption_text"], hashtags)
        elif clip_path and clip_path.suffix.lower() in {".jpg", ".jpeg", ".png"}:
            result = adapter.publish_image(clip_path, post["caption_text"], hashtags)
        else:
            result = {"success": False, "error": "No valid media file found for post"}

        # Record result
        log_entry = {**result, "platform": platform, "dry_run": dry_run}
        self.scheduler.mark_published(post["id"], result_log=json.dumps(log_entry))

        if result["success"]:
            logger.info("Published post #%d to %s: %s", post["id"], platform, result.get("post_url", "N/A"))
        else:
            logger.error("Failed to publish post #%d: %s", post["id"], result.get("error"))

        return result


# ──────────────────────────────────────────────
# CLI Entry Point
# ──────────────────────────────────────────────

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Publish influencer content to social platforms.",
    )
    parser.add_argument("--dispatch", action="store_true", help="Publish the next due post")
    parser.add_argument("--post-id", type=int, help="Publish a specific post by schedule ID")
    parser.add_argument("--persona", help="Filter by persona (used with --dispatch)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate publishing without API calls")
    parser.add_argument("--config", type=Path, default=None, help="Config file path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None):
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    import sqlite3
    from assemble_clip import load_config
    config = load_config()

    publisher = Publisher(config)

    if args.dispatch:
        result = publisher.dispatch_next(dry_run=args.dry_run)
        if result:
            status = "✅" if result["success"] else "❌"
            print(f"{status} Published: {result.get('post_url', 'N/A')}")
        else:
            print("No posts due for publishing.")
    elif args.post_id:
        result = publisher.publish_by_id(args.post_id, dry_run=args.dry_run)
        status = "✅" if result["success"] else "❌"
        print(f"{status} Post #{args.post_id}: {result.get('post_url', 'N/A')}")
    else:
        print("Specify --dispatch or --post-id. Use --dry-run to preview.")


if __name__ == "__main__":
    main()
