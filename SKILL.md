---
name: gif-stickers
description: >-
  Generate or plan a small looping animated sticker (动态表情包 / 会动的表情)
  and assemble it into a real looping GIF. Use when a user wants a GIF表情包,
  动图表情, 动态表情, 微信GIF表情, 动态贴纸, says 把我的表情包做成会动的 /
  做一套会动的表情 / 用我的照片做动图表情 / 给头像做个动图 / 生成会动的表情,
  or wants an animated sticker pack, a gif sticker from a photo, or an
  animated sticker set for WeChat/LINE/Telegram/Discord/X. Three
  budget-gated modes: A generates AI-redrawn frames/sheets and loops them
  (premium, token-gated; real-photo A is a likeness, not face-preserving);
  B keeps the real photo pixels and animates text/effects/photo motion
  deterministically; C renders a pure-code mascot. Do not use for: drawn
  static sticker packs (use sticker-set), single covers (use cover-pop),
  logos, video editing, or true talking-head / lip-synced facial animation
  (that needs a video model, not this skill).
---

# GIF Stickers

GIF Stickers turns a subject into a small looping animated sticker, then encodes it into a real send-ready GIF. A still sticker is a reply; an animated one is a reply with a heartbeat — but only if the loop is seamless, the file fits the platform's byte budget, and any text stays crisp.

The skill is the family's first hybrid: the assembly step is bytes, not a prompt, so the agent RUNS the shipped scripts to encode the frames — pure Pillow (with `gifsicle` used to shrink further if it happens to be on PATH). Mode A uses image generation for premium frames; Modes B/C are deterministic. The encoder needs nothing beyond Pillow.

## Modes & Tooling

This skill is at its best on an agent with **strong image generation — Codex (Image 2.0)** or any agent with a strong image model. That is where **quality and DIFFERENT STYLES** come from: one sticker set can be 3D 盲盒 / 像素 / 手绘涂鸦 / 水墨国潮 / 厚涂 / 扁平矢量 / 真实摄影贴纸 — see the style menu in `references/style-routing.md`. The code-render mode is the cheap floor that runs anywhere (no image model), but it is a floor, not the ceiling.

Token cost is now a first-class constraint. Image-gen outputs can be very expensive in Codex because
large generated PNGs and their metadata may enter the conversation context. Do not treat "better
visuals" as permission to run an open-ended A route. Every job runs the **Token Budget Gate** below.

THREE modes — pick one per job at the gate, never guess:

- **Mode A — image-gen frames (premium, budget-gated).** Generate 2–8 consistent frames per sticker with a strong image model — from a theme, or by editing a reference photo — and loop them. This is where **style variety and 颜值** live. Best for themed SETS and invented characters. **Honest:** editing a real photo ALTERS/stylizes the face (a likeness, not face-preserving). Needs image-gen + code exec → effectively Codex-class. For real-photo A-face-anchor packs, start with a tiny smoke batch and stop for review; never blindly generate 8-10 large sheets.
- **Mode B — face-preserving photo animation (runs anywhere).** Keep the real photo's face pixels, no image model. There are TWO subpaths:
  - **B-kinetic-text**: `scripts/kinetic_text.py` keeps the photo still and animates crisp composited text/effects. Use when the reply is mainly a caption.
  - **B-photo-puppet**: `scripts/photo_puppet.py` makes the photo itself move with deterministic scale/rotate/translate/bob/shake/stamp/slide plus small overlays. Use when the user says "让这个图动起来 / 每张图不一样但脸一样 / 保留同一张脸". This is the correct face-preserving route for "the person moves" without generative face resynthesis.
- **Mode C — code-rendered mascot (cheapest floor, runs anywhere, near-zero cost).** A pure-Pillow cute 团子 or 火柴人 + name/word, animated. No image model: `scripts/cutie.py` (polished 团子, squash-&-stretch, supersampled, 8 emotions) or `scripts/stickman.py` (minimal). Use when there is no image model, or for a fast, free, on-brand set with the user's name on it.

All three converge on ONE interface — a frames dir + `manifest.json` (the frame contract in `references/render-pipeline.md`) — handed to one deterministic assembler (`scripts/assemble.py`). The assembler never knows how the frames were made.

