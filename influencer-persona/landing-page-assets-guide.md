# Nova Chen — Landing Page Visual Assets Guide

## Assets

| File | Size | Dimensions | Purpose |
|---|---|---|---|
| `hero-landing-page.png` | ~1.8 MB | 1536×1024 | Hero section background / full-width header |
| `social-banner.png` | ~1.8 MB | 1536×1024 | Social media / OG share image + portfolio site banner |

---

## 1. Hero Image (`hero-landing-page.png`)

### Visual Description
Nova Chen in full Neon Oracle aesthetic — standing confidently in a futuristic neon-lit cityscape at twilight. She wears her signature oversized techwear blazer with metallic accents, cargo pants, and chunky sneakers, with translucent smart glasses pushed up on her head. The background features a sprawling cyberpunk skyline with neon amethyst (#9B59B6) and electric cyan (#00E5FF) holographic billboards against a void-black (#0A0A0A) sky. Dual lighting signature: warm amber key from right, cool cyan rim from left.

### Recommended Usage
- **Full-width hero background** — stretched to fill viewport width, Nova positioned slightly off-center left
- **Dark overlay** — apply a subtle gradient overlay (void-black to transparent, left-to-right or bottom-to-top) if text goes over the image
- **Text pairing** — pair with Orbitron-bold headline ("NOVA CHEN") in neon amethyst, and Space Mono subtitle ("The Neon Oracle") in warm pearl (#F5F0EB)
- **Max height** — 80vh–100vh, with content centered over the darker areas of the image

### Technical Specs
- **Format:** PNG (can be converted to WebP for performance)
- **Aspect ratio:** 3:2 (landscape) — use `object-fit: cover` if cropping to a different ratio
- **Lighting notes:** The dark left side of the image is ideal for text overlay without competing with Nova's face

---

## 2. Social Banner (`social-banner.png`)

### Visual Description
Nova walking confidently toward camera through a futuristic neon-lit street at night. Purple and cyan light reflections on wet pavement create depth. Nova is positioned on the right third of the frame, leaving negative space on the left for text/logo overlay. Blurred city lights in the background create a cinematic bokeh effect.

### Recommended Usage
- **OG / social share image** — use as the Open Graph image (1200×630 recommended crop — the image is 1536×1024, so crop center or slightly left)
- **Portfolio site banner** — full-width banner section below the hero, narrower height (e.g. 400px)
- **Email signature / newsletter header** — resize to 600×400

### Technical Specs
- **Format:** PNG
- **Aspect ratio:** 3:2
- **Text zone:** Left third is intentionally clear — overlay brand text in Orbitron bold

---

## Color & Typography Reference

### Brand Colors
| Color | Hex | Usage |
|---|---|---|
| Void Black | `#0A0A0A` | Backgrounds, text |
| Neon Amethyst | `#9B59B6` | Primary brand, headlines, CTAs |
| Electric Cyan | `#00E5FF` | Accents, highlights, glitch effects |
| Warm Pearl | `#F5F0EB` | Body text on dark backgrounds |
| Copper Ember | `#D4735E` | Warm accents, secondary CTAs |

### Typography
| Element | Font | Weight |
|---|---|---|
| Hero Headline | Orbitron | Bold 700+ |
| Subtitle / Tagline | Space Mono | Regular |
| Body copy | Inter | Regular 400 / Medium 500 |
| Fallback | system-ui | — |

---

## Suggested Hero Section HTML/CSS Snippet

```html
<section class="nova-hero">
  <div class="nova-hero__overlay"></div>
  <div class="nova-hero__content">
    <h1 class="nova-hero__title">NOVA CHEN</h1>
    <p class="nova-hero__subtitle">The Neon Oracle</p>
    <p class="nova-hero__tagline">AI-born. Style-driven. Always on.</p>
    <a href="#" class="nova-hero__cta">See My Latest ⚡</a>
  </div>
</section>

<style>
.nova-hero {
  position: relative;
  width: 100%;
  height: 90vh;
  background: url('hero-landing-page.png') center center / cover no-repeat;
  display: flex;
  align-items: center;
}
.nova-hero__overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, rgba(10,10,10,0.85) 0%, rgba(10,10,10,0.3) 50%, transparent 100%);
}
.nova-hero__content {
  position: relative;
  z-index: 1;
  padding: 4rem;
  max-width: 600px;
}
.nova-hero__title {
  font-family: 'Orbitron', sans-serif;
  font-weight: 700;
  font-size: clamp(3rem, 8vw, 6rem);
  color: #9B59B6;
  margin: 0;
  line-height: 1;
}
.nova-hero__subtitle {
  font-family: 'Space Mono', monospace;
  font-size: 1.2rem;
  color: #F5F0EB;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  margin-top: 0.5rem;
}
.nova-hero__tagline {
  font-family: 'Inter', sans-serif;
  font-size: 1.1rem;
  color: #00E5FF;
  margin-top: 1rem;
}
.nova-hero__cta {
  display: inline-block;
  margin-top: 2rem;
  padding: 0.8rem 2rem;
  background: #9B59B6;
  color: #0A0A0A;
  font-family: 'Orbitron', sans-serif;
  font-weight: 700;
  text-decoration: none;
  border-radius: 4px;
  transition: background 0.3s;
}
.nova-hero__cta:hover {
  background: #D4735E;
}
</style>
```

---

*Created for the Gen Ai team — VirtuAI Influencers*
*Persona: Nova Chen "The Neon Oracle"*