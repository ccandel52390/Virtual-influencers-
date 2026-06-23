"""
Tests for the VirtuAI Content Pipeline.

Run with: pytest tests/ -v
"""

import json
import sys
import tempfile
from pathlib import Path


# Ensure scripts directory is importable
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))


class TestClipAssembly:
    """Tests for assemble_clip.py"""

    def test_load_config(self):
        """Config should load without errors."""
        from assemble_clip import load_config
        config = load_config()
        assert "pipeline" in config
        assert config["pipeline"]["name"] == "virtuai-content-pipeline"

    def test_assembler_init(self):
        """ClipAssembler should initialise from config."""
        from assemble_clip import ClipAssembler, load_config
        config = load_config()
        assembler = ClipAssembler(config)
        assert assembler.encoding.get("format") == "mp4"


class TestCaptionGeneration:
    """Tests for generate_caption.py"""

    def test_generate_caption(self):
        """Caption generation should return expected keys."""
        from generate_caption import CaptionGenerator
        from assemble_clip import load_config

        config = load_config()
        generator = CaptionGenerator(config)

        result = generator.generate(
            persona="luna-ai",
            topic="summer skincare",
            platform="instagram",
        )

        assert "caption" in result
        assert "hashtags" in result
        assert "metadata" in result
        assert result["metadata"]["persona"] == "luna-ai"
        assert result["metadata"]["platform"] == "instagram"
        assert isinstance(result["caption"], str)
        assert len(result["caption"]) > 0

    def test_generate_variants(self):
        """Should generate multiple A/B variants."""
        from generate_caption import CaptionGenerator
        from assemble_clip import load_config

        config = load_config()
        generator = CaptionGenerator(config)

        variants = generator.generate_variants(
            persona="luna-ai",
            topic="tech unboxing",
            platform="tiktok",
            n=3,
        )

        assert len(variants) == 3
        # Variants should have different indices
        indices = [v["metadata"]["variant"] for v in variants]
        assert indices == [0, 1, 2]


class TestScheduling:
    """Tests for schedule_post.py"""

    def test_init_db(self):
        """Database should initialise with correct schema."""
        from schedule_post import init_db

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            init_db(db_path)
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = [t[0] for t in tables]
            assert "scheduled_posts" in table_names
            conn.close()
        finally:
            db_path.unlink()

    def test_schedule_and_list(self):
        """Should schedule a post and list it as pending."""
        from schedule_post import Scheduler
        from assemble_clip import load_config

        config = load_config()

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            scheduler = Scheduler(config, db_path=db_path)

            caption_data = {
                "caption": "Test caption!",
                "hashtags": ["#test", "#virtuai"],
            }

            post_id = scheduler.schedule(
                persona="luna-ai",
                platform="tiktok",
                caption_data=caption_data,
                post_at="2026-12-25T12:00:00Z",
            )

            assert isinstance(post_id, int)
            assert post_id > 0

            pending = scheduler.list_pending()
            assert len(pending) >= 1
            assert pending[-1]["persona"] == "luna-ai"
            assert pending[-1]["platform"] == "tiktok"
        finally:
            db_path.unlink()


class TestPublishing:
    """Tests for publish.py"""

    def test_dry_run_adapter(self):
        """Dry-run adapter should simulate successfully."""
        from publish import DryRunAdapter

        adapter = DryRunAdapter(config={}, platform_config={})
        assert adapter.authenticate() is True

        result = adapter.publish_video(
            clip_path=Path("/tmp/test.mp4"),
            caption="Test",
            hashtags=["#test"],
        )
        assert result["success"] is True
        assert "dry" in result["platform_post_id"]

    def test_publisher_init(self):
        """Publisher should initialise without errors."""
        from publish import Publisher
        from assemble_clip import load_config

        config = load_config()
        publisher = Publisher(config)
        assert publisher is not None
