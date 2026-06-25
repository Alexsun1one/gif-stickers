# Prompt Template

Two modes, one pipeline. Templates for both are below. Run the Face-Truth Gate first
(`SKILL.md (Face-Truth Gate)`) — it returns `MODE_A` or `MODE_B`, and you fill in only that
mode's template. Both modes emit the SAME frame contract — zero-padded `frames/f%04d.png` plus a
`manifest.json`, the contract documented in `render-pipeline.md` — then the SAME deterministic
assembler (`assemble.py`) turns those frames into bytes. The agent WRITES and RUNS the assembly
code; no image model touches the encode step.

- **MODE A** generates 2–8 consistent frames (theme-invented subject, OR by using a reference photo
  as a face/identity anchor) then loops them. A real-photo A run can redraw the scene, body, action,
  props, and background, and it may keep the face recognizably consistent, but it still re-synthesizes
  face pixels. Say this out loud.
- **MODE B** does not use an image model. `kinetic_text.py` animates captions over a photo;
  `photo_puppet.py` makes the original photo itself move by deterministic pixel transforms. Use
  B-photo-puppet when the user wants the same exact face pixels moving.

Neither mode does true talking-head or smooth facial animation — that needs a video model. This skill
makes a small looping sticker, not lip-sync.

## Token-Safe Artifact Rules

These are mandatory in Codex-like hosts:

- Do not paste, print, grep, or summarize generated image base64/result blobs.
- Keep references to generated assets as filesystem paths (`savedPath`) plus tiny metrics
  (dimensions, file size, verification result).
- For A-face-anchor, generate at most 2 sheets in the first pass. A full pack needs explicit
  high-budget approval and still runs in batches of max 4 image-gen calls.
- Prefer a single model sheet that slices into multiple frames over separate image calls per frame.
- Keep shell command output capped; never dump session JSONL or large manifests.

## MODE A — Planning Template

```text
Use $gif-stickers, MODE A. First plan, do not generate yet.

Subject source:
{theme-only / user-photo / pet-photo / brand-mascot}   ← if user-photo, print the honesty caveat

Chat moment(s) this loop is for:
{笑死 / 赞同 / 摆烂 / 求饶 / 晚安 / 生气 / ...}

Target platform(s):
{wechat / line / telegram / discord / twitter / generic}

Token budget route:
{medium A-smoke: <=2 image-gen calls now / high A-pack: <=4 image-gen calls per batch}

Return:
- subject (one line) + identity DNA (3-5 fixed traits: silhouette, palette, head shape, line, accessory)
- visual register (routed by vibe, style-routing.md), LOCKED across every frame
- identity-lock rung (frame-generation.md): A1 model-sheet / A2 reference-edit / A3 fixed-seed / A4 same-seed
- per loop: chat moment | the ONE element that varies per frame | motion_preset | loop_strategy (boomerang/cyclic/directional)
- frame_count (2-8) and fps ∈ {25,20,10,5,4,2}
- image-gen call budget for this pass + explicit stop point
- QA risks
```

## MODE A — Frame Generation Prompt (model-sheet first)

Generate ONE model sheet that locks identity by construction, then hand the saved PNG path to
`scripts/sheet_to_sticker.py`. The helper slices the sheet into `frames/f%04d.png`, assembles the
GIF, and runs verification with small logs. In Mode A, the image model should render the caption
natively inside each generated cell; programmatic text is only a repair/platform-specific fallback.
Vary EXACTLY
ONE element per frame; hold everything else identical (the register-before-stacking rule in
`frame-generation.md`).

```text
Generate ONE character model sheet for an animated chat sticker.

Square 1:1 per cell, clean transparent or flat single-color background, subject centered with margins.

Subject:
{one subject — what it is, in one sentence}

Visual register — routed by vibe (style-routing.md), LOCKED across every frame:
{圆润流行 (Zagnoli) / 水墨·工笔 ink (国潮·古风, 朱砂红+石青 accent, tiny 印章) / 减法扁平 / 剪纸纯色 / 大头卡通}

Identity DNA — keep IDENTICAL in every frame (drift = flicker):
- silhouette / body shape, palette (2-4 fixed roles), head shape & face layout, line weight, one signature accessory

Layout — a 1×N or 2×N grid of the SAME subject, one varied element per cell:
{e.g. 1×4: arm down → arm mid → arm up → arm mid  (a wave loop)}
- identical lighting, background, framing, and body across all cells
- ORIGINAL subject — not Disney / 宝可梦 / LINE FRIENDS / 玲娜贝儿 / 蛋仔 or any existing IP

Caption — render this exact Chinese text natively inside every cell, correct characters, no other text:
"{caption, ≤ 6 字}"
- keep it big, readable at 240px, high-contrast, top or bottom, off the face
- treat it as part of the sticker design, not a placeholder for later overlay
```

