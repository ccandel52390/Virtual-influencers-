# VirtuAI Content Pipeline — Development Plan

> **Persona target:** Nova Chen ("The Neon Oracle")
> **Brand guide:** `/home/team/shared/influencer-persona/01-brand-style-guide.md`

## Overview

The VirtuAI Content Pipeline ingests raw media assets and persona configuration, then creates, formats, schedules, and publishes short-form social media content — fully autonomously. This document breaks down the four major modules and their implementation roadmap.

---

## Module 1: Clip Generation (Video Assembly)

**Purpose:** Compose short-form video clips from source assets (images, video clips, audio) ready for social platforms.

### What It Does
- Ingests raw assets from a content brief (photos, B-roll, audio tracks)
- Stitches clips with transitions, text overlays, and background music
- Crops/resizes to platform-specific aspect ratios (9:16 TikTok, 1:1 Instagram, 16:9 YouTube)
- Adds Nova's signature visual branding: **Neon Amethyst (#9B59B6)** titles, **Electric Cyan (#00E5FF)** accents, **Void Black (#0A0A0A)** backgrounds
- Outputs ready-to-upload MP4 files

### Implementation Steps
| # | Step | Dependencies |
|---|------|-------------|
| 1 | Define `ClipAssembler` class with config-driven pipeline | config/default.yaml |
| 2 | Implement asset discovery (scan directory for supported formats) | — |
| 3 | Implement aspect-ratio cropping / padding logic | config/platforms.yaml |
| 4 | Add text overlay rendering (title, caption burn-in) | Pillow / ImageMagick |
| 5 | Wire in FFmpeg for final MP4 encoding with branding overlay | FFmpeg |
| 6 | Add batch mode: generate one clip per target platform from same assets | — |
| 7 | Add dry-run preview mode | — |

### Nova-Specific Details
- Overlay font: **Orbitron Bold** for headlines, **Inter** for body text
- Signature lighting overlay: warm amber `#D4735E` right rim + cool cyan `#00E5FF` left rim
- Lower-third watermark: "NOVA CHEN" in Space Mono, opacity 40%
- Default intro bumper: 1.5s animated neon ring motif

### Files
- `scripts/assemble_clip.py` — clip assembly orchestrator
- `templates/video_overlay/` — overlay configuration templates

---

## Module 2: Caption & Script Generation

**Purpose:** Generate platform-optimised captions, hashtags, and (optionally) voice-over scripts in Nova's distinctive brand voice.

