# Aesthetic Routing

The animated sticker's visual register is chosen BY THE SUBJECT — the subject's vibe, the niche,
the mood — automatically. The user does not name a style. A 自拍搞怪 set routes to bold flat
cartoon; a 萌宠 set routes to rounded pop; a 国潮/古风 avatar routes to ink-wash. Route first,
LOCK the register into the identity DNA, then the motion presets and the loop play inside it.

This is the same router as sibling `sticker-set` (the static-character skill), extended to two
modes. Run the Face-Truth Gate in SKILL.md (Face-Truth Gate) first; it returns the MODE. The
register is routed the same way in either mode, and feeds BOTH so they look like one family:

- **MODE A (frame-gen)** generates 2–8 consistent frames then loops them. Routing writes the look
  into the model-sheet / per-frame prompt — every frame and the loop share the register. When Mode A
  edits a real photo, the register is what the AI restyles the face INTO: this stylizes/alters the
  real face, so the output is a stylized likeness, NOT the byte-true person (say so, per the
  honesty caveat in SKILL.md (Face-Truth Gate)).
- **MODE B (photo + kinetic)** keeps the real photo byte-for-byte. The register lives on the
  composited TEXT system only — the CJK display font you pass to `kinetic_text.py --font`, stroke,
  palette, WeChat white-stroke flag. The photo is untouched; routing only decides how the crisp
  overlaid text and effects look.

## Style Menu (Mode A image-gen — where the variety lives)

On a strong image model (Codex), a sticker set can be rendered in genuinely DIFFERENT styles.
The router still picks a default from the subject/vibe, but the user can name a style outright,
and these are the distinct, recognizable looks to offer. Bake the chosen style into the
model-sheet prompt and LOCK it across the whole set (one style per pack):

- **3D 盲盒 / 泡泡玛特风** — soft-shaded vinyl toy, big head, glossy, studio light. (cute, premium, viral)
- **像素风 / pixel** — chunky low-res pixels, limited palette, retro. (small files, meme-y)
- **手绘涂鸦 / 蜡笔** — crayon / marker doodle, wobbly outline, paper texture. (warm, funny)
- **水墨国潮 / 工笔** — ink-brush or fine-line, rice-paper, 朱砂红 + 印章. (国风, classy)
- **厚涂 / semi-realistic** — painterly thick brush, rich light. (high颜值, illustration-grade)
- **扁平矢量 / flat** — clean flat shapes, bold color, no shading. (modern, brand-friendly)
- **日系扁平 / line-art** — thin even line + flat fills, kawaii. (萌, clean)
- **美式卡通 / bold cartoon** — thick outline, exaggerated expression. (沙雕, high传播)
- **真实摄影贴纸 / photo-real cutout** — a real-looking subject knocked out with a sticker border. (for pets/products)

Each is a single LOCKED look for the pack — never mix styles in one set. The cheap code-render
fallback (Mode C, `scripts/cutie.py`) covers the 圆润 团子 look without an image model; for any
other style, you need Mode A on Codex.

Neither mode does true talking-head / smooth subject animation — that needs a video model and is out
of scope. The register dresses the look; the motion library (`motion-library.md`) carries the beat;
the deterministic assembler (`render-pipeline.md`) turns frames into bytes. No image model touches
the encode step in either mode.

## Route by subject vibe → register

| Subject / vibe signal | Register (master-styles token family) | Tokens to apply | Default motion family |
| --- | --- | --- | --- |
| 自拍搞怪 / 沙雕 / 整活 / 梗 | bold flat cartoon (大头) | oversized head, thick black outline, punchy saturated palette, big stroked caption ≥38% cap-height | SHAKE / JELLY / ZOOM-PUNCH + big caption — ONE dominant motion + ≤1 overlay |
| 宠物 / 萌宠 / 软萌 mascot | 圆润流行 (Olimpia Zagnoli) | soft rounded organic silhouette, tested high-saturation flat fill, 2px white stroke, big eyes | BLINK / BOB / JELLY + HEARTS |
| **国潮 / 古风 / 古装 / 武侠 / 仙侠 / 神兽 头像或主题** | **水墨 / 工笔 (Chinese ink)** | ink-brush or fine 工笔 contour, rice-paper / warm ground, 朱砂红 + 石青 accent, a tiny 印章; caption set as 书法 | BOB (slow), TYPEWRITER (书法-flavored) |
| 职场 / 高级 / 商务克制 / brand-clean | minimal editorial (McFetridge / Swiss) | matte muted palette, clean contour, one accent, generous negative space; restrained type | minimal POP, slow BOB (sub-12% motion) |
| 情侣 / 节日 / 庆祝 | warm festive | warm multi-accent + gold, soft daylight, friendly display weight | STAMP / DROP-IN + HEARTS or CONFETTI (pick ONE overlay) |
| hype / 冲 / 牛 / gaming / 热血 | bold pop + anime | speed-lines, saturated accent, hard black outline, cel glow | POP / STAMP / ZOOM-PUNCH; SPEED-LINES *or* a glow = the one overlay, never both |
| 丧 / 摆烂 / 打工人 / tired | desaturated muted | slumped silhouette, marker outline, hand-scrawled caption | FALL-FLAT / BOB + ZZZ |
| 撒娇 / 害羞 / 卖萌 | pastel rounded | soft shadow, blush dots, rounded letterforms | WIGGLE / JELLY + HEARTS |
| 警告 / 震惊 / 急 / 气 | high-contrast heavy | hot red-orange, jagged bold weight | SHAKE / STOMP / ZOOM-PUNCH + STEAM (FLASH→POP on strict platforms) |
| (MODE B real photo, any vibe) | look lives on the TEXT system | a bold CJK display font (passed via `kinetic_text.py --font`, or the auto-detected system face), stroke ≥8px@240, routed palette, WeChat white-stroke flag; **photo untouched** | Bank A kinetic text + cheap photo motion (Ken-Burns / bounce / jelly) |

