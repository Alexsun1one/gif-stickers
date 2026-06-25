# Render Pipeline

The shared deterministic core. Both modes converge here. MODE A hands over generated frames
(model-sheet crops, edited variants); MODE B hands over photo-composited frames (the real photo
plus baked kinetic text). From this point on, the pipeline does not know or care how the frames
were made — it only sees `out/<name>/frames/f%04d.png` + `manifest.json` and turns them into one
small seamless-looping GIF.

**No image model runs in this step.** The whole assembly core is **Pillow-only** — no ffmpeg,
no gifski, nothing to `brew install`. This is why MODE B text is always crisp: it is drawn
programmatically onto RGBA frames by `kinetic_text.py` before quantization, never re-synthesized by
a model. It is also the one deliberate departure from the prompt-only `everyday-skills` family — a
GIF is bytes, not a prompt, so the agent WRITES and RUNS three small scripts rather than handing a
prompt to an image tool. Tool-neutral: Codex, Claude Code, or Hermes all drive the same scripts.

**Honesty first — see SKILL.md (Face-Truth Gate).** Before any frame exists, the Face-Truth Gate
in `SKILL.md` decides what the photo path is even allowed to claim. The pipeline below never
re-synthesizes a real face: MODE B animates TEXT and the whole still, never the subject's
expression. A photo that needs a talking/blinking/turning face is out of scope and the Gate stops
it there — this file assumes the Gate has already passed.

## The three real scripts (the entire pipeline)

| script | role |
| --- | --- |
| `scripts/sheet_to_sticker.py` | **MODE A** sheet handoff — slice a generated 1x4/2x4 sheet, bake crisp animated caption text, assemble, and verify with small logs. |
| `scripts/kinetic_text.py` | **MODE B** frame generator — composite a big stroked caption over the real photo (untouched) and animate the TEXT into RGBA frames + `manifest.json`. |
| `scripts/photo_puppet.py` | **MODE B** photo-motion generator — move the original photo pixels as one layer, with optional caption/overlay, into the shared frame contract. |
| `scripts/assemble.py` | **shared assembler** — `frames/f%04d.png` + `manifest.json` → one small, seamlessly-looping GIF. Pillow-only; uses `gifsicle` if it happens to be on PATH. |
| `scripts/verify_output.py` | **gate** — assert dims / size / frames / loop against a platform's caps; exit non-zero on breach so nothing off-spec ships. |

`scripts/README.md` documents the same three scripts plus the tested demo.

## Pipeline Order (fixed)

1. **Frames land in the contract** — both modes write `out/<name>/frames/f%04d.png` + `manifest.json`.
   MODE A normally runs `sheet_to_sticker.py`; MODE B runs `kinetic_text.py` or `photo_puppet.py`.
2. **Loop resolve** — `assemble.py` reads `loop_kind` / `loop_strategy` from the manifest and resolves the seam on
   RGBA frames (boomerang there-and-back, or a cyclic/directional sequence) BEFORE quantizing.
3. **Background resolve** — keep 1-bit transparency, OR pass `--flatten RRGGBB` to composite onto a
   flat color for platforms that drop alpha (WeChat / X).
4. **Encode** — `assemble.py` quantizes every frame to one shared adaptive palette and writes a
   `loop=0` (infinite) GIF. If `gifsicle` is on PATH it runs `gifsicle -O3` to shrink further;
   otherwise it falls back to Pillow's own optimizer. Either way the output is valid.
5. **Budget** — over the platform byte cap? Re-run `assemble.py` at a lower `--fps` or a smaller
   `--size` (regenerate frames at the smaller size) until you are under. Always re-encode from
   FRAMES, never re-process a finished GIF.
6. **Verify** — `verify_output.py --platform X` refuses non-compliant bytes (dims / size / frames /
   loop). It exits non-zero on a hard breach, and only WARNS on Discord's soft/uncertain numbers.

