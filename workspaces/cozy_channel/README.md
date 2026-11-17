# Cozy Channel Production Pipeline

Long-form ambient loops (1h / 3h / 8h) built locally with FFmpeg, with a
fail-closed license gate and a receipt for every render.

Reference format: *"Cozy November Fireplace 🍂 Slow Piano Jazz & Crackling
Fire for Reading and Relaxation"* — browse/suggested-feed driven, no search
reliance, no Content ID exposure.

## One command

```bash
python3 build_loop.py --duration 3h          # or 1h / 8h / bare seconds
python3 build_loop.py --duration 60 --dry-run  # print the exact ffmpeg argv
```

## Layout

```
cozy_channel/
  build_loop.py            master renderer (license gate + receipt)
  make_seamless_loop.py    xfade loop prepper for raw clips
  asset_ledger.json        license provenance for every input
  music/                   your royalty-free tracks (gitignored)
  visual_loop.mp4          prepared seamless visual loop (gitignored)
  fireplace_ambient.wav    prepared seamless ambient loop (gitignored)
```

## Fail-closed license gate

Every input must be registered in `asset_ledger.json` with source URL,
license, author, retrieval date, and sha256. The build refuses (exit 2,
structured PLACEHOLDER_* message) when:

- the asset is missing or unregistered
- the license is outside the allowed set (CC0 / public domain /
  YouTube Audio Library / CC-BY / OWNER-GENERATED)
- the file's sha256 no longer matches the ledger (drift = tamper)

`OWNER-GENERATED` covers footage you generate yourself (Runway / Sora /
Pika) — full rights held in-house, zero third-party copyright. Provenance is
still mandatory: `source_url` must record the generator and the prompt card
id from `visual_prompts.md`.

Allowed licenses and the full schema live in `asset_ledger.json`.

## Production workflow

1. **Source visuals** — generate them yourself (`visual_prompts.md` prompt
   cards → Runway Gen-3 / Sora / Pika → register as `OWNER-GENERATED`), or
   pull CC0 footage from Pexels / Pixabay, Mixkit, Archive.org. Prefer
   **static tripod shots**
   (fireplace, rain on glass, steaming mug by a snowy window): static
   frames crossfade invisibly; camera moves expose the seam.
2. **Prepare the loop** — `python3 make_seamless_loop.py --input raw_clip.mp4`
   trims the tail and crossfades it into the head so the restart vanishes.
3. **Source audio** — YouTube Audio Library (Jazz/Ambient, Calm mood; no
   attribution) and freesound.org filtered to **CC0** for crackle/rain/wind
   loops. Register every file in `asset_ledger.json` (sha256 it first:
   `shasum -a 256 <file>`).
4. **Render** — `build_loop.py --duration 1h|3h|8h`. Shuffle seed and the
   exact ffmpeg argv land in `memory/catch_log/COZY_BUILD_RECEIPT.json`.
5. **Audit before publish** — upload **Unlisted**, wait 24h for Content ID
   to scan; only schedule public when the scan comes back clean.

## Packaging (CTR + watch time)

- **Title:** `[Cozy Location/Season] + [Visual Element] + [Genre] & [Ambient]
  for [Use Case]` — e.g. *"Cozy November Cabin 🍂 Slow Piano Jazz &
  Crackling Fireplace for Reading, Studying & Sleep"*.
- **Thumbnail:** high-contrast frame, warm highlights, darkened shadows so
  firelight pops on mobile; at most a 2-word serif overlay ("3 HOURS").
- **Description:** timestamped tracklist — viewers read it, and YouTube
  indexes the text semantically.

## Self-test

`python3 selftest.py` builds a 60-second master from synthetic CC0-marked
assets, proves duration/asset checks, exercises both refusal paths, and
writes `memory/catch_log/COZY_PIPELINE_SELFTEST_RECEIPT.json`. Run it after
any change to the pipeline.
