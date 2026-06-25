# Motion Library

The preset vocabulary for both modes. Motion is **routed from the chat moment**, never named by the
user — they say "笑死" or upload a 摆烂 selfie; the skill picks the preset. Every preset declares its
chat moment, frame plan + timing, 240px readability note, and which mode it leans toward.

Two motion families plus overlays:

- **Bank A — kinetic text** (the caption itself moves): Mode B's home turf, also legal in Mode A.
- **Bank B — frame-loop** (the subject loops): Mode A's home turf (it owns generated frames).
- **Bank C — decorative overlay** (the ≤12% secondary accent): either mode, at most one.

Pick ONE dominant motion per sticker. This file IS the preset bank — the mode-bias detail lives in the
Moment → Preset Reverse Map below, and how frames become bytes lives in `render-pipeline.md`. The text
banks map straight onto `kinetic_text.py --preset {pop|bounce|shake|flash|hold}`; the richer preset
names here (BOUNCE, WIGGLE, GLITCH …) are authoring vocabulary that resolves down to one of those five
mechanical primitives plus the per-frame plan you bake. Timing shorthand: `[in → hold → out]` in frames
at the stated fps. "back" = overshoot-then-settle, "elastic" = overshoot-wobble-settle, "ease-out" =
fast-start-slow-end.

## Global Rules (every preset obeys these)

```text
R1  ONE dominant motion per sticker; everything else is sub-12% secondary accent.
R2  Loop-seamless: last frame must blend into first — ease-to-rest or a verified cyclic seam.
R3  Huge stroked text: cap-height ≥ 38% of canvas, stroke ≥ 8px @ 240px, one outline + soft shadow.
R4  No seizure-flashing (WCAG 2.3.1): ≤ 3 flashes/sec, never global luminance slam — flash = LOCAL glow.
R5  Loop 0.6–1.8s, fps ∈ {25,20,10,5,4,2} only; motion lives in the first 70%, last 30% holds a rest pose.
R6  ≤ 5 words of text, ≤ 2 lines; emotion is carried by motion, not paragraphs.
R7  Anti-alias the stroke, not the fill; keep fills flat-color for crisp small-size.
R8  Mandatory safe-swaps for strict platforms + R4 compliance: FLASH → POP, GLITCH → SHAKE.
```

R5's fps list is a hard constraint, not a preference: GIF delays are integer centiseconds, so only
{25,20,10,5,4,2} fps divide cleanly (4/5/10/20/25/50 cs). Author anything else and `kinetic_text.py`
snaps it to the nearest legal rate, and playback drifts if your frame plan assumed otherwise. **Every
preset below is already authored in a legal fps, with its frame counts recomputed at that fps** — the
tables are the source of truth, copy them verbatim, never re-derive from a "feel" rate. The default
encode rate is **20fps (5cs)**; presets that need a snappier hit run at 25fps (4cs) and slow, calm
ones drop to 10fps (10cs). See `render-pipeline.md` for how the encoder honors these delays.

## Bank A — Kinetic Text (text moves; Mode B home)

| Preset | Chat moment | Mechanics | Frames @ fps `[in→hold→out]` | 240px readability |
| --- | --- | --- | --- | --- |
| **POP** | 赞同 / 强调 / 对！ | scale 0→1.15→1.0 (back) + 1-frame local glow on peak | 20fps `[6→7→2]` 15f ~0.75s | hold at 1.0 is the screenshot; peak ≤1.15 so text never clips |
| **BOUNCE** | 开心 / 期待 / 冲！ | word drops in, squash on contact, 2 decaying re-bounces | 20fps `[3→9→5]` 17f ~0.85s | squash ≤12% height-loss or letters go illegible mid-bounce |
| **SHAKE** | 生气 / 急 / 啊啊啊 | high-freq X/Y jitter ±6px, snap-still on a held angry frame | 25fps `[2→15→3]` 20f ~0.8s | jitter ≤6px or letters smear; end on a still readable frame |
| **TYPEWRITER** | 已读不回 / 欲言又止 / 思考 | reveal char-by-char L→R, blinking caret `▌`, hold | 10fps `[reveal 10→hold 8]` 18f ~1.8s | mono/heavy font; reserve final-width box so layout never reflows |
| **WIGGLE** | 卖萌 / 调皮 / 撒娇 | each letter rotates ±8° on an offset sine (wave through word) | 20fps cyclic 15f ~0.75s | per-letter pivot at base; ≤8° so the baseline still reads |
| **FLASH** | 警告 / 震惊 / ！！！ | stroke tint cycles accent↔white via GLOW, never bg; ≤3/sec | 10fps `[2→glow 2→2]` 6f ~0.6s | R4-critical: glow the stroke only; hold a lit final frame |
| **SLIDE** | 闪现 / 路过 / 溜了 | word slides in from edge, brief hold, exits opposite | 20fps `[6→8→6]` 20f ~1.0s | 2–3px motion-blur trail on in/out only; rest frame sharp |
| **JELLY** | 软萌 / 害羞 / 嘤 | elastic squash-stretch, settles like jello (decaying) | 20fps `[1→14→5]` 20f ~1.0s | cap stretch ±15% on one axis at a time; keep volume so letters don't tear |
| **STAMP** | 拍板 / 成交 / 盖章 | slams down from 1.4 scale, 2px impact shake, dust puff | 25fps `[4→3→11]` 18f ~0.72s | impact frame = peak boldness; one screen-shake sells weight, more jars |
| **GLITCH** | 崩溃 / 无语 / 系统错误 | RGB channel-split ±4px + 2-frame scanline, snap clean | 20fps `[2→glitch 4→hold 10]` 16f ~0.8s | glitch only 2–4 frames; clean held frame mandatory |
| **ZOOM-PUNCH** | 强调到顶 / 重点! | text rushes 0.3→1.0 with radial blur, locks sharp | 25fps `[5→13]` 18f ~0.72s | radial blur ONLY during punch; locked frame fully sharp, centered |
| **DROP-IN** | 报幕 / 上场 / 登场 | letters fall staggered from top, land + tiny bounce | 20fps `[11→7]` 18f ~0.9s | stagger ≤2 frames/letter or the word reads too slowly |

