# VirtuAI Content Pipeline

The content pipeline is the engine behind VirtuAI Influencers — it **creates, formats, schedules, and publishes** AI influencer content across multiple social platforms. All operations are fully automated and designed for scale.

## Active Persona: Nova Chen — "The Neon Oracle"

This pipeline is **fully configured** for **Nova Chen**, an AI-born virtual influencer at the intersection of **streetwear fashion, tech culture, and digital philosophy**. See her complete brand guide at:

📁 [`/home/team/shared/influencer-persona/01-brand-style-guide.md`](/home/team/shared/influencer-persona/01-brand-style-guide.md)

### Configuration Status ✅

| Component | File | Nova Integration |
|---|---|---|
| **Persona Profile** | `config/nova-chen.yaml` | Full brand identity: voice, colors, typography, hashtag strategy, posting cadence |
| **Default Config** | `config/default.yaml` | Default persona set to `nova-chen`, brand overlay colors and fonts configured |
| **Clip Assembly** | `scripts/assemble_clip.py` | `BRAND` constant with Nova's colors (#9B59B6, #00E5FF, #0A0A0A), typography (Orbitron, Inter, Space Mono), watermark ("NOVA CHEN"), signature lighting |
| **Caption Generation** | `scripts/generate_caption.py` | 4 pillar templates mapped to Nova's content categories; hashtag sets per pillar; persona defaults loaded from config |
| **Caption Templates** | `templates/caption_templates/` | 5 templates: default, streetwear, tech, philosophy, community — each written in Nova's brand voice |
| **Scheduling** | `scripts/schedule_post.py` | Enforces Nova's posting cadence (1-2 posts/day per platform, 4hr min gap) |

For the full development roadmap, see [`plan.md`](./plan.md).

## Architecture

```
                        ┌──────────────────┐
                        │  Nova's Persona   │
                        │  DB (team-db)     │
                        └────────┬─────────┘
                                 │
┌──────────────┐    ┌───────────▼───────────┐    ┌──────────────┐
│  Media Assets │───▶│  assemble_clip.py     │───▶│  captions/    │
│  (images,     │    │  (video clip assembly)│    │  (generated   │
│   video src)  │    └───────────────────────┘    │   text+meta)  │
└──────────────┘                                   └──────┬───────┘
                                                           │
┌──────────────┐    ┌───────────────────────┐              │
│  Caption     │───▶│  generate_caption.py  │──────────────┘
│  Templates   │    │  (AI caption gen)     │
└──────────────┘    └───────────────────────┘
                                                           │
                                                           ▼
┌──────────────┐    ┌───────────────────────┐    ┌──────────────────┐
│  Schedule    │───▶│  schedule_post.py     │───▶│  schedule.db     │
│  Config      │    │  (timeline manager)   │    │  (post queue)    │
└──────────────┘    └───────────────────────┘    └────────┬─────────┘
                                                           │
                                                           ▼
┌──────────────┐    ┌───────────────────────┐    ┌──────────────────┐
│  Platform    │───▶│  publish.py           │───▶│  Social APIs     │
│  Credentials │    │  (multi-platform pub) │    │  (TikTok, IG, X) │
└──────────────┘    └───────────────────────┘    └──────────────────┘
```

### Modules

| Module | File | Responsibility |
|---|---|---|
| **Assemble Clip** | `scripts/assemble_clip.py` | Composes short-form video clips from source assets; handles trimming, transitions, overlay text, aspect ratio resizing, and output encoding — renders Nova's signature neon branding overlays |
| **Generate Caption** | `scripts/generate_caption.py` | Creates platform-optimised captions from Nova's 4 content pillars (streetwear, tech, philosophy, community); supports A/B variants and hashtag generation per brand guide |
| **Schedule Post** | `scripts/schedule_post.py` | Manages a post queue with timing rules, frequency caps, and platform-specific best-time posting; persists schedule to SQLite |
| **Publish** | `scripts/publish.py` | Authenticates to social platforms and publishes content with correct formats, alt text, and metadata; logs results |
| **Engagement Tracking** | `scripts/track_engagement.py` *(planned)* | Polls platform APIs for post metrics and feeds KPI data back into the pipeline |