### What It Does
- Accepts a content topic/brief and target platform
- Loads Nova's brand voice profile from the persona database
- Picks a caption template matching the content pillar (streetwear, tech, philosophy, community)
- Fills template with topic-specific content
- Generates relevant hashtags (3-5 per post, Nova's primary + secondary sets)
- Returns multiple A/B variants for testing

### Implementation Steps
| # | Step | Dependencies |
|---|------|-------------|
| 1 | Define `CaptionGenerator` class with persona-aware pipeline | persona config |
| 2 | Implement YAML caption template system with variable interpolation | — |
| 3 | Create Nova-specific templates for each content pillar (see below) | brand-style-guide.md |
| 4 | Implement hashtag generation from Nova's primary/secondary strategy | — |
| 5 | Add A/B variant generation (different hooks, structures) | — |
| 6 | Add preview mode that prints rendered captions | — |
| 7 | Wire in LLM API for dynamic content generation (future) | OpenAI / Anthropic |

### Nova's Caption Templates (4 Pillars)

**Streetwear Futurism (OOTD/Style):**
```
[1-2 line hook about the outfit or vibe]

Details on this look:
→ Jacket: [brand / "digital render"]
→ Pants: [brand]
→ Shoes: [brand]

[1 line attitude / philosophy]

#NeonOracle #[pillar hashtag]
```

**Tech Meets Fashion (Review/Commentary):**
```
[Hot take or surprising observation]

The thing nobody tells you about [product]:
→ [Point 1]
→ [Point 2]
→ [Point 3]

[Closing verdict — 5 words or less]

#NeonOracle #TechFashion
```

**Digital Philosophy (Viral Thought):**
```
[Mood-setting observation about digital life]

[2-3 sentences expanding the thought]

—

[Resonant closing line or question]

#NeonOracle #DigitalThoughts
```

**Community Interaction:**
```
[Engagement hook / question]

[Context or setup — 1-2 lines]

Drop your take below 👇

#NeonOracle #VirtualVibe
```

### Files
- `scripts/generate_caption.py` — caption generation orchestrator
- `templates/caption_templates/*.yaml` — pillar-specific templates

---

## Module 3: Scheduling & Posting System

**Purpose:** Manage a content calendar, schedule posts at optimal times, queue them, and dispatch to social platforms.

### What It Does
- Maintains a SQLite database of scheduled posts (persona, platform, clip path, caption, scheduled time, status)
- Enforces frequency limits (per platform per day)
- Picks optimal posting windows from platform profiles
- Exposes a queue that the publisher can consume
- Allows listing, rescheduling, cancelling posts

### Implementation Steps
| # | Step | Dependencies |
|---|------|-------------|
| 1 | Define SQLite schema for `scheduled_posts` table | — |
| 2 | Implement `Scheduler` class with CRUD operations | — |
| 3 | Implement frequency cap enforcement (max posts/day, min gap) | config/schedule |
| 4 | Implement "best time" algorithm per platform | config/platforms.yaml |
| 5 | Add `--list`, `--flush`, `--post-id` CLI commands | — |
| 6 | Add `mark_published()` status tracking | — |
| 7 | Integrate with Nova's posting cadence (1-2 posts/day per platform) | Nova persona config |

### Scheduling Rules (from Nova's Brand Guide)
- **TikTok:** 1-2 posts/day, best window 12:00-20:00 UTC
- **Instagram:** 1 post/day, best window 09:00-21:00 UTC
- **YouTube Shorts:** 1 post/day, best window 14:00-22:00 UTC
- Minimum 4 hours between posts on same platform
- Peak engagement: Thursday-Sunday evenings

### Files
- `scripts/schedule_post.py` — scheduler with SQLite persistence

---

## Module 4: Engagement Tracking

**Purpose:** Monitor post performance across platforms and feed engagement data back into the pipeline to improve content.

### What It Does
- After publishing, polls platform APIs for post metrics (views, likes, shares, comments, saves)
- Stores engagement data in the shared team database
- Calculates key KPIs: viral hit rate, engagement rate, follower growth
- Flags high-performing content for amplification (repost / boost)
- Feeds engagement trends into caption generation (what hooks work)

### Implementation Steps
| # | Step | Dependencies |
|---|------|-------------|
| 1 | Define `EngagementTracker` class with platform data-fetch interface | platform APIs |
| 2 | Implement metric polling per platform (TikTok Analytics, Instagram Insights, etc.) | OAuth + API access |
| 3 | Store engagement data in shared team-db database | team-db |
| 4 | Calculate KPIs: viral hit rate (>5% engagement = viral), engagement rate, follower growth | — |
| 5 | Implement engagement dashboard / report generator | — |
| 6 | Feed top-performing hooks back into caption generation as "winning patterns" | — |

### KPIs (from Business Plan)
- **Viral hit rate** — % of posts exceeding defined engagement thresholds
- **Follower growth rate** — net new followers per AI influencer per month
- **Engagement rate** — (likes + comments + shares + saves) / followers per post

### Files
- `scripts/track_engagement.py` — engagement tracker (to be created)
- `config/engagement.yaml` — engagement thresholds and polling intervals (to be created)

---

## Integration Architecture

```
┌───────────────┐     ┌──────────────────┐     ┌───────────────┐
│  Nova's       │────▶│  Caption Gen     │────▶│  Schedule     │
│  Persona DB   │     │  (generate_      │     │  (schedule_   │
│  (team-db)    │     │   caption.py)    │     │   post.py)    │
└───────────────┘     └──────────────────┘     └───────┬───────┘
                                                        │
┌───────────────┐     ┌──────────────────┐              │
│  Media Assets │────▶│  Clip Assembly   │──────────────┘
│  (images/vid) │     │  (assemble_      │
│               │     │   clip.py)       │
└───────────────┘     └──────────────────┘              │
                                                        ▼
┌───────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Platform     │◀────│  Engagement      │◀────│  Publisher       │
│  APIs         │     │  Tracker         │     │  (publish.py)    │
│  (TikTok, IG) │     │  (track_engage..)│     │                  │
└───────────────┘     └──────────────────┘     └──────────────────┘
```

---

## Implementation Order

| Phase | Modules | Goal |
|-------|---------|------|
| **Phase 1** (current) | Skeleton + config + templates | Scaffold ready for coding |
| **Phase 2** | Clip assembly (real FFmpeg integration) | Can produce actual video clips |
| **Phase 3** | Caption generation + LLM integration | Can write Nova-voiced copy |
| **Phase 4** | Scheduling + posting database | Can manage a content calendar |
| **Phase 5** | Multi-platform publishing | Can post to TikTok, IG, YT Shorts |
| **Phase 6** | Engagement tracking + KPI reporting | Can measure and improve performance |

---

*Plan v1.0 — Updated for Nova Chen "The Neon Oracle" persona*