The five `--preset` values `kinetic_text.py` accepts are the mechanical primitives behind this bank:
`pop` (POP / ZOOM-PUNCH / DROP-IN), `bounce` (BOUNCE / JELLY / STAMP), `shake` (SHAKE / WIGGLE /
GLITCH), `flash` (FLASH), and `hold` (TYPEWRITER / SLIDE held-rest). Pass the primitive, then author the
exact `[in→hold→out]` plan from the row above via `--frames` and `--fps`.

## Bank B — Frame-Loop (subject loops; Mode A home)

| Preset | Chat moment | Mechanics | Frames @ fps | 240px readability |
| --- | --- | --- | --- | --- |
| **BLINK** | 呆 / 卖萌 / 听着呢 | 2-frame eye close on a slow cadence | 10fps cyclic 18f ~1.8s, blink at f15–16 | tiny motion = "alive idle"; pair with a static sharp caption |
| **WAVE** | 打招呼 / 再见 / 嗨~ | arm rotates from shoulder pivot, 2 swings, return | 20fps cyclic 14f ~0.7s, ±25° | big readable arc; don't move the body or the caption shifts. **Never ping-pong** (directional) |
| **BOB** | 在 / 摆烂 / 漂浮 / 晚安 | whole body sine up-down ±6px (breathing float) | 20fps cyclic 16f ~0.8s | slowest, calmest motion; ideal under 晚安/在听; never moves the text |
| **TEAR-DROP** | 委屈 / 求饶 / 呜呜 | eyes well up, one tear swells → rolls → drips off-frame | 20fps cyclic 20f ~1.0s | one tear, not a flood; keep face still so caption sits stable |
| **HAND-UP / HAND-DOWN** | 求抱 / 举手 / 投降 / 拜托 | both hands raise (up) or slump (down), 2 staged poses | 20fps `[pose1 8→pose2 hold 10]` 18f ~0.9s | big silhouette change; hold the final gesture 60% as the readable beat |
| **NOD / SHAKE-HEAD** | 同意 / 拒绝 / 嗯嗯 / 不行 | head rotates Y (nod) or X (shake) ×2, return to center | 20fps cyclic 16f ~0.8s | pivot at the neck; caption below stays put; center-rest = screenshot |
| **STOMP** | 急 / 催 / 快点! | body squash + foot stomp + 2px ground-shake ×2 | 20fps cyclic 16f ~0.8s | ground-shake ≤2px; caption mustn't ride the shake |
| **FALL-FLAT** | 摆烂 / 累瘫 / 我不行了 | character topples sideways, lies flat, tiny breathing twitch | 20fps `[stand→topple 6→lie+twitch 12]` 18f ~0.9s | the lying frame IS the meme; twitch ≤2px |

**Ping-pong (boomerang) doubles frames for free and is automatically seamless** — use it for there-and-back
motion (BLINK, BOB, NOD, JELLY). **Never ping-pong directional motion** (WAVE, SLIDE, STOMP-exit): a one-way
wave that rewinds reads as broken — author a true cyclic loop instead. Mode A records this choice in
`manifest.json` as `loop_strategy` (`directional | cyclic | boomerang`); `assemble.py` reads it and
expands boomerang frames at encode time. `frame-generation.md` describes how Mode A keeps a model sheet
consistent before that handoff.

## Bank C — Decorative Overlay (≤12% accent; at most one)