### Data Flow

1. **Input**: Media assets (images, video clips) + Nova's persona config + content brief
2. **Assembly**: `assemble_clip.py` stitches raw assets into platform-ready short-form clips with Nova's Neon Oracle branding
3. **Captioning**: `generate_caption.py` crafts captions in Nova's witty, self-aware, fashion-forward voice
4. **Scheduling**: `schedule_post.py` slots the post into a calendar respecting frequency rules (1-2 posts/day per platform)
5. **Publishing**: `publish.py` delivers the post to target platforms and records results

### Config System

All pipeline behaviour is driven by YAML config files in `config/`:

- **`default.yaml`**: Core pipeline settings (output dirs, encoding, retry limits, caption defaults)
- **`platforms.yaml`**: Per-platform profiles (aspect ratios, length limits, posting rules for TikTok, Instagram, X, YouTube Shorts)

Persona-specific overrides are loaded at runtime from the shared team database.

## Getting Started

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
make test

# Preview a Nova caption
python scripts/generate_caption.py --persona "nova-chen" --topic "cyberpunk streetwear" --platform tiktok --preview

# Schedule a post
python scripts/schedule_post.py --persona "nova-chen" --platform tiktok --caption path/to/caption.json --clip path/to/clip.mp4

# List scheduled posts
python scripts/schedule_post.py --list
```

## Directory Structure

```
content-pipeline/
├── README.md                # This file
├── plan.md                  # Detailed development plan & module breakdown
├── Makefile                 # Common tasks
├── requirements.txt         # Python dependencies
├── config/
│   ├── default.yaml         # Core pipeline config
│   └── platforms.yaml       # Per-platform profiles
├── scripts/
│   ├── __init__.py
│   ├── assemble_clip.py     # Video clip assembly with Nova's branding
│   ├── generate_caption.py  # AI caption generation (4 pillar templates)
│   ├── schedule_post.py     # Post scheduling & SQLite queue
│   └── publish.py           # Multi-platform publishing (adapter pattern)
├── templates/
│   ├── caption_templates/   # Nova's pillar-based caption format templates
│   └── video_overlay/       # Overlay text/graphic templates
├── tests/                   # Unit and integration tests
├── data/
│   ├── output/              # Generated clips and captions
│   └── samples/             # Sample assets for testing
└── output/                  # Render output directory
```

## Nova Chen — Brand Integration

Nova's brand voice is infused throughout the pipeline:

| Brand Element | Pipeline Integration |
|---|---|
| **Tone** (witty, confident, self-aware) | Caption templates model her conversational, sharp style |
| **Content Pillars** (4 categories) | Each pillar has its own caption template in `templates/caption_templates/` |
| **Color Palette** (Neon Amethyst #9B59B6, Electric Cyan #00E5FF, Void Black #0A0A0A) | Video overlay configs reference brand colors for title cards, lower-thirds |
| **Typography** (Orbitron, Inter, Space Mono) | Specified in overlay templates for consistent branding |
| **Hashtag Strategy** (3-5 per post, primary + secondary sets) | `generate_caption.py` implements the tiered hashtag approach |
| **Posting Cadence** (1-2 posts/day per platform) | `schedule_post.py` enforces frequency rules from brand guide |

## Development

```bash
make test      # Run tests
make lint      # Lint scripts
make clean     # Remove generated content
```

## KPIs This Pipeline Supports

- **Viral hit rate** — tracks engagement per post after publishing
- **Follower growth rate** — publishing cadence drives growth
- **Engagement rate** — caption quality and timing affect engagement

These KPIs are measured by the **Engagement Tracking module** (Phase 6 in `plan.md`).