After the sheet comes back, use the sheet helper by default:

```bash
python3 scripts/sheet_to_sticker.py --sheet /abs/path/sheet.png --grid 1x4 \
  --platform wechat --loop cyclic \
  --out out/xiaosi
```

Use `--caption` / `--text-motion` only to repair failed native text or when the user explicitly asks
for programmatic animated text. Inline Pillow slicing is a fallback only if the helper is unavailable.

## MODE A — Face-Anchor Edit Prompt (AI redraw, same-person goal)

When the subject is a user/pet photo and the user accepts AI-redrawn frames. This is the route for:
"照片里的脸尽量保留同一个人，但场景/身体/动作/道具可以重绘，多帧合成 GIF." Print the caveat
verbatim FIRST. Branch every frame/sheet from the ONE base image — never chain edit→edit→edit (the
drift trap in `frame-generation.md`). Generate **at most 2 candidate sheets in the first pass**, then
select and assemble the best face-consistent one. Continue to a pack only after the user accepts the
high-budget route.

```text
Honesty caveat (surface to the user before generating):
"这是把你照片作为身份参考重新生成一组动图帧：脸会尽量保持像同一个人，但五官细节、皮肤和表情会被 AI 重绘；
场景、身体动作和构图也可能重绘。要逐像素保留真实的脸，请改用 MODE B-photo-puppet。"

Generate ONE 1x4 animated-sticker model sheet from the ATTACHED base portrait.

Use the attached portrait as the identity reference. Keep the same person's face identity across all
four cells: same face shape, glasses, haircut/hairline, skin tone, age impression, and overall likeness.
The body pose, hands, props, simple scene, and sticker composition may be redrawn to serve the action.

Visual register (style-routing.md), LOCKED across all frames: {…}

Action loop, one varied element:
{e.g. neutral -> shocked -> more shocked -> settle}

Square 1:1 per cell, clean flat background, subject centered with margins.
Same lighting, style, crop, and background across cells.
Caption — render this exact Chinese text natively inside every cell, correct characters, no other text:
"{caption, ≤ 6 字}"
- big, high-contrast, top/bottom placement, off the face
- the caption may subtly shift/scale between cells if that helps the motion, but characters must stay correct
Important: reject any frame that looks like a different person.
```

After generation:

```text
1. Copy the generated PNG from savedPath into the project output directory.
2. Print only: filename, dimensions, byte size.
3. Run `sheet_to_sticker.py` to slice locally, preserving the native caption, then assemble and verify.
   Add programmatic caption only to repair failed native text or by explicit user request.
4. Do not inspect session JSONL or print image-generation result payloads.
5. Stop after the A-smoke preview unless high-budget continuation was explicitly requested.
```

## MODE A — Batch Template (a whole themed SET)

A pack is a SET, not random loops. Declare the identity/register ONCE and a fixed seed pack-wide (the
batch/SET section of `frame-generation.md`); platform set-counts are guardrails (WeChat 16/24
all-animated-or-all-static; LINE 8/16/24). The agent loops generation, then runs the shared assembler
per loop.

```text
Use $gif-stickers, MODE A, batch a SET. High budget was explicitly accepted.

Identity DNA (declared ONCE, frozen pack-wide): {…}
Visual register (LOCKED): {…}      Fixed seed (pack-wide): {seed}
Platform + set count: {wechat 16 / line 24 / ...}   ← refuse non-allowed counts
Image-gen budget for this pass: max 4 calls, then stop for review

Set manifest — one row per sticker:
[ (label, chat_moment, the ONE varied element, motion_preset, loop_strategy) , ... ]

Per sticker: generate a model sheet / edit sheet with native caption → copy savedPath only → run
`sheet_to_sticker.py` without `--caption` by default → verify_output.py result. Use `--flatten auto` unless a
specific platform color is required.
Return one report per sticker: path | chat moment | rendered caption (if any) | on-model? | pass/regenerate.
```

## MODE B — Build Spec (real photo, deterministic)

No image model. Choose one B subpath:

- **B-kinetic-text**: photo stays still; only the composited caption is animated by `kinetic_text.py`.
- **B-photo-puppet**: original photo pixels move as one layer via `photo_puppet.py` (scale/rotate/
  translate/bob/shake/stamp/slide), with optional caption/overlay. This is the face-exact route for
  "same face, image moves."