## Step 1 — Frames into the contract

MODE B (the real-photo path) generates frames directly from a photo + caption:

```bash
python3 scripts/kinetic_text.py --base photo.png --text 笑死 --preset bounce \
    --frames 12 --fps 10 --size 240 --out out/xiaosi
```

`--base` is the user's real photo, fitted to `--size` by cover-crop (never distorted); pass
`--base ""` (blank) for a flat ground instead of a photo. This writes `out/xiaosi/frames/f0000.png …`
plus `out/xiaosi/manifest.json`. MODE A normally starts from a generated sheet and runs:

```bash
python3 scripts/sheet_to_sticker.py --sheet sheet.png --grid 1x4 \
  --caption 笑死 --text-motion pop --platform wechat --loop cyclic \
  --out out/xiaosi
```

The helper writes the same `frames/f%04d.png` layout and `manifest.json`, then calls `assemble.py`
and `verify_output.py`. It is the default because it avoids ad hoc crop code, keeps logs small, and
adds exact animated Chinese text after frame selection.

## Step 2 — Seamless Loop

`loop_kind` / `loop_strategy` comes from the manifest (`kinetic_text.py`, `photo_puppet.py`, and
`sheet_to_sticker.py` write it from `--loop`). Stickers loop forever; a hard jump reads as broken. `assemble.py` resolves the seam on RGBA
frames before quantizing — never after.

- **boomerang** — forward then reverse, always seamless, doubles length for free. `assemble.py`
  builds `frames + frames[-2:0:-1]` so the duplicated endpoints do not stutter. Use for
  there-and-back motion (blink / bob / nod / a pop that settles).
- **cyclic** — motion authored so the last frame blends back into the first; the assembler plays
  the frames straight through. Verify the seam differs by one motion step.
- **directional** — a one-way move (wave-off, slide-out). Played straight through, NEVER
  boomeranged (a wave that rewinds looks broken). Set `--loop directional`.

## Step 3 — Background Resolve (transparency vs. flatten)

GIF alpha is **1-bit** (fully opaque or fully transparent — no soft edges). By default `assemble.py`
keeps transparency: it reserves one palette index for alpha and thresholds at 50% (`a < 128` →
transparent). Pass `--flatten RRGGBB` to composite every frame onto a flat color first, for
platforms that drop alpha entirely:

```bash
# Keep 1-bit transparency (LINE / Discord / Telegram)
python3 scripts/assemble.py --in out/zantong --out out/zantong/sticker.gif

# Flatten onto white (WeChat / X — no usable alpha downstream)
python3 scripts/assemble.py --in out/xiaosi --flatten FFFFFF --out out/xiaosi/wechat.gif
```

Need real *soft* alpha (feathered edges, gradients)? GIF cannot do it at any setting — export APNG
or WEBM instead (see `platform-specs.md`). For WeChat specifically, bake a +2px white stroke into
the frames before flattening so the subject does not bleed into the background.

## Step 4 — Encode (Pillow-only, gifsicle optional)

`assemble.py` quantizes every frame to **one shared adaptive palette** (MEDIANCUT, 256 colors flat
/ 255 + 1 reserved for transparency) and writes a single `loop=0` GIF. There is no ffmpeg and no
gifski in this path — it runs anywhere Python + Pillow runs. After the GIF is written, the script
calls `gifsicle -O3` **only if `gifsicle` is found on PATH**; if it is missing, Pillow's own
`optimize=True` already produced a valid file and the script says so. You never need to probe for or
install an encoder — the scripts are Pillow-only and degrade to "gifsicle not found" gracefully.

```bash
# what assemble.py prints on success
GIF: out/xiaosi/wechat.gif  240x240  8 frames  100ms/frame  62.9KB  [gifsicle -O3]
```

For a one-off higher-quality palette you *may* hand-swap ffmpeg `palettegen/paletteuse` or `gifski`,
but that is an optional upgrade described in `scripts/README.md` — it is never required, and the
skill never claims a probe script gatekeeps it.

