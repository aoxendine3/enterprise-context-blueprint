# Visual Generation Prompt Library — Cozy Channel

Prompt cards for seasonal cinematic loops. Generation ownership model: footage
you generate (Runway Gen-3 / Sora / Pika / etc.) is **owner-generated** — you
hold the full rights, zero third-party copyright liability. Register it in
`asset_ledger.json` with license `OWNER-GENERATED` and the generator + prompt
recorded in `source_url` / `notes`.

Pipeline path for every card:

1. Generate 4K/1080p **16:9** clip from the prompt below (10–20s is enough).
2. `python3 make_seamless_loop.py --input raw_clip.mp4 --output visual_loop.mp4`
   — crossfades the tail into the head so the restart is invisible.
3. Register the prepared loop in `asset_ledger.json`
   (`license: OWNER-GENERATED`, sha256 via `shasum -a 256 <file>`).
4. `python3 build_loop.py --duration 1h|3h|8h`.

Static tripod framing is mandatory — camera movement exposes the loop seam.

---

## VPC-001 — Winter Snowy Window & Steam (December/January)

* **Best for:** Runway Gen-3 / Sora / Pika
* **Aspect Ratio:** 16:9
* **Status:** PROMPT_READY (awaiting generation → loop prep → ledger)
* **Prompt:**
  Cinematic static shot looking out a rain-streaked window onto a softly
  falling nighttime snowstorm over a quiet pine forest, a ceramic mug of hot
  tea sitting on the wooden windowsill with steam gently rising, warm interior
  glow contrasted against cold blue winter moonlight, cozy mood, high
  fidelity, 4k.
