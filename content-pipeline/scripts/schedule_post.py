#!/usr/bin/env python3
"""
VirtuAI Content Pipeline — Post Scheduling
============================================

Manages the post queue with timing rules, frequency caps, and
platform-specific best-time posting. Persists schedule to a SQLite
database so it survives restarts.

Usage:
    python scripts/schedule_post.py \\
        --persona "luna-ai" \\
        --platform tiktok \\
        --caption data/output/captions/luna_tiktok_v0.json \\
        --clip data/output/clips/luna_ai_tiktok.mp4 \\
        --post-at "2026-06-22T14:00:00Z"

    python scripts/schedule_post.py --list
    python scripts/schedule_post.py --flush
"""

import argparse
import json
import logging
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Schedule Database
# ──────────────────────────────────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS scheduled_posts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    persona         TEXT NOT NULL,
    platform        TEXT NOT NULL,
    clip_path       TEXT,
    caption_path    TEXT,
    caption_text    TEXT,
    hashtags        TEXT,           -- JSON array
    scheduled_at    TEXT NOT NULL,  -- ISO-8601 UTC
    status          TEXT NOT NULL DEFAULT 'pending',
        -- status values: pending, published, failed, cancelled
    published_at    TEXT,
    result_log      TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_schedule_status ON scheduled_posts(status);
CREATE INDEX IF NOT EXISTS idx_schedule_at    ON scheduled_posts(scheduled_at);
"""


def init_db(db_path: Path):
    """Ensure the schedule database and tables exist."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()


# ──────────────────────────────────────────────
# Scheduler
# ──────────────────────────────────────────────

