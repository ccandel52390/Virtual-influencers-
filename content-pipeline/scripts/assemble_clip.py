#!/usr/bin/env python3
"""
VirtuAI Content Pipeline — Video Clip Assembly
================================================

Composes short-form video clips from source assets for social media platforms.
Applies Nova Chen's brand identity: Neon Amethyst + Electric Cyan + Void Black palette,
Orbitron/Inter/Space Mono typography, and signature lighting overlays.
Supports batch processing for multi-platform variants.

Usage:
    python scripts/assemble_clip.py \\
        --persona "nova-chen" \\
        --input path/to/assets/ \\
        --platform tiktok \\
        --output output/clips/
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "default.yaml"


def load_config(path: Optional[Path] = None) -> dict:
    """Load pipeline configuration from YAML file."""
    import yaml
    path = path or DEFAULT_CONFIG_PATH
    with open(path, "r") as f:
        return yaml.safe_load(f)


# ──────────────────────────────────────────────
# Clip Assembly
# ──────────────────────────────────────────────

class ClipAssembler:
    """
    Assembles short-form video clips from source media assets.

    Applies Nova Chen's brand identity to every clip:
    - Color palette: Neon Amethyst (#9B59B6), Electric Cyan (#00E5FF), Void Black (#0A0A0A)
    - Typography: Orbitron (headlines), Inter (body), Space Mono (accent)
    - Signature lighting: warm amber right rim (#D4735E) + cool cyan left rim (#00E5FF)
    - Watermark: "NOVA CHEN" in Space Mono, 40% opacity

    In production this wraps FFmpeg or a Python video editing library (e.g., MoviePy / ffmpeg-python).
    The skeleton below defines the interface and data flow.
    """

    # Nova Chen brand identity constants
    BRAND = {
        "name": "NOVA CHEN",
        "alias": "The Neon Oracle",
        "colors": {
            "void_black": "#0A0A0A",
            "neon_amethyst": "#9B59B6",
            "electric_cyan": "#00E5FF",
            "warm_pearl": "#F5F0EB",
            "copper_ember": "#D4735E",
        },
        "fonts": {
            "headline": "Orbitron",
            "body": "Inter",
            "accent": "Space Mono",
        },
        "lighting": {
            "key_color": "#D4735E",    # warm amber right
            "rim_color": "#00E5FF",    # cool cyan left
        },
        "watermark": {
            "text": "NOVA CHEN",
            "font": "Space Mono",
            "opacity": 0.4,
        },
        "bumper_duration_sec": 1.5,
    }

    def __init__(self, config: dict):
        self.config = config
        self.encoding = config.get("encoding", {})
        self.branding = config.get("branding", {})
        logger.info("ClipAssembler initialized with Nova Chen brand identity")

    def assemble(
        self,
        input_dir: Path,
        platform: str,
        persona: str,
        output_path: Path,
        aspect_ratio: str = "9:16",
        duration: Optional[int] = None,
    ) -> Path:
        """
        Compose a single short-form clip with Nova's brand identity.

        Args:
            input_dir: Directory containing source media assets
            platform: Target platform key (e.g., "tiktok", "instagram")
            persona: Influencer persona identifier (e.g., "nova-chen")
            output_path: Destination file path
            aspect_ratio: Target aspect ratio string (e.g., "9:16", "1:1")
            duration: Target duration in seconds (None = auto-detect)

        Returns:
            Path to the assembled clip file.
        """
        # --- Stage 1: Load assets ---------------------------------
        logger.info("Scanning assets in %s for Nova Chen (%s)", input_dir, persona)
        assets = self._discover_assets(input_dir)

        if not assets:
            raise FileNotFoundError(f"No media assets found in {input_dir}")

        # --- Stage 2: Determine composition -----------------------
        brand_colors = self.BRAND["colors"]
        logger.info(
            "Composing clip: persona=%s platform=%s aspect=%s "
            "brand_colors=%s",
            persona, platform, aspect_ratio,
            f"{brand_colors['neon_amethyst']}/{brand_colors['electric_cyan']}",
        )
        clip_params = self._calculate_composition(
            assets, aspect_ratio, duration
        )

        # Add Nova brand overlay parameters
        clip_params["brand"] = {
            "watermark": self.BRAND["watermark"],
            "color_overlay": brand_colors["neon_amethyst"],
            "font_headline": self.BRAND["fonts"]["headline"],
            "font_body": self.BRAND["fonts"]["body"],
        }

        # --- Stage 3: Render --------------------------------------
        logger.info("Rendering clip to %s with Nova brand overlay", output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # TODO: Replace with FFmpeg / MoviePy call applying:
        #   - Nova's watermark ("NOVA CHEN" in Space Mono, 40% opacity, lower-third)
        #   - Intro bumper with neon amethyst ring animation (1.5s)
        #   - Color grade with warm amber key + cool cyan rim lighting
        #   - Title cards in Orbitron Bold, body in Inter
        self._render(assets, clip_params, output_path)

        logger.info(
            "Clip assembled: %s (%.1f sec) — Nova Chen branding applied",
            output_path, clip_params["duration_sec"],
        )
        return output_path

    def batch_assemble(
        self,
        input_dir: Path,
        platforms: list[str],
        persona: str,
        output_dir: Path,
    ) -> dict[str, Path]:
        """
        Assemble clips for multiple platforms from the same source assets.
        Each clip gets Nova's brand identity applied per platform specs.

        Returns:
            Dict mapping platform name -> clip file path.
        """
        results = {}
        for platform in platforms:
            out_path = output_dir / f"{persona}_{platform}.mp4"
            result = self.assemble(input_dir, platform, persona, out_path)
            results[platform] = result
        return results

    # ── Private helpers ───────────────────────────────────────────

    def _discover_assets(self, directory: Path) -> list[Path]:
        """Return sorted list of supported media files in directory."""
        SUPPORTED_EXTENSIONS = {".mp4", ".mov", ".avi", ".png", ".jpg", ".jpeg"}
        assets = sorted(
            p for p in directory.iterdir()
            if p.suffix.lower() in SUPPORTED_EXTENSIONS
        )
        logger.debug("Discovered %d assets", len(assets))
        return assets

    def _calculate_composition(
        self, assets: list[Path], aspect_ratio: str, duration: Optional[int]
    ) -> dict:
        """Determine clip structure (timeline, transitions, overlay positions)."""
        # Parse aspect ratio
        w_str, h_str = aspect_ratio.split(":")
        ratio = float(w_str) / float(h_str)

        # Default duration if not specified
        max_dur = self.encoding.get("max_duration_sec", 60)
        dur = duration if duration else min(len(assets) * 5, max_dur)

        return {
            "aspect_ratio": aspect_ratio,
            "ratio": ratio,
            "duration_sec": dur,
            "asset_count": len(assets),
            "resolution": self._target_resolution(ratio),
        }

    def _target_resolution(self, ratio: float) -> tuple[int, int]:
        """Return (width, height) matching aspect ratio at 1080p height."""
        height = 1080
        width = int(height * ratio)
        # Ensure even dimensions for codec
        return (width // 2 * 2, height // 2 * 2)

    def _render(self, assets: list[Path], params: dict, output_path: Path):
        """Execute the render pipeline with Nova's brand identity."""
        # Placeholder: create a minimal valid file for testing
        brand_name = self.BRAND["name"]
        brand_color = self.BRAND["colors"]["neon_amethyst"]
        logger.info(
            "Render pipeline executed (placeholder) — "
            "would apply %s branding with %s color overlay",
            brand_name, brand_color,
        )
        # In production: FFmpeg subprocess with:
        #   - drawtext filter for "NOVA CHEN" watermark (Space Mono, 40% opacity)
        #   - colorbalance for warm/cool dual lighting
        #   - ass filter for Orbitron title cards
        #   - ColorMatrix / colortransfer for Void Black grade


# ──────────────────────────────────────────────
# CLI Entry Point
# ──────────────────────────────────────────────

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Assemble a short-form video clip for an AI influencer.",
    )
    parser.add_argument("--persona", default="nova-chen", help="Influencer persona ID")
    parser.add_argument("--input", "-i", required=True, type=Path, help="Source assets directory")
    parser.add_argument("--platform", required=True, help="Target platform key")
    parser.add_argument("--output", "-o", type=Path, default=None, help="Output file path")
    parser.add_argument("--aspect-ratio", default="9:16", help="Target aspect ratio (e.g., 9:16, 1:1)")
    parser.add_argument("--duration", type=int, default=None, help="Target duration in seconds")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH, help="Config file path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None):
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    config = load_config(args.config)
    assembler = ClipAssembler(config)

    output = args.output or Path(config["paths"]["clips_dir"]) / f"{args.persona}_{args.platform}.mp4"

    assembler.assemble(
        input_dir=args.input,
        platform=args.platform,
        persona=args.persona,
        output_path=output,
        aspect_ratio=args.aspect_ratio,
        duration=args.duration,
    )


if __name__ == "__main__":
    main()