| Overlay | Chat moment | Mechanics | Frames @ fps | 240px readability |
| --- | --- | --- | --- | --- |
| **SPARKLE** | 厉害 / 闪亮 / ✨牛✨ | 3–5 4-point stars twinkle in/out on offset phase | 20fps cyclic 16f ~0.8s | in negative space, never over text strokes; twinkle = scale 0→1→0, not flash |
| **HEARTS** | 喜欢 / 比心 / 撒爱 | small hearts float up + drift + fade, staggered emitter | 10fps cyclic 14f ~1.4s | 2–4 hearts max; off the caption baseline; soft fade, no pop-disappear |
| **SPEED-LINES** | 冲 / 急速 / 快! | radial/horizontal streaks pulse toward motion direction | 20fps cyclic 16f ~0.8s | behind the subject only; thin, accent-color, low opacity so text stays on top |
| **SWEAT-DROP** | 尴尬 / 慌 / 无语 | one big anime sweat bead pops at temple, slides, drips | 20fps cyclic 18f ~0.9s | one big bead > many small; beside the face, never on text |
| **TEARS (comic)** | 笑死 / 哭笑 / 假哭 | twin fountain tear-streams spurt sideways (笑哭 style) | 20fps cyclic 14f ~0.7s | big exaggerated arcs in negative space; bright accent; reads instantly |
| **STEAM / ANGER-VEIN** | 生气 / 冒火 / 气炸 | 💢 vein pops + 2 steam puffs rise from head | 20fps cyclic 16f ~0.8s | vein near temple/fist; steam thins as it rises; hot accent color |
| **CONFETTI** | 庆祝 / 恭喜 / 🎉 | multi-color bits burst once, then gently fall + spin | 20fps `[burst 4→fall 16]` 20f ~1.0s | burst on f1 as the hook; falling bits sparse so caption stays clear |
| **ZZZ** | 困 / 晚安 / 摸鱼睡 | stacked Z's rise + scale up + fade, staggered | 10fps cyclic 18f ~1.8s | 3 Z's ascending off the head; slow + sleepy; pair with BOB |
| **QUESTION-MARKS** | 疑惑 / ??? / 看不懂 | 1–3 ❓ pop above head with a tiny wobble, fade | 20fps cyclic 18f ~0.9s | wobble ±5°, upper side, so face + caption stay readable |
| **DUST-PUFF** | 溜了 / 闪现 / 跑路 | cartoon dust cloud where the subject was, subject gone | 20fps `[puff 7→dissipate 9]` 16f ~0.8s | pairs with SLIDE / character exit; dust = fast exit punctuation |

## Moment → Preset Reverse Map

The skill reads the chat moment from intake and picks here. Primary = one Bank A or Bank B preset;
overlay = at most one Bank C. The **mode-bias** column is the default lean — Mode A favors Bank B
(subject loops it can generate), Mode B favors Bank A (text over an untouched still). Whether the upload
is even a Mode-B candidate is decided upstream by the Face-Truth Gate; see `SKILL.md (Face-Truth Gate)`.

| Chat moment | Primary (A text / B frame-loop) | Overlay | Mode bias |
| --- | --- | --- | --- |
| 笑死 / 哈哈哈 | SHAKE / JELLY | TEARS | B text / A subject |
| 赞同 / 对对对 | POP / NOD | SPARKLE | either |
| 已读不回 / 在吗 | TYPEWRITER (held caret) | — (stillness is the joke) | B |
| 摆烂 / 躺平 | FALL-FLAT / BOB | ZZZ | A |
| 生气 / 气死 | SHAKE / STOMP | STEAM / ANGER-VEIN | A |
| 求饶 / 拜托 / 求抱 | HAND-UP / TEAR-DROP | SWEAT-DROP | A |
| 晚安 / 困了 | BOB (slow) | ZZZ | A |
| 震惊 / 啊？ | ZOOM-PUNCH / FLASH→POP | QUESTION-MARKS | either |
| 喜欢 / 比心 | JELLY / WIGGLE | HEARTS | either |
| 冲 / 快点 | SLIDE / STOMP | SPEED-LINES | either |
| 庆祝 / 恭喜 | STAMP / DROP-IN | CONFETTI | either |
| 溜了 / 跑路 | SLIDE-out | DUST-PUFF | B |
| 厉害 / 牛 | POP / STAMP | SPARKLE | either |
| 尴尬 / 无语 | GLITCH→SHAKE | SWEAT-DROP | either |
| 思考 / 欲言又止 | TYPEWRITER / BLINK | QUESTION-MARKS | either |
| 登场 / 报幕 | DROP-IN | CONFETTI | A |

## Worked Examples (moment → preset + caption)

- 同事甩活过来 → **FALL-FLAT** subject (Mode A) + **ZZZ** overlay, caption `我不想干了`. Topple held in
  the last 30%; that lying frame is what gets sent.
