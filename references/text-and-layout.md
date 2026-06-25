# Text & Layout

The caption is the second half of the sticker. The motion catches the eye; the **≤6-字 caption
says what to send it for**. At 240px on a busy chat background, a thin or low-contrast caption
disappears — and a caption baked by an image model garbles. So in this skill the caption is
**composited programmatically with a resolved font (Pillow, via `scripts/kinetic_text.py`), never
asked of an image model.** The scripts are Pillow-only — no ffmpeg required. Programmatic text is
always correct, never melted, never doubled, never gibberish — that is the whole point.

This applies to **both modes**. MODE A frames may be generated with NO baked text (a clean
caption zone), then the caption is composited at assembly. MODE B keeps the real photo and the
caption IS the deliverable — it lives entirely on the text system; `kinetic_text.py --base
photo.png` runs straight on the photo (`--base` blank = flat ground). Either way, text is the
last RGB layer before quantization, so the glyphs stay correct.

## The legibility law (every captioned sticker)

| # | Rule | Why |
| --- | --- | --- |
| L1 | **≤ 6 字, ≤ 2 lines.** Emotion is carried by the motion, not a sentence. | 240px can't hold a clause legibly. |
| L2 | **Cap-height ≥ 38% of canvas** for the hero line; one dominant caption, never two. | A small caption reads as decoration, not a reply. |
| L3 | **One hard outline, stroke ≥ 8px @ 240px** (scale with canvas), high contrast, optional soft drop-shadow. | The stroke gives the quantizer a high-contrast edge to lock onto; survives any chat background. |
| L4 | **Flat fill** in palette-exact white/black or one accent — never a gradient fill. | Gradients dither to mud at thumbnail scale; flat fills stay crisp. |
| L5 | **Anti-alias the STROKE, not the fill.** Keep the fill 1–2 solid colors. | Smooth edges on the outline, hard flat letters inside. |
| L6 | **Place the caption OFF the face/subject** — top band or bottom band, in safe area (`--pos {top\|bottom}`). | Text over the eyes kills both the expression and the words. |
| L7 | **Reserve the caption zone before motion is authored** — the subject never drifts into it. | A bobbing head that clips the caption reads as broken. |
| L8 | **Pass a real `.ttf` via `--font` or let `kinetic_text.py` auto-detect a system CJK face; never call a font by bare name and hope.** | A font picked by name differs per machine → non-reproducible, sometimes missing → blank text. |

## The 1-bit-alpha caveat (read before promising a "soft" outline)

GIF alpha is **1-bit** — every pixel is fully opaque or fully transparent, no in-between. So on a
**transparent GIF** the anti-aliased edge of L5's soft stroke has nowhere to live: the threshold
forces each edge pixel to opaque or gone, and the smooth outline collapses to a **hard jagged
edge**. This is independent of how the text was rendered — Pillow at 4× then downscaled still
hits the same 1-bit wall at encode. The fringe is not a rendering bug to chase; it is the format.

Route around it, do not fight it:

- **Soft outline that must stay soft on transparency → output APNG / WebP, not GIF.** Both carry
  full 8-bit alpha; the anti-aliased stroke survives. LINE animated stickers already ship as
  transparent APNG (`render-pipeline.md` Step 4), so this is the default there anyway.
- **GIF deliverable → reserve flat-fill + hard-stroke for an OPAQUE or PLATE backing.** On a flat
  ground (or behind a solid plate/pill) the stroke edge sits on opaque pixels and quantizes
  clean — the 1-bit alpha never touches it. This is also the WeChat/X path: run `assemble.py
  --flatten FFFFFF` to drop alpha onto a flat ground, so there is no usable alpha to fringe.
- **Transparent GIF you cannot avoid → expect a 1px hard edge.** Pre-multiply against the likely
  background and accept the crisp-but-aliased silhouette; do not promise a feathered halo it
  cannot keep.