## Step 5 — Budget (drive under the byte cap)

Byte caps are brutal (Telegram 256KB, WeChat ~400–500KB). There is no separate budget script — you
re-run `assemble.py` with cheaper inputs until `verify_output.py` passes. Climb the knobs in order:

1. **fps↓** — `--fps 5` instead of `--fps 10` halves the centisecond delays' frame churn.
2. **size↓** — regenerate frames at a smaller `--size` (e.g. 240 → 200), then reassemble.
3. **fewer frames** — fewer `--frames`, or switch a directional clip to a tighter cyclic loop.

Always re-encode from source FRAMES, never re-process a finished GIF (re-quantizing a dithered GIF
compounds artifacts). Few frames + flat/transparent bg + a tight loop are how you stay under spec —
not just aesthetics.

## Step 6 — Verify (refuse off-spec bytes)

```bash
python3 scripts/verify_output.py --file out/xiaosi/wechat.gif --platform wechat
```

`verify_output.py` opens the finished GIF and asserts the platform's hard caps — max side, file
size, frame count (and `max_frames` for LINE), and `loop == 0` where loop is required — printing
PASS/FAIL per check and exiting non-zero on any hard breach. The Discord caps are flagged uncertain
in `platform-specs.md`, so for `--platform discord` a breach is a **warning only** (exit 0), never a
hard reject. `--platform` is one of `{wechat | line | telegram | discord | twitter | generic}`.

## The tested end-to-end demo (use THESE exact forms)

```bash
# MODE B: animate the caption 笑死 over a photo, bounce, 12 frames @10fps, WeChat 240px
python3 scripts/kinetic_text.py --base photo.png --text 笑死 --preset bounce \
    --frames 12 --fps 10 --size 240 --out out/xiaosi
python3 scripts/assemble.py --in out/xiaosi --flatten FFFFFF --out out/xiaosi/wechat.gif
python3 scripts/verify_output.py --file out/xiaosi/wechat.gif --platform wechat
```

Verified result: `240×240 · 8 frames (held frames merged) · loop=0 · ~63KB · PASS wechat`. A
transparent variant (no photo, flat ground, kept alpha):

```bash
python3 scripts/kinetic_text.py --base "" --text 赞同 --preset pop --frames 10 --fps 10 --size 240 --out out/zantong
python3 scripts/assemble.py --in out/zantong --out out/zantong/sticker.gif   # keeps transparency
```

## Deterministic-Timing Law

GIF delays are stored in **centiseconds**, so only `fps ∈ {25, 20, 10, 5, 4, 2}` divides cleanly
(4 / 5 / 10 / 20 / 25 / 50 cs). `assemble.py` enforces exactly this set — pass any other `--fps` and
it snaps to the nearest safe value rather than producing jittery rounding. `duration = frames / fps`
should land on a clean number. Never author above 50 fps. The written GIF is always `loop=0`
(infinite). Because the whole core is Pillow-only, there is no encoder to probe and nothing to
install — a missing `gifsicle` just means a slightly larger (but valid) file.

## MODE B — Text & Effect Compositing (crisp, deterministic)

`kinetic_text.py` composites the caption on RGBA frames **before** GIF quantization — text rendered
into a 256-color dithered space goes muddy. It draws a big white fill with a hard dark stroke
(`stroke_width ≈ 3.5% of canvas`), which is the single best legibility trick through quantization: it
gives the quantizer high-contrast edges to lock onto. The fills stay pure white/near-black so they do
not dither. The real photo pixels are never re-synthesized — only TEXT and overlays are added (this
is what keeps MODE B inside the Face-Truth Gate).

**Fonts — there is no shipped `fonts/` dir, and the skill never claims one.** `kinetic_text.py`
auto-detects a system CJK font, trying STHeiti → Hiragino Sans GB → PingFang → Noto CJK in order.
If none is found, or you want a specific bold face, pass it explicitly:

```bash
python3 scripts/kinetic_text.py --base photo.png --text 笑死 --preset bounce \
    --frames 12 --fps 10 --size 240 --font /path/to/bold-CJK.ttf --out out/xiaosi
```

The five presets (`--preset {pop | bounce | shake | flash | hold}`) all animate in the first ~70%
of the frames and then **settle to a held rest pose** — the frame people screenshot. `--cap-ratio`
controls cap-height as a fraction of the canvas; `--pos {top | bottom}` places the caption.

## MODE B — Cheap Photo Motion (optional, baked into the frames)

Animating the WHOLE still (nod/shake/bob/pop/stamp/slide/sleep/question) is handled by
`photo_puppet.py`. It moves the original photo pixels as one layer, so the face remains the source
photo, but the person/image visibly moves. It does not make the face talk, blink, or turn; that
needs a video/face model and is out of scope.

```bash
python3 scripts/photo_puppet.py --base photo.png --text 离谱 --action question \
  --overlay question --frames 12 --fps 10 --size 240 --loop cyclic --out out/lipu
python3 scripts/assemble.py --in out/lipu --flatten FFFFFF --out out/lipu/wechat.gif
python3 scripts/verify_output.py --file out/lipu/wechat.gif --platform wechat
```

## The Frame Contract (`frames/f%04d.png` + `manifest.json`)

This is documented HERE because it is the one interface both modes share. Each output dir holds a
`frames/` folder of zero-padded RGBA PNGs and a `manifest.json` that `assemble.py` reads:

```json
{
  "mode": "B",
  "preset": "bounce",
  "fps": 10,
  "size": 240,
  "frames": 12,
  "loop_kind": "cyclic",
  "loop_strategy": "cyclic",
  "text": "笑死",
  "text_motion": "pop",
  "frame_glob": "frames/f%04d.png"
}
```

`fps` MUST land in `{25, 20, 10, 5, 4, 2}` (the assembler snaps it if not). `loop_kind` /
`loop_strategy` is `cyclic | boomerang | directional` — `boomerang` doubles the played frames
there-and-back inside `assemble.py`. MODE A uses `sheet_to_sticker.py` to write this shape; the
frames just need to live at `frame_glob` in sorted order. `verify_output.py` then re-checks the
*encoded* bytes against the platform caps and refuses anything off-spec.

## Decision Cheats

- Photo + a punchy word → **MODE B**: `kinetic_text.py` (real photo untouched, text animated).
- Generated sheet + exact Chinese caption → **MODE A helper**: `sheet_to_sticker.py --caption ... --text-motion pop`.
- Flatten for **WeChat / X** with `assemble.py --flatten RRGGBB`; keep transparency (omit `--flatten`)
  for **LINE / Discord / Telegram**.
- Soft alpha or >256 colors → GIF can't; export APNG / WEBM (see `platform-specs.md`). LINE wants APNG.
- Loop: author **cyclic** if you can; **boomerang** is the foolproof fallback; never boomerang
  directional motion.
- Size: re-run `assemble.py` at lower `--fps` → smaller `--size` → fewer `--frames`; re-encode from
  frames. `gifsicle -O3` runs automatically when present, but is never required.
- Text: bake it on RGBA frames before quantization, with a hard stroke and a CJK font that
  `kinetic_text.py` auto-detects (or pass `--font /path/to/bold-CJK.ttf`).
- Everything is Pillow-only — nothing to probe, nothing to `brew install`; a missing `gifsicle` only
  means a slightly larger valid file.

Sources: Pillow `save_all` GIF docs (palette, transparency, disposal) · gifsicle `-O3` optimization
guide · DigitalOcean gifsicle guide · WeChat / LINE animated-sticker (transparent APNG) guidelines ·
Telegram WEBM/VP9 notes (see `platform-specs.md` for the alpha-video foot-gun).
