# QA Checklist

Three verdicts: **Accept** (ship it), **Regenerate** (the frames are wrong — go back to the producer),
**Repair** (the frames are fine — fix the loop/encode/caption). Route every failure to the right one;
do not regenerate a whole set when only the encode is over budget.

## Accept

- **Loop test (falsifiable):** play the sticker 5 times in a row and watch the seam. If the last
  frame jumps to the first — a pop, a snap, a position skip — it fails. Ping-pong and verified
  cyclic loops pass; a directional motion that rewinds fails.
- **Thumbnail test (falsifiable):** shrink to 240px and read it in one second. If you cannot read
  the caption AND name the chat moment (笑死 / 摆烂 / 已读不回 …) from the thumbnail alone, fail.
- **Spec test (falsifiable):** run `verify_output.py --file FILE.gif --platform {wechat|line|telegram|discord|twitter|generic}`
  for the target platform. Dims, byte size, fps, frame count, and loop flag must all pass — it exits
  nonzero on any breach. A WeChat GIF at 401KB or 260×260 fails — no eyeballing.
- **Token-budget test (falsifiable):** the delivery states the budget route used (`low` / `medium`
  / `high`) and the number of image-gen calls. A real-photo A-face-anchor run fails QA if it
  generated more than 2 sheets before the first preview, or more than 4 sheets in one high-budget
  batch. A delivery also fails if it printed/generated-image base64 or dumped session JSONL.
- The motion serves the chat moment; if motion adds nothing, a clean static sticker is the better deliverable.
- There is ONE dominant motion + at most one overlay (≤12% weight). Two big motions fail.
- The caption is correct, ≤6 字, 网络口吻, crisp at 240px with a stroke (≥8px@240) that survived quantization.
- Edges are clean: transparent where the platform needs alpha, or a deliberate flat/white-stroke matte for WeChat/X — no dark halo, no fringe.
- Timing is legal: fps ∈ {25, 20, 10, 5, 4, 2} (the GIF-safe set `kinetic_text.py`/`assemble.py` snap to), `duration = frames/fps` is clean, loop length 0.6–1.8s.
- Not seizure-flashing: ≤3 flashes/sec, local glow only, never a full-frame luminance slam, with a clean held rest frame.
- **[MODE A]** Every frame is on-model: same identity block, lighting, background, framing — no flicker, no cross-frame drift. The subject reads as one character, not eight cousins. (See `frame-generation.md` for the consistency rungs that hold a set together.)
- **[MODE A, real-photo edit]** The delivery carries the verbatim honesty caveat (the output is a *stylized likeness, not the real face*). This is the Face-Truth Gate — see `SKILL.md (Face-Truth Gate)`. A Mode-A-edits-real-photo run that omits it FAILS regardless of how good the loop looks.
- **[MODE A, real-photo edit]** The first pass is an A-smoke unless the user explicitly accepted a
  high-budget pack. Do not ship a surprise full A pack after many image-gen calls.
- **[MODE B]** The real photo is byte-for-byte undistorted — only composited text and deterministic photo motion (Ken-Burns / bounce / jelly) move. No face was re-synthesized. (The Mode B compositing path is documented in `render-pipeline.md`.)
- **Real-pack test:** placed next to a real WeChat/LINE pack a person actually uses, does this look amateur or off? If yes, regenerate.

## Regenerate

Frame-level failures — the producer must make new frames.

- **[MODE A]** The set drifts off-model: a frame's face, body, palette, or accessory does not match the others. Pull back to the model sheet / base image, branch (never chain), regenerate. (The model-sheet and batch/SET workflow is in `frame-generation.md`.)
- **[MODE A]** Frames flicker: background re-noises, lighting pops, or the subject jumps >3px between frames (a registration failure, not an encode failure).
- **[MODE A]** Only rung A4 (same-seed-only) was available and >2 frames visibly wobble — the identity lock is too weak for this motion; drop frames or escalate the rung (see the rung ladder in `frame-generation.md`).
- **[MODE B]** The "real photo" is actually distorted, warped, or re-synthesized — an image model touched the pixels. Mode B forbids this; rebuild from the untouched still.
- The sticker maps to no real chat moment — it is decoration, not a reply. Cut it or reassign a real moment.
- The producer exceeded the image-gen budget (more than 2 sheets before first preview, or more than
  4 sheets in a high-budget batch). Stop and report budget overrun; do not continue generating.