## How to route

1. Read the subject source + the subject's vibe + the mood. Run the Face-Truth Gate in
   SKILL.md (Face-Truth Gate) first; it decides MODE. The register is routed the same way in
   either mode.
2. Pick the register from the table. When two fit, pick the one a follower of this niche expects
   (国潮头像 belongs on rice paper, not a neon grid). **Culture wins over cuteness:** a 古风 subject
   routes to ink even when it is cute.
3. Apply the register's tokens. In MODE A, write them into the model-sheet and every per-frame
   prompt so the whole loop shares one look. In MODE B, apply them to the composited text/effects
   only — never repaint the photo.
4. LOCK the register into the identity DNA before any frame or motion work — it is a frozen trait,
   the consistency moat. The motion presets and the seamless loop run INSIDE the register, unchanged.
5. The user may override; the default is the routed register, never a generic gradient.

## Compatibility rule

The host is a tiny looping sticker that must stay legible at a 240px preview and loop clean. The
restraint laws override the router for EVERY register — loud or clean — not just the clean ones.
Routing picks the look; it never buys extra motion, extra overlays, or extra flash. Only route to
registers whose restraint survives the host:

- The caption must read in one second at 240px — keep stroked text ≥38% cap-height, one outline,
  flat fill (`motion-library.md` R3). Never route to a register that buries the caption under
  ornament.
- **ONE dominant motion + at most ONE overlay, full stop** (`motion-library.md` R1). This caps every
  register, including the loud ones: a glow, a cel-glow, speed-lines, sparkles, confetti, and steam
  are all Bank C overlays — each one SPENDS the single-overlay budget. A hype route is POP *plus
  one* of {SPEED-LINES, glow}, never POP + SPEED-LINES + glow; a 庆祝 route is STAMP *plus one* of
  {CONFETTI, HEARTS}, never both. If a register's token list names a glow AND speed-lines, the router
  drops one before it ships.
- **Glow / cel-glow is local and flash-budgeted** (`motion-library.md` R4): it tints the text stroke
  or a small area only — never a full-frame luminance slam — and pulses ≤3 times per second. Glow is
  the one overlay, not a free extra on top of one; on a strict platform it takes the FLASH→POP /
  GLITCH→SHAKE safe-swap (R8). A loud register never earns a strobe.
- The loop must be seamless and quiet enough to send forever — clean subjects (职场/高级/brand)
  cap total motion + overlay below 12% (slow BOB, minimal POP); never strobe a clean set.
- Never route a clean sticker to a maximalist register (Yokoo collage, Klimt ornament). If the
  vibe is genuinely loud (沙雕/hype/庆祝), bold flat cartoon and festive pop are allowed — but the
  same R1/R3/R4 caps hold: one motion, one overlay, readable caption, no strobe, and the held rest
  frame (last 30% of the loop, R5) stays clean.

## The ink register (国潮 / 古风 stickers, often missed)

For 国潮 / 古风 / 古装 / 武侠 / 仙侠 / 神兽 avatars or themes, default to: warm rice-paper or flat
warm ground, an ink-brush or fine 工笔 contour, generous 留白, the caption set as brush 书法, and a
single 朱砂红 / 石青 accent with a tiny red 印章 as the one warm punctuation — no gradients, no neon.
Motion stays calm (slow BOB, or a 书法-flavored TYPEWRITER reveal) so the ink restraint holds. In
MODE A this governs the model sheet and every frame; in MODE B it governs only the overlaid 书法
caption and seal, leaving the real photo untouched. See the East-Asian / 工笔 section of the
master library for the transferable tokens.

## Font note (no shipped fonts)

There is no bundled `fonts/` directory in this skill — drop any "shipped font" assumption. The
caption font is something you supply at render time: pass a bold CJK face to
`kinetic_text.py --font /path/to/bold-CJK.ttf`, or omit `--font` and let `kinetic_text.py`
auto-detect a system CJK font (STHeiti / Hiragino / PingFang / Noto). Either way the routed
register decides the stroke, palette, and weight; the font path is just how that look gets drawn.