- 对方已读不回 → **TYPEWRITER** text (Mode B, real photo untouched), caption `在吗…` with a blinking caret.
  Stillness is the joke; no subject motion, no overlay.
- 群里有瓜 → **POP** text + **SPARKLE**, caption `吃瓜`. Either mode; if it's the user's real face, Mode B
  keeps it crisp and pops only the word. The Mode-B path runs straight through `kinetic_text.py`:
  `python3 scripts/kinetic_text.py --base photo.png --text 吃瓜 --preset pop --frames 12 --fps 10 --size 240 --out out/chigua`.
- 朋友考过了 → **STAMP** text (Mode A character) + **CONFETTI**, caption `恭喜`. Slam on impact, confetti
  bursts on f1.
- 撒娇要抱抱 → **JELLY** subject (Mode A) + **HEARTS**, caption `抱抱我`. Decaying wobble, 2–3 hearts in the
  negative space above the head.

The canonical tested run end-to-end (caption `笑死`, BOUNCE primitive, WeChat 240px) is:

```bash
python3 scripts/kinetic_text.py --base photo.png --text 笑死 --preset bounce --frames 12 --fps 10 --size 240 --out out/xiaosi
python3 scripts/assemble.py --in out/xiaosi --flatten FFFFFF --out out/xiaosi/wechat.gif
python3 scripts/verify_output.py --file out/xiaosi/wechat.gif --platform wechat
```

## Mode-Specific Production Defaults

```text
canvas:     square, ≥512×512 authoring; design-checked at 240px preview
fps:        default 20fps (5cs); snappy hits (SHAKE/STAMP/ZOOM-PUNCH) 25fps (4cs);
            slow/calm (TYPEWRITER/BLINK/FLASH/HEARTS/ZZZ) 10fps (10cs) — never re-derive,
            COPY each preset's authored fps + frame count; the tables already obey R5
loop:       0.6–1.8s, seamless; motion in first 70%, held rest pose in last 30%
text:       cap-height ≥38%, stroke ≥8px@240, one outline + soft shadow, flat fill.
            kinetic_text.py auto-detects a system CJK face (STHeiti / Hiragino / PingFang / Noto);
            override with --font /path/to/bold-CJK.ttf when you want a specific bold weight
budget:     1 dominant motion + ≤1 overlay; overlay ≤12% visual weight
flash:      local glow only, ≤3/sec, never global luminance slam; strict platform → FLASH→POP, GLITCH→SHAKE
mode A:     prefer Bank B (subject loops); BLINK/BOB/NOD/JELLY are ping-pong-friendly; vary ONE element/frame
mode B:     prefer Bank A (kinetic text on the real still) + cheap photo motion (Ken-Burns / bounce / jelly)
            text is baked on RGB before quantization → set manifest text_baked=true so the assembler skips dithering it
```

There is no shipped `fonts/` directory — `kinetic_text.py` finds a system CJK face on its own, and the
only knob you ever pass is `--font /path/to/bold-CJK.ttf` when you want a specific weight. Don't write a
font path into the skill that assumes a bundled file; it would dangle.

Mode-B photo motion uses `photo_puppet.py`; Mode-A model sheets use `sheet_to_sticker.py`.
`sheet_to_sticker.py` can animate exact Chinese captions with
`--text-motion pop|pulse|bounce|shake|none`, then assemble and verify. Inline Pillow loops are only
emergency fallbacks.

A preset's fps is part of the preset, not a free knob: every `[in→hold→out]` count in the tables is
already counted at the fps printed beside it and lands inside R5's 0.6–1.8s window. Take a preset's
fps AND its frame plan together; never keep the timing string from one rate and encode at another, or
the loop drifts. To fit a platform byte budget there is no separate sizing tool — re-run `assemble.py`
at a lower `--fps` (or regenerate at a smaller `--size`) until the file lands under the cap, then
re-run `verify_output.py --platform X` to confirm dims/size/frames/loop. The scripts are Pillow-only —
no ffmpeg or probe step required; if `gifsicle` happens to be on PATH, `assemble.py` uses it to shrink
the file further. Platform exports follow the same path: `assemble.py --flatten RRGGBB` for surfaces
that drop alpha (WeChat / X), then `verify_output.py --platform X`; the per-platform caps live in
`platform-specs.md`.

Two tradeoffs to flag when routing. **TYPEWRITER** is the longest loop (18f @ 10fps ≈ 1.8s, R5's
ceiling) and can feel slow in a fast picker — keep the string ≤4 words and let the caret-blink carry
the loop; do not push it past 1.8s. **GLITCH** and **FLASH** sit nearest the R4 seizure line — both are
specced as *local* glow / channel-split with a mandatory clean held frame, never a global strobe; if a
platform is strict, take the R8 swap for the same emotional beat at zero flash-risk.