## Workflow

1. Read the request: subject source, real-face-preservation need, deliverable, chat moment(s), target platform(s).
2. Run the **Face-Truth Gate** (below) to route MODE A or MODE B — answered from intake, not guessed.
3. Run the **Token Budget Gate** (below). Default is low-cost B-photo-puppet for real-photo jobs unless the user explicitly accepts AI-redraw and the token budget.
4. Route the look by subject vibe (国潮/古风 → 水墨, 萌宠 → 圆润流行, 热血 → bold pop…) into the shared master-styles tokens — feeds Mode A's prompt AND Mode B's text palette so both modes look like one family (`references/style-routing.md`).
5. Plan the SET, not 8 random loops: one identity block + fixed seed, a set-manifest, a moment→sticker map, and platform set-counts (see the batch/SET section of `references/frame-generation.md`).
6. Pick ONE dominant motion per sticker (+ ≤1 overlay) from the chat moment with `references/motion-library.md` — the moment picks the motion; the user never names a preset.
7. Produce frames per mode with `references/prompt-template.md`: Mode A via budget-gated model-sheet-first with native caption typography in the generated cells, then `scripts/sheet_to_sticker.py` to slice/assemble/verify; Mode B via either `scripts/kinetic_text.py` (caption-led) or `scripts/photo_puppet.py` (photo-led, face-preserving subject motion).
8. Emit the frame contract (`out/<name>/frames/f%04d.png` + `manifest.json`, documented in `references/render-pipeline.md`) — both modes emit the same shape. `sheet_to_sticker.py`, `kinetic_text.py`, and `photo_puppet.py` write exactly this for you.
9. Assemble deterministically with `scripts/assemble.py`: it loads frames in sorted order, loops the seam, and writes a small optimized GIF (see **Assembly** below).
10. Export per platform: keep transparency by default, or pass `--flatten RRGGBB` for platforms that drop alpha (WeChat / X), per `references/platform-specs.md`.
11. Verify the bytes — dims, size, fps, frames, loop — with `scripts/verify_output.py` and refuse non-compliant output (see **Verify** below).
12. Run QA with `references/qa-checklist.md`; route failures to accept / regenerate / repair.
13. For README/gallery/showcase stickers, ship at least one real animated GIF, not only a static frame sheet. Prefer original non-engineering characters (lanterns, pets, paper creatures, food spirits, clouds, plants) so the gallery shows charm beyond work/training scenarios.

## Face-Truth Gate

Run this FIRST, before any look or frame work, answered from intake. It is the signature gate — and the honesty backbone of the whole skill. It lives here, inline.

```text
sticker job:
- subject source:        theme-only | user-photo | user-avatar | pet-photo | brand-mascot
- any face-preservation intent expressed (now or earlier in the chat)?   yes / no   ← DECISIVE
- deliverable:           single sticker | SET (count)
- dominant chat moment(s): {笑死 / 赞同 / 摆烂 / 求饶 / 晚安 / 生气 / 震惊 / ...}
- motion preset:         routed from the chat moment (never user-named)
- frame count (A):       2-8 (boomerang doubles for free; never boomerang directional motion)
- loop:                  seamless? (cyclic | boomerang | directional)
- legible @240px:        yes / no
- target platform(s):    wechat | line | telegram | discord | twitter | generic
→ MODE: A (frame-gen)  |  B (photo + kinetic)
→ routing reason:
→ if motion adds nothing: ship a STATIC sticker (use sticker-set) instead
```

Routing logic (hard, priority order — earlier rules WIN and make later ones unreachable):