class Scheduler:
    """
    Manages the post queue, respecting frequency caps and timing rules.
    """

    def __init__(self, config: dict, db_path: Optional[Path] = None):
        self.config = config
        schedule_cfg = config.get("schedule", {})
        self.db_path = db_path or Path(config.get("paths", {}).get("schedule_db", "data/schedule.db"))
        init_db(self.db_path)

    def schedule(
        self,
        persona: str,
        platform: str,
        caption_data: dict,
        clip_path: Optional[Path] = None,
        post_at: Optional[str] = None,
    ) -> int:
        """
        Schedule a post for a specific time.

        Args:
            persona: Influencer persona ID
            platform: Target platform key
            caption_data: Caption dict (from generate_caption.py)
            clip_path: Path to assembled clip
            post_at: ISO-8601 datetime string (None = pick best time)

        Returns:
            Post ID in the schedule database.
        """
        # Determine posting time
        if post_at is None:
            post_at = self._pick_best_time(persona, platform)

        # Validate against frequency limits
        self._check_frequency_limits(persona, platform, post_at)

        # Insert into schedule
        conn = sqlite3.connect(str(self.db_path))
        try:
            cur = conn.execute(
                """
                INSERT INTO scheduled_posts
                    (persona, platform, clip_path, caption_path, caption_text, hashtags, scheduled_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
                """,
                (
                    persona,
                    platform,
                    str(clip_path) if clip_path else None,
                    caption_data.get("caption_path"),
                    caption_data.get("caption", ""),
                    json.dumps(caption_data.get("hashtags", [])),
                    post_at,
                ),
            )
            post_id = cur.lastrowid
            conn.commit()
            logger.info("Scheduled post #%d for %s on %s at %s", post_id, persona, platform, post_at)
            return post_id
        finally:
            conn.close()

    def list_pending(self, persona: Optional[str] = None) -> list[dict]:
        """List all pending posts, optionally filtered by persona."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            if persona:
                rows = conn.execute(
                    "SELECT * FROM scheduled_posts WHERE persona = ? AND status = 'pending' ORDER BY scheduled_at",
                    (persona,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM scheduled_posts WHERE status = 'pending' ORDER BY scheduled_at"
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def mark_published(self, post_id: int, result_log: str = ""):
        """Mark a scheduled post as published."""
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute(
                "UPDATE scheduled_posts SET status = 'published', published_at = datetime('now'), result_log = ? WHERE id = ?",
                (result_log, post_id),
            )
            conn.commit()
            logger.info("Post #%d marked as published", post_id)
        finally:
            conn.close()

    def flush_all(self, confirm: bool = False):
        """Delete all pending posts (for testing / manual override)."""
        if not confirm:
            print("Use --flush --confirm to delete all pending posts")
            return
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute("DELETE FROM scheduled_posts WHERE status = 'pending'")
            conn.commit()
            logger.info("All pending posts flushed")
        finally:
            conn.close()

    # ── Private helpers ───────────────────────────────────────────

    def _pick_best_time(self, persona: str, platform: str) -> str:
        """
        Pick the best available posting time based on platform rules
        and existing schedule density.
        """
        import random
        schedule_cfg = self.config.get("schedule", {})
        windows = schedule_cfg.get("best_time_window", {})
        platform_window = windows.get(platform, ["09:00", "17:00"])

        # Simple heuristic: pick next slot at a random minute within the window
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        # Start from tomorrow to allow time for preparation
        base = now + timedelta(days=1)
        hour_start, hour_end = [int(h.split(":")[0]) for h in platform_window]
        hour = random.randint(hour_start, hour_end)
        minute = random.randint(0, 59)
        best = base.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return best.isoformat()

    def _check_frequency_limits(self, persona: str, platform: str, post_at: str):
        """Raise if scheduling violates configured frequency limits."""
        schedule_cfg = self.config.get("schedule", {})
        max_per_day = schedule_cfg.get("max_posts_per_day", 3)
        min_gap = schedule_cfg.get("min_gap_minutes", 240)

        conn = sqlite3.connect(str(self.db_path))
        try:
            # Count posts on the same day
            day = post_at[:10]
            count = conn.execute(
                "SELECT COUNT(*) FROM scheduled_posts WHERE persona = ? AND platform = ? AND scheduled_at LIKE ?",
                (persona, platform, f"{day}%"),
            ).fetchone()[0]

            if count >= max_per_day:
                raise RuntimeError(
                    f"Frequency limit: {persona} already has {count} posts scheduled "
                    f"for {day} on {platform} (max: {max_per_day})"
                )
        finally:
            conn.close()


# ──────────────────────────────────────────────
# CLI Entry Point
# ──────────────────────────────────────────────

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Schedule influencer posts for publishing.",
    )
    parser.add_argument("--persona", help="Influencer persona ID")
    parser.add_argument("--platform", help="Target platform key")
    parser.add_argument("--caption", type=Path, help="Path to caption JSON file")
    parser.add_argument("--clip", type=Path, help="Path to assembled clip file")
    parser.add_argument("--post-at", help="ISO-8601 datetime (empty = auto-pick best time)")
    parser.add_argument("--list", action="store_true", help="List pending posts")
    parser.add_argument("--flush", action="store_true", help="Delete all pending posts")
    parser.add_argument("--confirm", action="store_true", help="Confirm destructive actions")
    parser.add_argument("--config", type=Path, default=None, help="Config file path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None):
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    from assemble_clip import load_config
    config = load_config()

    scheduler = Scheduler(config)

    if args.list:
        posts = scheduler.list_pending(persona=args.persona)
        if not posts:
            print("No pending posts.")
        for p in posts:
            print(f"  #{p['id']:>4}  {p['persona']:<16}  {p['platform']:<12}  {p['scheduled_at']:<22}  {p['status']}")
        return

    if args.flush:
        scheduler.flush_all(confirm=args.confirm)
        return

    # Schedule a new post
    if not all([args.persona, args.platform, args.caption]):
        print("Error: --persona, --platform, and --caption are required to schedule a post.")
        sys.exit(1)

    with open(args.caption) as f:
        caption_data = json.load(f)

    post_id = scheduler.schedule(
        persona=args.persona,
        platform=args.platform,
        caption_data=caption_data,
        clip_path=args.clip,
        post_at=args.post_at,
    )
    print(f"Scheduled post #{post_id}")


if __name__ == "__main__":
    main()