- Two or three motions stack with no dominant beat; the eye does not know where to land.
- A directional motion was ping-ponged and visibly rewinds (a one-way wave running backward). Re-author as a true cyclic loop (see `motion-library.md`).
- The frames carry baked-in gibberish or melted text from the image model (Mode A) — kill it; captions are composited deterministically by `kinetic_text.py`, not generated.

## Repair Moves

The frames are good; fix the loop, encode, caption, or budget. All of these re-run from the
`frames/f%04d.png` + `manifest.json` contract (documented in `render-pipeline.md`) — never re-process
a finished GIF.

If the loop seam jumps:

```text
Re-loop on the RGBA frames BEFORE quantization. For there-and-back motion (blink/bob/nod),
regenerate with --loop boomerang (reverse all but the duplicated endpoints). For directional
motion, design a true cyclic loop where frame N+1 == frame 0 and pass --loop cyclic. Never
crossfade after quantize. Re-run assemble.py --in DIR --out FILE.gif.
```

If the file is over the platform byte budget:

```text
There is no separate budget step — re-run assemble.py at a lower --fps or a smaller --size
until you clear the platform byte cap, RE-ENCODING FROM FRAMES (regenerate the frames with
kinetic_text.py at the new --fps/--size for Mode B), not from the finished GIF. Telegram ≤256KB
/ Discord emoji ≤256KB usually need fewer --frames + a flat-or-transparent bg + --loop boomerang.
If gifsicle is on PATH, assemble.py automatically uses it to shrink further. Re-run
verify_output.py --platform X after each step until it exits zero. See platform-specs.md for caps.
```

If the token/image-gen budget is overrun:

```text
Stop generation immediately. Build a contact sheet from already-saved PNG files, assemble only the
best candidates already produced, and report the overrun. Do not inspect session JSONL to recover
payloads; use saved paths. Offer the low-cost B-photo-puppet route as the fallback.
```

If the caption is wrong, garbled, or muddy at 240px:

```text
Re-render the caption deterministically with kinetic_text.py: --text "{correct text}" EXACTLY,
a bold CJK font via --font /path/to/bold-CJK.ttf (there is NO shipped fonts/ dir — pass your own,
or omit --font and let kinetic_text.py auto-detect a system CJK font: STHeiti / Hiragino /
PingFang / Noto). Aim for cap-height ≥38% of canvas via --cap-ratio, with the stroke ≥8px@240
baked on RGBA before quantization. Mode B keeps text crisp by definition — if it is muddy, the
text was dithered downstream; re-bake pre-quantization. See text-and-layout.md for sizing.
```

If edges fringe or carry a dark halo:

```text
For alpha platforms: keep transparency (omit --flatten); assemble.py exports 1-bit alpha with
hard edges, so author the stroke to read against any chat bg. For WeChat/X: re-run
assemble.py --flatten RRGGBB onto the flat ground (WeChat → add the 2px white-stroke variant).
Re-encode from frames; do not re-process the finished GIF. See render-pipeline.md / text-and-layout.md.
```

If the motion is jittery or flickers between frames at encode:

```text
assemble.py uses Pillow's own optimizer (ordered/no extra temporal dither), so jitter here is
usually too many near-identical frames or too high an fps for the palette. Re-run with fewer
--frames, a lower --fps, and a flat/transparent bg so the palette stays stable. For higher-quality
palettes/encoding beyond the portable Pillow path, swap in ffmpeg paletteuse or gifski as
described in render-pipeline.md — then re-run verify_output.py.
```

If a strict platform rejects FLASH/GLITCH (or for seizure safety):

```text
Swap to the safe equivalent at zero flash-risk: FLASH→POP, GLITCH→SHAKE (both are presets:
--preset pop / --preset shake). Same emotional beat, mandatory clean held rest frame (--preset hold
or a held endpoint), local glow only — never a global strobe. See motion-library.md for the
safe-swap table.
```

If you cannot encode at all:

```text
Do not fake output. These scripts are Pillow-only — NO ffmpeg, gifski, or gifsicle is required,
so a normal Python 3 + Pillow environment always encodes; if gifsicle happens to be on PATH,
assemble.py uses it to shrink further. There is no probe script to run and nothing to brew-install
for the reference path. The only true "cannot encode" case is an image-only agent with no shell:
it can produce Mode A frames but cannot run assemble.py — hand off frames/ + manifest.json for
manual ezgif assembly rather than lying.
```