1. **Any face-preservation intent, now or earlier → MODE B, always.** If the user has at any point said "保留我的脸 / 用我本人 / 别改我长相 / 每张图不一样但脸一样" or uploaded a selfie as "我", rule 1 fires and rules 3–4 are unreachable regardless of any later edit-consent answer. No image model touches the pixels. Pick the B subpath from intent: if they want the photo itself to move, use **B-photo-puppet**; if they mainly want reply captions, use **B-kinetic-text**. This is the honesty backbone — a soft "随便改吧" never overrides an earlier face-preservation intent.
2. `subject = theme-only` → **MODE A** (you own the identity; cleanest loops).
3. `user-photo/avatar` AND **no** face-preservation intent → before routing to MODE A, print the verbatim honesty caveat (below), THEN ask the explicit-cost consent question (below). Only an informed `yes` routes to **MODE A (edit branch)**; cap ~2–3 variants. Any `no`, any hesitation, or silence → MODE B.
4. "a whole set / 16 / 24 / themed pack" → **MODE A** (only frame-gen batches a SET cheaply) — unless rule 1 already fired.
5. **Ambiguous real face → default MODE B** and ask one question: *"要保留你照片里真实的脸，还是可以做成 AI 风格化的你？"* Ambiguity dominates the A-edit branch: when in doubt, B.
6. Both face-true AND a fast set → **B-photo-puppet first** for a real-face moving set; only split to A when the user explicitly accepts an AI-stylized likeness. Never force one generation to do both.

The consent question for rule 3 must surface the cost in plain words BEFORE the user answers — never a soft "可以改吗？":

```text
要把你的照片做成会动的，AI 会重新合成你的五官（眼睛、颧骨、皮肤都是重画的）——
这不是你本人的脸，是一个「AI 版的你」。动作越大越不像你本人。接受吗？
  接受 → MODE A（edit branch，做 AI 风格化的你，封顶 2–3 个动作）
  不接受 / 想保留真脸 → MODE B（B-photo-puppet 让原照片动；或 B-kinetic-text 只动文字/特效）
```

Output one token (`MODE_A` / `MODE_B`) + sub-path (`A-theme` / `A-edit` / `B`). If motion adds nothing the joke doesn't already carry, ship a static sticker — a still that loops nothing is dead weight under a byte budget.

## Token Budget Gate

Run this immediately after the Face-Truth Gate. Output the chosen budget in the plan.

```text
token budget:
- route: low | medium | high
- image-gen calls allowed now:
- expected deliverable in this pass:
- stop point:
```

Hard routing:

1. **Default low budget.** If the user did not explicitly ask for AI-redrawn frames, use Mode B
   (`B-photo-puppet` for "person/image moves", `B-kinetic-text` for caption-led stickers). Target:
   zero image-gen calls; a quick 6-9 sticker pack should stay cheap because only shell scripts run.
2. **Medium budget A-smoke.** If the user asks for A-face-anchor / AI-redrawn action from a real
   photo, generate at most **2 sticker sheets** first (2 image-gen calls total), assemble them, and
   show an animated preview. Stop there unless the user explicitly asks to continue the expensive
   route.
3. **High budget A-pack.** Only when the user explicitly accepts a full AI-redraw pack budget, run
   A-face-anchor in batches of **max 4 image-gen calls per pass**. After each batch, make a contact
   sheet from saved files, select/assemble, and stop before the next batch.
4. **Never generate 8-10 large A sheets in one blind run.** That pattern can push a simple sticker
   job into millions of logged tokens in Codex because the generated PNG payloads are huge.
5. **Do not read or grep session JSONL to recover images.** Use the generated image `savedPath` (or
   list filenames in the generated_images directory) and move/copy files locally. Never print base64,
   never dump image-generation tool outputs, and keep shell outputs capped to filenames/metrics.

If the user complains about cost or asks for optimization, choose low budget and deliver a good
Mode B pack first. A-route quality is a paid upgrade, not the default.

## Economy, Sets & Shareability (three more gates)

- **Economy is a HARD constraint, not精致.** A sticker is meant to be cheap and tiny. Cap at
  ≤240px, 2–12 frames, few colors, small file. On Codex this also means **don't over-spec the
  image gen** — large/ultra-crisp frames burn tokens for no benefit; deliberately render small
  and a little rough. Generate the FEWEST frames that loop, at the SMALLEST size that reads.
  Reject any plan that asks for big, high-res, many-frame stickers.
- **A SET is the default deliverable.** Unless the user asks for one, plan a coherent SET (a
  WeChat pack is 16/24; a quick set is ~6–9) — one identity + one routed style, varied per
  sticker by chat moment. Single stickers are the exception.