The legibility law still holds on every target — the stroke is the legibility carrier regardless.
The caveat only governs whether its EDGE reads soft (8-bit alpha formats) or hard (1-bit GIF).

## Fonts (resolved explicitly, never guessed)

There is **no shipped `fonts/` directory** in this skill — do not reference one. The renderer gets
its font one of two ways, both reproducible:

- **Pass `--font /path/to/bold-CJK.ttf`** to `kinetic_text.py` to pin an exact face. This is the
  reproducible default when you care about the family look.
- **Omit `--font`** and let `kinetic_text.py` auto-detect a heavy system CJK font — it probes the
  usual macOS/Linux paths (STHeiti / Hiragino / PingFang / Noto Sans SC) and uses the first it
  finds. Convenient, but the exact face then depends on the machine.

Type guidance for the caption:

- **Chinese:** a Noto Sans SC Bold/Black-class face — covers 简体 captions cleanly at small size.
  Heavy weight reads better than regular under an 8px stroke. If you need this exact look on any
  machine, point `--font` at a vendored/installed bold CJK `.ttf` rather than trusting auto-detect.
- **Latin / numbers:** one bold geometric or grotesque (e.g. an Inter-Bold-class face) for
  `LOL` / `OK` / `???`.
- Route the **type voice** from `style-routing.md`: 国潮/古风 captions lean a 书法-flavored or
  serif 宋体 weight (pairs with the ink register); 沙雕/梗 captions go fat rounded sans; 高级/品牌
  go restrained clean sans. Express the voice by pointing `--font` at the right `.ttf` — the font
  is part of the family look, not an afterthought.
- When you need the look pinned and reproducible, **pass an explicit `--font` path** and let the
  run STOP if that path is absent — better a loud failure than a silent fallback to whatever the
  machine happens to have. The rule is: resolve, verify, fail loud — never quietly guess.

## Safe areas & placement

- Canvas is square (`--size 240`); keep the caption inside a **~8% margin** on all sides
  (platforms crop and round corners). At 240px export that is ~20px of breathing room.
- Caption sits in a **top band or bottom band** (`--pos top` / `--pos bottom`); the subject owns
  the center. Default: caption bottom, subject upper-center, the held rest pose framed clean.
- If the look needs a backing for contrast on a transparent or busy frame, use a **solid plate
  or pill** behind the caption (one flat color + the stroke), not a translucent blur. A plate
  also buys back the soft stroke edge on a transparent GIF — the stroke now sits on opaque
  pixels instead of the 1-bit alpha boundary.
- **WeChat variant:** GIF loses smooth alpha → assemble with `--flatten FFFFFF` onto a flat
  ground and add the **2px white stroke** convention around BOTH subject and caption so edges
  don't fringe on the chat background (see `render-pipeline.md` Step 3).

## How the motion animates the text (preset bank)

The caption animates with ONE of the kinetic-text presets from `motion-library.md`, picked from
the chat moment — the user never names a preset. `kinetic_text.py --preset {pop|bounce|shake|
flash|hold}` re-renders the composited text per frame in RGB, so the glyphs stay correct through
the whole animation:

- **POP / STAMP** (`--preset pop`) — scale the caption per frame (back-ease overshoot → settle),
  held sharp on the rest frame. Cap peak scale ≤ 1.15 so letters never clip the safe area.
- **BOUNCE** (`--preset bounce`) — the caption drops/rises with an elastic settle; **end on a
  still readable frame**.
- **SHAKE / JELLY** (`--preset shake`) — jitter ±6px or squash ±15% on one axis, **end on a still
  readable frame**.
- **HOLD** (`--preset hold`) — minimal motion; reserve the final-width box so the layout never
  reflows. Best for 已读不回 / 思考 (stillness is the joke).
- **FLASH → POP** (`--preset flash`) on strict platforms (seizure safety): glow/channel-split the
  STROKE locally, never strobe the whole frame, always land on a clean held frame.

