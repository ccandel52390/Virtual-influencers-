#!/usr/bin/env python3
"""
VirtuAI Content Pipeline — Caption Generation
===============================================

Creates platform-optimised captions for AI influencer posts. Uses caption
templates, persona voice guidelines, and context to craft engaging copy.
Supports A/B variant generation and automatic hashtag creation.

Usage:
    python scripts/generate_caption.py \\
        --persona "luna-ai" \\
        --topic "summer skincare tips" \\
        --platform instagram \\
        --preview

    python scripts/generate_caption.py \\
        --persona "luna-ai" \\
        --topic "tech unboxing" \\
        --platform tiktok \\
        --output data/output/captions/
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Template Loading
# ──────────────────────────────────────────────

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates" / "caption_templates"


def load_template(template_name: str) -> dict:
    """Load a caption template from YAML."""
    import yaml
    path = TEMPLATES_DIR / f"{template_name}.yaml"
    if not path.exists():
        logger.warning("Template '%s' not found, using default", template_name)
        path = TEMPLATES_DIR / "default.yaml"
    with open(path, "r") as f:
        return yaml.safe_load(f)


# ──────────────────────────────────────────────
# Caption Generation
# ──────────────────────────────────────────────

class CaptionGenerator:
    """
    Generates platform-optimised captions for AI influencer content.

    Uses Nova Chen's 4 content pillars as template categories:
    - Streetwear Futurism (40%)  → templates/caption_templates/streetwear.yaml
    - Tech Meets Fashion (25%)   → templates/caption_templates/tech.yaml
    - Digital Philosophy (20%)   → templates/caption_templates/philosophy.yaml
    - Community Interaction (15%) → templates/caption_templates/community.yaml

    Each template captures Nova's brand voice: witty, confident, self-aware,
    with sparing emoji usage (🌙 🔥 ✦ ⚡) and max 3-5 hashtags per post.

    In production this calls an LLM API (OpenAI/Anthropic) with Nova's
    voice profile as system context. The skeleton below defines the
    interface and templating pipeline.
    """

    def __init__(self, config: dict):
        self.config = config
        self.caption_cfg = config.get("caption", {})
        self._persona_cache: dict[str, dict] = {}

    def generate(
        self,
        persona: str,
        topic: str,
        platform: str,
        template_name: str = "default",
        ab_variant: int = 0,
    ) -> dict:
        """
        Generate a caption for a post.

        Args:
            persona: Influencer persona identifier
            topic: Content topic/keyword
            platform: Target platform key
            template_name: Caption template to use
            ab_variant: A/B variant index (0 = primary)

        Returns:
            Dict with keys: caption, hashtags, metadata
        """
        persona_profile = self._get_persona(persona)
        template = load_template(template_name)

        # Build the caption from template + persona data
        caption = self._compose(
            template=template,
            persona=persona_profile,
            topic=topic,
            platform=platform,
            variant=ab_variant,
        )

        # Generate hashtags (use template-specified set, fall back to "primary")
        hashtag_set = template.get("hashtag_set", "primary")
        hashtags = self._generate_hashtags(
            topic=topic,
            persona=persona_profile,
            platform=platform,
            template_hashtag_set=hashtag_set,
        )

        result = {
            "caption": caption,
            "hashtags": hashtags,
            "metadata": {
                "persona": persona,
                "platform": platform,
                "topic": topic,
                "template": template_name,
                "variant": ab_variant,
                "char_count": len(caption),
            },
        }
        return result

    def generate_variants(
        self,
        persona: str,
        topic: str,
        platform: str,
        template_name: str = "default",
        n: int = 2,
    ) -> list[dict]:
        """Generate N A/B caption variants for the same post."""
        return [
            self.generate(persona, topic, platform, template_name, ab_variant=i)
            for i in range(n)
        ]

    # ── Private helpers ───────────────────────────────────────────

    def _get_persona(self, persona_id: str) -> dict:
        """Fetch persona profile — from cache or shared database."""
        if persona_id not in self._persona_cache:
            # TODO: Load from team database via team-db CLI
            # Default to Nova Chen "The Neon Oracle" profile
            self._persona_cache[persona_id] = {
                "id": persona_id,
                "name": "Nova Chen",
                "alias": "The Neon Oracle",
                "voice_tone": "witty, confident, self-aware, conversational",
                "emoji_style": "sparing — 🌙 🔥 ✦ ⚡",
                "brand_hashtags": ["#NeonOracle", "#AIFashion", "#DigitalIdentity"],
                "hashtag_sets": {
                    "primary": ["#NeonOracle", "#AIFashion", "#DigitalIdentity"],
                    "streetwear": ["#StreetwearFuture", "#CyberStyle", "#NeonOracle"],
                    "tech": ["#TechMeetsFashion", "#VirtualVibe", "#NeonOracle"],
                    "philosophy": ["#DigitalThoughts", "#NeonOracle", "#AIConsciousness"],
                    "community": ["#VirtualVibe", "#NeonOracle", "#RateMyFit"],
                },
            }
        return self._persona_cache[persona_id]

    def _compose(
        self,
        template: dict,
        persona: dict,
        topic: str,
        platform: str,
        variant: int = 0,
    ) -> str:
        """
        Compose a caption string from a template and persona data.

        Template structure example:
            intro: "Hey besties! 💕"
            body_template: "Today we're talking about {topic}..."
            outro: "What do you think? Drop a comment below! 👇"
            cta: "Follow for more {persona_topic} content!"
        """
        intro = template.get("intro", "")
        body_template = template.get("body_template", "Let's talk about {topic}!")
        outro = template.get("outro", "")
        cta = template.get("cta", "")

        # Fill in template variables
        body = body_template.format(
            topic=topic,
            persona_name=persona.get("name", ""),
            persona_topic=persona.get("topic", topic),
        )

        # Assemble and cap character length
        full = f"{intro}\n\n{body}\n\n{outro}\n\n{cta}"
        max_chars = self.caption_cfg.get("max_length", 2200)
        if len(full) > max_chars:
            full = full[:max_chars].rsplit(" ", 1)[0] + "..."

        return full.strip()

    def _generate_hashtags(
        self, topic: str, persona: dict, platform: str,
        template_hashtag_set: str = "primary",
    ) -> list[str]:
        """
        Generate a list of relevant hashtags.

        Uses the persona's tiered hashtag sets (from Nova's brand guide):
        - Primary set always included (#NeonOracle, #AIFashion, #DigitalIdentity)
        - Secondary set depends on content pillar (streetwear, tech, philosophy, community)
        - Topic-derived tags as supplementary

        Nova's rule: max 3-5 hashtags per post, always on a separate line.
        """
        # Start with pillar-specific set if available
        hashtag_sets = persona.get("hashtag_sets", {})
        pillar_tags = hashtag_sets.get(template_hashtag_set, [])

        # Fall back to brand defaults
        brand_tags = persona.get("brand_hashtags", [])

        # Derive topic tags from key words (supplementary)
        topic_words = topic.lower().replace(",", " ").split()
        topic_tags = [f"#{w}" for w in topic_words if len(w) > 2]

        # Priority: pillar tags first, then brand, then topic-derived
        # De-duplicate preserving order
        all_tags = list(dict.fromkeys(pillar_tags + brand_tags + topic_tags))

        # Nova's rule: max 3-5 hashtags per post
        limit = self.caption_cfg.get("hashtag_limit", 5)
        return all_tags[:limit]


# ──────────────────────────────────────────────
# CLI Entry Point
# ──────────────────────────────────────────────

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate captions for AI influencer posts.",
    )
    parser.add_argument("--persona", required=True, help="Influencer persona ID")
    parser.add_argument("--topic", required=True, help="Content topic or keyword")
    parser.add_argument("--platform", required=True, help="Target platform key")
    parser.add_argument("--template", default="default", help="Caption template name")
    parser.add_argument("--output", "-o", type=Path, default=None, help="Output directory for caption files")
    parser.add_argument("--preview", action="store_true", help="Print caption to stdout only")
    parser.add_argument("--variants", type=int, default=1, help="Number of A/B variants to generate")
    parser.add_argument("--config", type=Path, default=None, help="Config file path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None):
    args = parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    # Load config
    from assemble_clip import load_config
    config = load_config()

    generator = CaptionGenerator(config)

    if args.variants > 1:
        results = generator.generate_variants(
            persona=args.persona,
            topic=args.topic,
            platform=args.platform,
            template_name=args.template,
            n=args.variants,
        )
    else:
        results = [generator.generate(
            persona=args.persona,
            topic=args.topic,
            platform=args.platform,
            template_name=args.template,
        )]

    if args.preview:
        for i, r in enumerate(results):
            print(f"\n{'='*60}")
            print(f"Variant {i}  |  {r['metadata']['char_count']} chars")
            print(f"{'='*60}")
            print(r["caption"])
            if r["hashtags"]:
                print()
                print(" ".join(r["hashtags"]))
    elif args.output:
        args.output.mkdir(parents=True, exist_ok=True)
        for i, r in enumerate(results):
            out_path = args.output / f"{args.persona}_{args.platform}_v{i}.json"
            with open(out_path, "w") as f:
                json.dump(r, f, indent=2)
            logger.info("Caption written to %s", out_path)


if __name__ == "__main__":
    main()