- **颜值 + 传播度 test (the point of a sticker).** People make stickers to SPREAD them. Every
  sticker must pass: is it **cute OR funny** (颜值 or 梗), does it have a **hook** someone would
  forward, and does it map to a **real chat moment**? If a sticker is neither beautiful nor
  funny, cut it — pretty-but-mute and clear-but-boring both fail. Max both aesthetics AND
  virality; this is the core of the harness.
- **Real-face-required means no generative face resynthesis.** For "actual face, different motions",
  use **B-photo-puppet** first: the face remains the original photo transformed as pixels. If the user
  wants new expressions, turned head angles, mouth shapes, or true acting while staying identical,
  say plainly that this needs a face-aware video/animation model outside this skill. Mode A can make
  richer frames, but on a real photo it is an AI-stylized likeness, not the same face.

## Default Look

Read `references/motion-library.md` before generating. Core DNA:

- ONE dominant motion per sticker; everything else is sub-12% accent; ≤1 overlay.
- Loop-seamless: last frame blends into first (cyclic, or boomerang for there-and-back). `assemble.py` honors the `loop_strategy` in the manifest.
- Huge readable text: cap-height ≥ 38% of canvas, strong outline/contrast, flat fill, anti-aliased stroke. In Mode A, ask the image model to render the caption natively inside each generated cell. In Mode B/C, the scripts draw text deterministically because there is no image generation path.
- Motion lives in the first 70%; the last 30% settles to a held rest pose — the frame people screenshot (`--preset hold` is the explicit settle preset).
- ≤ 5 words of text; emotion carried by motion, not paragraphs.
- Square canvas, subject centered with safe margins, transparent or flat ground; loop length 0.6–1.8s; fps ∈ {25, 20, 10, 5, 4, 2} only (GIF delays are integer centiseconds — these are the values `kinetic_text.py --fps` accepts).
- Mode A: same identity block + same seed pack-wide; vary exactly ONE element per frame.
- Mode B: no generated face. In **B-kinetic-text**, the real photo is still and the look lives on the text system. In **B-photo-puppet**, the real photo is transformed as one pixel layer (scale/rotate/translate/bob/shake) so the subject appears to move while the face remains the same source pixels. Supply a bold CJK font with `--font /path/to/bold-CJK.ttf`; omit it and the scripts auto-detect a system CJK font (STHeiti / Hiragino / PingFang / Noto).
- No seizure-flashing (WCAG 2.3.1): ≤3 local glows/sec, never a global luminance slam; FLASH→POP, GLITCH→SHAKE on strict platforms (the `flash`/`shake` presets are the safe swap pair).
- Never fake a finished GIF: the encoder is Pillow-only, so it always runs — but if frames are missing or a manifest is malformed, STOP and say so rather than ship a broken file.

## Aesthetic Routing (automatic, by subject vibe — shared by both modes)

The look is **routed by subject vibe**, not hand-picked, into the shared master-styles token engine, so Mode A frames and Mode B text feel like one family (`references/style-routing.md`). 国潮/古风/古装/武侠/仙侠/神兽 → 水墨/工笔 ink (rice-paper ground, 朱砂红+石青 accent, tiny 印章 — culture wins over cuteness); 可爱/萌宠 → Zagnoli rounded pop; hype/热血/gaming → bold pop + speed-lines; 丧/摆烂/打工人 → desaturated muted; 高级/商务克制 → 减法扁平 (sub-12% motion). Route ONCE, then LOCK the register into the identity DNA. Clean subjects forbid clutter — never route them to a maximalist motion.

## Set Design

A pack is a SET, not eight random loops. Lock the coherence layer once, then derive every sticker from it — the batch/SET section of `references/frame-generation.md` covers this in full:

- **Identity block** (Mode A): 3–5 fixed traits — silhouette, palette (2–4 fixed roles), head shape, line weight, one signature accessory — declared ONCE and frozen pack-wide. Vary exactly one element per frame.
- **Fixed seed** (Mode A): one seed for the whole pack; same-seed derivation keeps frames on-model.
- **Set-manifest:** one row per sticker — `(label, chat_moment, the ONE varied element, motion_preset, loop_strategy)`.
- **Moment→sticker map:** each sticker maps to a concrete chat moment; cut any that maps to none.
- **Platform set-counts** are guardrails, not suggestions: WeChat 16 or 24 (all-animated OR all-static, never mixed); LINE 8 / 16 / 24. Refuse a non-allowed count.

## Frame Contract

Both modes emit the SAME shape into `out/<name>/`, and the assembler reads only this — it never knows whether an image model or Pillow drew the pixels. The full schema lives in `references/render-pipeline.md`; the shape is:

```text
out/<name>/
  frames/f0000.png, f0001.png, ...   # zero-padded, identical dims, subject registered ≤3px
  manifest.json:
    {
      "name":          "<name>",
      "mode":          "A" | "B",
      "fps":           25 | 20 | 10 | 5 | 4 | 2,
      "frame_count":   2-8 (effective; boomerang expands later),
      "loop_strategy": "cyclic" | "boomerang" | "directional",
      "canvas":        [w, h],          # square, ≥240 authoring
      "chat_moment":   "笑死",
      "caption":       "在吗…" | null,
      "platforms":     ["wechat", "line", ...]
    }
```

`scripts/sheet_to_sticker.py` writes `frames/f%04d.png` + `manifest.json` for Mode A sheets, then can assemble and verify in the same call. For Mode A, default to native caption text already rendered in the generated sheet; run the helper with no `--caption` or `--text-motion none` unless you are explicitly repairing failed native text or adding a platform-specific animated caption requested by the user. `scripts/kinetic_text.py` writes the same contract for B-kinetic-text; `scripts/photo_puppet.py` writes it for B-photo-puppet. Inline Pillow slicing is only a fallback if the helper script is unavailable.

## Assembly (deterministic, the agent runs the shipped script)

No image model in this step. The agent runs `scripts/assemble.py` — the pipeline is fixed, only the inputs change:

```bash
python3 scripts/assemble.py --in out/xiaosi --flatten FFFFFF --out out/xiaosi/wechat.gif
```

1. **Pillow-only, no ffmpeg required.** `assemble.py` builds the GIF with Pillow alone; if `gifsicle` happens to be on PATH it is used to shrink the file further, but it is never required. There is no tool-probing step and no `brew install` gate — the encoder always runs.
2. **Frame hygiene is built in.** `assemble.py` loads `frames/f%04d.png` in sorted order, so frame ordering and seam alignment are handled for you — you do not align frames by hand.
3. **Alpha vs flat.** Omit `--flatten` to keep transparency. Pass `--flatten RRGGBB` (e.g. `--flatten FFFFFF`) for platforms that drop alpha — WeChat and X — so the subject lands on a clean flat ground instead of a black halo.
4. **Optional fps override.** `assemble.py --fps N` re-times playback at encode if you want to diverge from the manifest's fps.

Timing is a hard constraint: only fps ∈ {25, 20, 10, 5, 4, 2} divide cleanly into integer centiseconds; author anything else and playback drifts. These are exactly the values `kinetic_text.py --fps` accepts.

## Platform Targets

The shipped pipeline ships GIF — one container, tuned per platform. The per-platform caps and the "safe target" live in `references/platform-specs.md`; the knobs you actually turn are `assemble.py --flatten` and `--fps`:

- **WeChat** — GIF, loses alpha; assemble with `--flatten FFFFFF` (flat white ground). Set-count 16 / 24, all-animated or all-static.
- **LINE** — GIF; keep alpha (omit `--flatten`); set-count 8 / 16 / 24.
- **Telegram / Discord** — GIF; the ≤256KB emoji budget usually needs fewer frames + flat/transparent bg + boomerang.
- **X (Twitter)** — drops alpha; assemble with `--flatten` and design for no-alpha.
- **generic** — GIF, transparency kept (omit `--flatten`).

If a file is over budget, climb the ladder by **re-running `assemble.py` at a lower `--fps` or a smaller `--size` (re-render frames with `kinetic_text.py --size`)** until it lands under the platform byte cap — always re-encode FROM FRAMES, never re-compress the finished GIF.