Loop behavior is set at render with `--loop {cyclic|boomerang|directional}`. Re-render each
frame's text in RGB **before** GIF quantization — `kinetic_text.py` does this by writing
`DIR/frames/f%04d.png` per frame, and `assemble.py` only quantizes at the end. Never bake text
into a generated image frame and never composite onto an already-dithered GIF — both garble the
glyphs.

## Caption contract (emitted per sticker, consumed by the text/assembly step)

```text
caption:
  text:        "在吗"            # ≤ 6 字, correct 简体 — passed verbatim as --text
  lines:       1                 # 1-2 max
  font:        --font /path/to/bold-CJK.ttf  # explicit .ttf path, or omit to auto-detect system CJK
  weight:      black
  fill:        "#FFFFFF"         # flat, palette-exact
  stroke_px:   8                 # ≥ 8 @ 240px, scale with canvas
  stroke_fill: "#1A1A1A"
  stroke_edge: soft|hard         # soft only survives on APNG/WebP or behind a plate (1-bit GIF → hard)
  shadow:      soft|none
  plate:       none|pill:#RRGGBB # backing if frame contrast needs it OR to keep a soft edge on transparency
  band:        bottom|top        # --pos; never over the face
  safe_margin: 0.08
  motion:      pop               # --preset {pop|bounce|shake|flash|hold}, routed from chat moment
  wechat_flatten: FFFFFF|none    # assemble.py --flatten FFFFFF for WeChat/X (drops alpha)
  composited:  programmatic      # ALWAYS — image model never renders this text
```

## Worked example (the tested command chain)

The text + motion + assembly path is a three-call chain — these are the tested forms:

```sh
# 1. composite the caption onto the photo, animated (Mode B)
python3 scripts/kinetic_text.py --base photo.png --text 笑死 --preset bounce \
  --frames 12 --fps 10 --size 240 --out out/xiaosi
# 2. assemble frames+manifest → looping GIF, flattened white for WeChat
python3 scripts/assemble.py --in out/xiaosi --flatten FFFFFF --out out/xiaosi/wechat.gif
# 3. assert dims/size/frames/loop for the target platform
python3 scripts/verify_output.py --file out/xiaosi/wechat.gif --platform wechat
```

If the result is over a platform byte cap, re-run `assemble.py` at a lower `--fps` or a smaller
`--size` until it clears `verify_output.py`.

## Examples (inline)

- `笑死` — fat rounded sans (`--font` a heavy CJK face), white fill + black 8px stroke, **shake**,
  TEARS overlay; bottom band.
- `已读不回` — heavy 宋体, **hold** with a held caret; subject still; the stillness is the joke.
- `摆烂` — marker-flavored sans, muted fill, **bounce** + ZZZ; caption rides the bottom.
- `恭喜🎉` — display bold, gold accent fill, **pop** + CONFETTI; top band, clear of the burst.
- 国潮 `干了这碗` — 书法-flavored weight (`--font` a 书法 `.ttf`), 朱砂红 fill on rice-paper plate,
  slow **pop**; ink register.

## Acceptance

- Every glyph is correct 简体 — programmatic render guarantees this; if any text looks melted or
  doubled, an image model touched it → move the text back to `kinetic_text.py` and regenerate.
- The hero line reads in one second at a **240px** preview, off the face, inside the safe margin.
- One dominant caption + ≤ 1 overlay; fill is flat; stroke is the legibility carrier.
- **Edge matches the format:** a caption that needs a soft outline ships as APNG/WebP or sits on
  a plate; on a transparent GIF the edge is hard by design, not a defect — never sign off a
  "feathered" stroke on a 1-bit-alpha GIF.
- The caption was rendered programmatically by `kinetic_text.py` with a resolved font (an explicit
  `--font` path, or the auto-detected system CJK face — never a guessed bare name) and a stroke
  ≥8px@240, baked on RGB before quantization; the WeChat variant carries the 2px white stroke and
  was assembled with `--flatten FFFFFF`. A caption rendered any other way fails the run, and
  `verify_output.py --platform wechat` is the final gate.
