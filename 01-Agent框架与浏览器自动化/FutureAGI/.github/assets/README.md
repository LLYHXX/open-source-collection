# README assets — spec sheet for marketing

Every image the top-level `README.md` references is listed below with its exact intent, position, dimensions, and format. **Total asset budget < 12 MB** — keep GIFs only where noted; static PNGs elsewhere.

## Required before public launch

### 1. `logo-banner.png` + `logo-banner-dark.png` — Hero logo

- **Where:** very top of README
- **What:** full wordmark "Future AGI" + tagline "AI Agents hallucinate. Fix it faster." — centered
- **Size:** 1600 × 400, PNG, transparent background
- **Variants:** light + dark (served via `<picture>` tag)
- **Optimize with:** `pngquant --quality 80-95`

### 2. `hero-demo.gif` + `hero-demo-dark.gif` — Hero product demo

- **Where:** directly below the hero, slot 2
- **What:** 8–12 second product loop. Suggested flow: *open trace → expand span → run eval → see score → navigate to Simulate → voice agent conversation plays → navigate to Gateway → cost / guardrails dashboard.* Silent. Seamless loop.
- **Size:** 1600 × 900, GIF ≤ 4 MB
- **Fallback:** first frame as `hero-demo.png` for GIF-blocked viewers
- **Variants:** light + dark (dark records on dark theme)
- **Pipeline:** record MP4 → `ffmpeg -i in.mp4 -vf "fps=15,scale=1600:-1" frames/%04d.png` → `gifski -o hero-demo.gif frames/*.png --fps 15 --quality 90`

### 3–8. Six feature banner images

One per core pillar, all **2400 × 960 PNG** (GitHub renders at 2× for Retina) on dark theme:

| Filename | Pillar | Should show |
|---|---|---|
| `feature-simulate.png` | Simulate | Simulate tab — voice-agent conversation playing, persona panel on left, transcript on right |
| `feature-evals.png` | Evaluate | Evals dashboard — run table (pass/fail rows) + per-metric score histogram on right |
| `feature-guardrails.png` | Control | Protect page — rule list with toggles (PII, Injection, Jailbreak…) on left, live blocked-request feed on right |
| `feature-observe.png` | Monitor | Trace detail — timeline of spans, LLM span highlighted with prompt/response pane, token/cost headers across top |
| `feature-gateway.png` | Gateway | Gateway dashboard — provider routing stack (OpenAI → Anthropic fallback visible), cost/token graphs, guardrail events feed, "Shadow Experiment" card |
| `feature-optimize.png` | Optimize | Optimization run view — before/after prompt diff on left, metric lift chart on right, algorithm selector at top (GEPA highlighted) |

**Recording tool:** CleanShot X (Mac) or equivalent. Keep window chrome consistent across all six. Hide cursor. Redact any real customer data, real emails, real API keys — use `demo-user@example.com` and obviously-fake tokens.

### 9. `architecture.svg` — existing

Already committed. 1200 × 760 dark-palette SVG with four bands (client → edge → platform → data). Swap only if doing a branded redraw.

### 10. `integrations-grid.png` — Integrations

- **Where:** below Integrations heading
- **What:** 5-row × 5-col **grayscale** logo grid. **Colored logos look like an ad** — use grayscale.
  - Row 1 (LLM): OpenAI · Anthropic · Google · AWS Bedrock · Azure
  - Row 2 (Framework): LangChain · LlamaIndex · CrewAI · AutoGen · DSPy
  - Row 3 (Voice): LiveKit · VAPI · Retell · Pipecat · Deepgram
  - Row 4 (Vector): Pinecone · Qdrant · Weaviate · Chroma · Milvus
  - Row 5 (Tools): OpenTelemetry · Vercel · MCP · A2A · HuggingFace
- **Size:** 1600 × 800, PNG
- **Fallback:** the markdown category table below the image already serves if the image 404s

### 11. `social-preview.png` — GitHub social preview

- **Where:** **NOT** committed to the repo. Uploaded via repo Settings → Options → Social preview.
- **What:** logo + tagline + 1 screenshot tile. Shown on Twitter / LinkedIn / Slack / Discord unfurls.
- **Size:** 1280 × 640, PNG (GitHub's required size)

## Optional (nice-to-have)

### `deploy-buttons.png` — one-click deploy row

Inline shields already work; only swap to an image if you need brand color accents beyond what `img.shields.io` allows.

### `use-cases-band.png` — use-case icon row

Seven small tiles (headset · phone · briefcase · magnifier · robot · mouse · code) in a single 1600 × 200 band. Currently emoji bullets — image is purely visual polish.

### `feature-falcon-ai.gif` — Falcon AI copilot demo

6-second loop of the in-product AI copilot answering a question. GIF ≤ 3 MB, 1600 × 900. Only needed once Falcon AI is public.

## Do NOT add

- **Contributor avatar wall** — skip until we cross ~50 contributors (premature social proof hurts more than helps). Use [`contrib.rocks`](https://contrib.rocks/) when ready.
- **More than 6 badges** in the header — we're already at 6 (license, stars, Docker pulls, PyPI, npm, Discord). Peer projects with >10 badges measurably bounce harder.
- **Colored competitor logos** — legal risk + visual noise.

## Recording + optimization checklist

1. Record on the **dark theme** always (matches landing page + GitHub dark mode).
2. Hide the mouse cursor for screenshots; subtle cursor highlight for GIFs.
3. **No real data.** Use `demo-user@example.com`, `sk-fake-test-key-for-demos`.
4. PNG optimize: `pngquant --quality 80-95 --skip-if-larger -o out.png in.png` (expect ~70% size drop with no visible loss).
5. GIF optimize: `gifski` not `ffmpeg` — much higher quality at same size.
6. Verify on a 1440p monitor and a 4K monitor before committing. GitHub renders at display pixels, so crisp at 2× source.

## Sources to reuse from

The landing page at [futureagi.com](https://futureagi.com) has polished, on-brand product shots. Check `../../new-landing-page/public/` for existing `.webp` / `.png` assets before re-recording — anything there is already art-directed.