## Verify

After encode, the agent runs `scripts/verify_output.py` against the target platform and REFUSES non-compliant output — dims, byte size, fps, frame count, and loop flag must all pass:

```bash
python3 scripts/verify_output.py --file out/xiaosi/wechat.gif --platform wechat
```

It exits nonzero on any breach. A WeChat GIF at 401KB or 260×260 fails; no eyeballing, no shipping it anyway. If it fails on size, route to the byte-budget ladder (Repair: re-run `assemble.py` at lower `--fps` / smaller `--size`, not Regenerate); if it fails on frames or loop, fix the seam in the manifest and re-assemble.

## Tooling Note

This is a session-agnostic skill — Codex / Claude Code / Hermes, not Codex-only. Mode A needs **image-gen + code exec**; Mode B needs only **code exec** (no image model). The encoder is **Pillow-only** — there is no ffmpeg/gifski dependency to probe, and `gifsicle` is used only opportunistically if present to shrink further. An image-only chat agent can produce Mode A frames but cannot run `assemble.py` to encode the GIF or batch a set — it must hand the `frames/` + `manifest.json` off for assembly elsewhere, or decline. Never fake a finished animated file.

## Output Contract

For planning, return:

```text
mode: A (theme | edit) | B
token budget route: low | medium | high
image-gen calls allowed now:
stop point:
subject + real-face-preservation:
deliverable: single | SET (count)
chat moment(s):
look register (routed by vibe):
per sticker: chat moment | motion preset | overlay | frame count | loop strategy
identity block + seed (Mode A):
platform target(s) + caps:
honesty caveat (verbatim if Mode A edits a real photo):
QA risks:
```

For generation, produce one sticker at a time and report:

- output path (and per-platform exports)
- mode + sub-path
- token budget route + actual image-gen call count
- the exact text rendered
- native text status: Mode A should confirm whether generated cells already contain the caption; if script typography was used, state that it was an explicit repair/platform-fidelity route rather than silent default
- the chat moment + motion preset
- platform + dims + size + fps + frames + loop (post-verify)
- whether it passes QA or needs regeneration

## Honest Caveats

Surface these BEFORE the user uploads a selfie — see `references/prompt-template.md` and `scripts/README.md`:

- Mode A on a real photo is NOT face-preserving: generative editing re-synthesizes eyes, cheekbones, and skin; the output is a stylized likeness, not your face. The verbatim caveat + the explicit-cost consent question (Face-Truth Gate, rule 3) must come BEFORE the user agrees, never after routing. Cap ~2–3 variants. Hard face-preservation → Mode B. QA fails any Mode-A-edits-real-photo delivery that omits the verbatim caveat.
- True talking-head / lip-synced animation needs a video model. This skill makes a 2–8 frame loop, not smooth facial animation.
- One container ships here: GIF. Platforms that keep alpha (LINE, generic) get a transparent GIF; platforms that drop alpha (WeChat, X) get a flattened GIF via `--flatten`. There is no APNG/WEBM exporter in this skill — `references/platform-specs.md` flags where that distinction matters.

## End-to-End Example (tested)

The exact tested demo — Mode B, from a photo to a verified WeChat GIF:

```bash
python3 scripts/kinetic_text.py --base photo.png --text 笑死 --preset bounce --frames 12 --fps 10 --size 240 --out out/xiaosi
python3 scripts/assemble.py --in out/xiaosi --flatten FFFFFF --out out/xiaosi/wechat.gif
python3 scripts/verify_output.py --file out/xiaosi/wechat.gif --platform wechat
```