```text
Use $gif-stickers, MODE B. Real photo preserved exactly.

photo path:        {/abs/path/to/photo.png}
caption text:      "{exact text, ≤ 6 字, correct Chinese characters}"
chat moment:       {笑死 / 已读不回 / 摆烂 / ...}
routed register:   {text system from style-routing.md — font role, palette, WeChat white-stroke flag}
motion preset:     {B-kinetic-text: pop|bounce|shake|flash|hold OR B-photo-puppet: nod|shake|bob|pop|stamp|slide|sleep|question}
loop_strategy:     {boomerang / cyclic / directional}
fps:               {∈ 25,20,10,5,4,2}     frame_count: {N, e.g. 12; held frames merge to ~8 effective}
position:          {top / bottom}
platform(s):       {wechat / line / telegram / discord / twitter / generic}
```

## MODE B — Deterministic Render Invocation

`kinetic_text.py` draws the caption programmatically on RGB BEFORE quantization with a stroke auto-sized
to the canvas (~8px @240) — that is why Mode B text never muddies. There is NO shipped font folder: pass
your own bold CJK face with `--font /path/to/bold-CJK.ttf`, or omit `--font` and let the script auto-detect
a system CJK font (STHeiti / Hiragino / PingFang / Noto). Pipeline order, encoders, and the byte-budget
ladder live in `render-pipeline.md`.

```text
# 1. Bake the crisp caption on the untouched photo into RGBA frames + manifest.json
#    (Pillow-only; auto-detects a system CJK font, or pass --font /path/to/bold-CJK.ttf):
python3 scripts/kinetic_text.py --base photo.png --text 笑死 --preset bounce \
    --frames 12 --fps 10 --size 240 --pos bottom --loop cyclic --out out/xiaosi

# 2. Assemble frames + manifest into a small looping GIF (Pillow-only; uses gifsicle if on PATH).
#    --flatten RRGGBB for platforms that drop alpha (WeChat/X); omit to keep transparency:
python3 scripts/assemble.py --in out/xiaosi --flatten FFFFFF --out out/xiaosi/wechat.gif

# 3. Refuse non-compliant output — asserts dims/size/frames/loop, exits nonzero on breach:
python3 scripts/verify_output.py --file out/xiaosi/wechat.gif --platform wechat
```

Transparent variant (no photo, flat ground, kept transparent through assembly):

```text
python3 scripts/kinetic_text.py --base "" --text 赞同 --preset pop --frames 10 --fps 10 --size 240 --out out/zantong
python3 scripts/assemble.py --in out/zantong --out out/zantong/sticker.gif   # keeps transparency
python3 scripts/verify_output.py --file out/zantong/sticker.gif --platform generic
```

Optional cheap photo motion (Ken-Burns / bounce) is NOT a separate script — if you want the still photo
itself to move, use `photo_puppet.py`:

```text
python3 scripts/photo_puppet.py --base photo.png --text 离谱 --action question --overlay question \
    --frames 12 --fps 10 --size 240 --pos top --loop cyclic --out out/lipu
python3 scripts/assemble.py --in out/lipu --flatten FFFFFF --out out/lipu/wechat.gif
python3 scripts/verify_output.py --file out/lipu/wechat.gif --platform wechat
```

## Fallbacks

- **No encoder needed:** the scripts are Pillow-only — there is NO ffmpeg/gifski/probe step to run.
  If `gifsicle` happens to be on PATH, `assemble.py` uses it to shrink the file further; otherwise it
  falls back to Pillow's own optimizer. Never claim a probe script or fake a finished GIF.
- **Over the platform byte cap:** re-run `assemble.py` at a lower `--fps` (re-bake with a smaller
  `kinetic_text.py --fps`) or a smaller `--size` until `verify_output.py` passes. That down-ladder
  is the whole budget story — no separate budget script.
- **Image-only agent (no shell):** Mode A can produce frames but cannot encode or batch; hand off the
  `frames/` for manual ezgif assembly, or decline. Mode B needs only a shell (no image model).
- **Mode A drift:** if a frame goes off-model, regenerate it FROM the model sheet, do not chain-edit
  the bad output. On rung A4 only, warn that loops over 2 frames will wobble.
- **Caption renders wrong in Mode A:** first repair/regenerate the sheet with shorter text, stronger
  type constraints, and clearer top/bottom caption placement so the image model renders the caption
  natively. Use `sheet_to_sticker.py --caption ... --text-motion ...` only when the user explicitly
  chooses a post-production/animated-text repair or the native text route fails after a repair pass
  and you clearly report that exception.