`sheet_to_sticker.py` accepts `--sheet SHEET`, `--grid 1x4|2x4`, `--caption TEXT`, `--text-motion {none|pop|bounce|shake|pulse}`, `--platform`, `--flatten auto|RRGGBB`, `--fps`, `--size`, `--loop`, and `--out`; it writes frames, manifest, GIF, and verify output with small logs. `kinetic_text.py` accepts `--base PHOTO` (a blank value gives a flat ground), `--text`, `--preset {pop|bounce|shake|flash|hold}`, `--frames N`, `--fps {25|20|10|5|4|2}`, `--size 240`, `--pos {top|bottom}`, `--loop {cyclic|boomerang|directional}`, `--cap-ratio F`, `--font PATH`, and `--out DIR`. `photo_puppet.py` accepts `--base PHOTO`, `--text`, `--action {nod|shake|bob|pop|stamp|slide|sleep|question}`, `--overlay {none|question|sparkle|zzz|speed|sweat}`, the same `--frames/--fps/--size/--pos/--loop/--font/--out` controls, and keeps the face as original photo pixels.

## References

- `references/frame-generation.md`: Mode A — generate a short sequence of consistent frames (model-sheet-first, fixed seed, vary one element), from a theme or by editing a reference photo; also the batch/SET section for packs and the consistency rules that keep frames on-model.
- `references/render-pipeline.md`: the shared deterministic assembly core — the `frames/f%04d.png` + `manifest.json` frame contract, Mode B compositing, and frames → small seamless-looping GIF; the working implementation lives in `scripts/` (Pillow-only, tested).
- `references/style-routing.md`: auto-route the look by subject vibe (国潮/古风 → 水墨, 萌宠 → 圆润流行…) into the master-styles tokens; applies to both modes.
- `references/motion-library.md`: the motion banks + moment→preset map, FLASH/GLITCH safe-swaps, the global motion rules, and the per-mode defaults — read before generating.
- `references/platform-specs.md`: per-platform export caps (WeChat / LINE / Telegram / Discord / X) + the "safe target", with uncertainties flagged.
- `references/text-and-layout.md`: huge stroked legible captions, safe areas, the `--font` / auto-detect CJK font rule, and why programmatic text (Mode B compositing) is always crisp.
- `references/prompt-template.md`: the two-mode templates — Mode A (planning / model-sheet / edit-from-photo / batch-a-SET) and Mode B (build spec + deterministic render), with the verbatim honesty caveat.
- `references/qa-checklist.md`: the three verdicts — accept / regenerate / repair — plus the falsifiable loop, thumbnail, and spec tests and the per-platform byte gate.

Working scripts (Pillow-only, no ffmpeg required; tested — see `examples/`):

- `scripts/kinetic_text.py`: Mode B-kinetic-text — composite a stroked caption over the real photo (or a flat ground) and animate it into `frames/f%04d.png` + `manifest.json`. Presets `{pop|bounce|shake|flash|hold}`, fps `{25|20|10|5|4|2}`, `--font PATH` or system CJK auto-detect.
- `scripts/photo_puppet.py`: Mode B-photo-puppet — make the original photo itself move via deterministic pixel transforms, with optional crisp caption and small overlays. Use for "same face, moving image" requests.
- `scripts/sheet_to_sticker.py`: Mode A sheet handoff — slice a generated 1x4/2x4 sheet, preserve native caption text by default, optionally add/repair a caption only when explicitly needed, write the frame contract, assemble, and verify in one low-output command.
- `scripts/assemble.py`: frames + manifest → optimized looping GIF (Pillow; uses `gifsicle` if present, loads frames in sorted order). `--flatten RRGGBB` for WeChat/X, transparent otherwise; `--fps N` to re-time.
- `scripts/verify_output.py`: refuse non-compliant output against a platform's caps — `--platform {wechat|line|telegram|discord|twitter|generic}` asserts dims / size / frames / loop and exits nonzero on breach.
- `scripts/cutie.py`: Mode C — a polished pure-Pillow cute 团子 (squash-&-stretch, supersampled, blush + per-emotion face + meme overlays). `--emotion {agree|laugh|flat|emo|cheer|love|sleep|shy} --name X --word Y` → `frames/` + `manifest.json`. The free, on-brand floor; sample set in `examples/cutie/`.
- `scripts/stickman.py`: Mode C — a minimal 火柴人 + name/word variant (`--action {wave|clap|cheer|jump}`). Even cheaper than cutie.
- `scripts/README.md`: the exact tested end-to-end demo command + sample outputs.
