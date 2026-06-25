# Frame Generation (MODE A)

MODE A makes a short loop by **generating 2–8 consistent still frames** of one subject with an
image model, then handing them to the deterministic assembler. The frame-gen step needs an image
model; the assembly step does not (see `render-pipeline.md`). The hard problem here is NOT the
encoding — it is keeping the **same subject across frames** while changing **exactly one thing**.
Consistency is never assumed; it is *measured* before the frames ship (the drift gate, below).

Two sub-paths, decided by the Face-Truth Gate before any look work (see `SKILL.md (Face-Truth Gate)`):

- **A-theme** — invent the subject. You own the identity; cleanest loops, easiest to batch.
- **A-face-anchor / A-edit** — start from a user photo / avatar. Use the face as an identity
  anchor, then allow the scene, body pose, props, expression, and sticker composition to be
  re-rendered across several frames. This is the right route when the user says "可以重绘场景/动作,
  但脸要尽量像同一个人". It is **not pixel-face-preserving**: the model re-synthesizes facial
  details, so the output is a *best-effort AI likeness with face consistency*, not the exact photo.
  Say this before generation. If the face must stay exact pixels, use MODE B-photo-puppet.

MODE A cannot do true talking-head or smooth facial animation — that needs a video model. This
makes a 2–8 frame loop, nothing more.

This is tool-neutral: the frame model can be any image-gen the host (Codex / Claude Code / Hermes)
can call; the assembler is plain code. Neither step is locked to a vendor.

## Token Discipline for MODE A

MODE A is visually stronger but can be token-expensive in Codex. Treat generated image payloads as
heavy artifacts, not chat text.

- **Default A-face-anchor pass = A-smoke, not full pack.** Generate at most 2 sticker sheets, assemble
  those, and stop with a preview. Continue only after explicit user approval.
- **Full A-pack = batch of 4 image-gen calls max.** After each batch, copy saved PNGs to the project,
  create a contact sheet, assemble the winners, and stop before generating more.
- **One generated sheet should earn multiple frames.** Prefer a 1x4/2x4 sheet that can be sliced.
  Never generate separate full-resolution images for individual frames unless the tool cannot make
  sheets.
- **Never dump generated-image payloads.** Do not paste or print base64. Do not grep session logs for
  result blobs. Use `savedPath` and local file operations.
- **Keep shell output tiny.** Print filenames, dimensions, byte sizes, and verification summaries;
  do not print manifests, large JSON, or image data.
- **If the first A-smoke fails face consistency, do not keep spending blindly.** Either switch to
  B-photo-puppet, narrow the prompt, or ask for a higher budget before more image-gen calls.

Recommended cost ladder:

```text
low:    B-photo-puppet quick set, 0 image-gen calls
medium: A-face-anchor smoke, <=2 image-gen calls, 1-2 stickers assembled
high:   A-face-anchor pack, <=4 image-gen calls per batch, review between batches
```

## Identity-Lock Ladder (pick the highest rung the tool supports)

Strongest → weakest control. Stronger rungs lock identity by construction, so flicker and drift
*start* lower — but no rung is drift-free, so every rung still passes through the drift gate.

- **A1 — model-sheet crop (DEFAULT).** Generate ONE image that is a `1×N` / `2×N` grid of the
  same subject in N poses, then crop the cells into frames. All cells share one generation, so
  style / lighting / palette are locked from a single draw — this **lowers** cross-frame drift, it
  does not zero it: cells in one grid still vary in subject **scale, position, and crop framing**,
  which reads as flicker until registered. So A1 frames are NOT shippable raw — they MUST clear the
  drift gate (below). Prompt pattern: *"character model sheet, same character, 1×4 grid,
  white background, identical style and lighting, frame 1 neutral, frame 2 blinking, frame 3
  smiling, frame 4 waving."* Slice and assemble the sheet with `scripts/sheet_to_sticker.py`; use
  inline Pillow only as a fallback if the helper is unavailable.
- **A2 — reference-edit from ONE base.** Feed the same base image + a per-frame instruction
  ("now raise the right hand"). Modern editors hold a subject across edits, but each edit re-noises
  position and background. **Always branch from the base, never chain edit→edit→edit** (drift trap,
  below). Drift-gate every output before stacking.
- **A2F — face-anchor multi-frame edit.** Feed the same face/source photo as identity reference,
  then generate several full-frame sticker poses from a shared prompt: same face identity,
  redesigned body/scene/action per frame. This rung is for "face roughly same, action/scene can be
  redrawn." Generate **1-2 candidate sheets for smoke**, or **max 4 candidate sheets per high-budget
  batch**, slice them, then choose the sheet whose face remains most consistent. Never claim exact
  face preservation; this is a likeness QA problem, not a pixel truth problem.
- **A3 — fixed-seed img2img (self-hosted SD / Flux).** Lock the seed, change one phrase. Numbers:
  denoise **0.35–0.5**, CFG **4–6**, IP-Adapter FaceID **0.65–0.8**, ControlNet OpenPose to drive
  the pose. These are starting values, not guarantees — the drift gate is what proves they held.
  Keep a fixed identity block; swap only the action line.
- **A4 — same-seed-only (fallback).** Lock the seed, change one word. Identity wobbles once the
  pose moves; the drift gate will fail it past 2 frames. Warn the user before authoring >2 frames.

### Slicing a model sheet (A1) — use the helper first

Use `scripts/sheet_to_sticker.py` for normal Mode A handoff. It slices a `1×N` / `2×N` sheet,
center-crops cells to square frames, optionally bakes animated Chinese caption text, writes the
manifest, assembles the GIF, and verifies the platform cap:

```bash
python3 scripts/sheet_to_sticker.py --sheet sheet.png --grid 1x4 \
  --caption 离谱 --text-motion pop --platform wechat --loop cyclic \
  --out out/lipu
```

For a `2×N` grid, the helper uses row-major order; pass `--cells 0,1,2,3` to choose a subset or
reorder frames. It writes both `loop_kind` and `loop_strategy` in the manifest for compatibility.
Inline Pillow slicing is now only the emergency fallback.

## Harness Invariants (QA-verifiable)

1. **Vary exactly ONE element per frame** — eyes, OR hand height, OR vertical bounce — never
   several at once. One variable is what makes 4 frames read as deliberate animation, not jitter.
2. **Hold background, body, framing, and lighting identical.** Generate on flat white / a flat
   color / transparent so the cut-out stays clean; busy backgrounds re-noise every frame and
   flicker hardest.
3. **Branch, never chain.** Every frame comes off the same base image / seed. Chained edits let
   facial embeddings wander until frame 8 no longer matches frame 1.
4. **Register, then PROVE it, before stacking.** Keep every frame centered and comparable; use
   `sheet_to_sticker.py` for normal sheet slicing and run the drift gate when identity/framing drift
   is in doubt. **Fail the set if it is still out of spec** — eyeballing is the last resort, not the
   first. A 3px subject jump reads as flicker, so 3px is the line.
5. **Same identity block + same seed pack-wide** — locks style frame-to-frame *and* sticker-to-
   sticker across the whole set.

## The Drift Gate (measured, not eyeballed)

A1's single-grid draw lowers drift; it does not remove it. "Near-zero drift" is a lie by omission —
so MODE A *measures*. There is no drift-measurement script; the gate is a short inline Pillow/numpy
pass you run on every set after slicing (A1) or after each branch render (A2–A4). It emits the same
three numbers the QA `>3px` and `flicker` rules assert against — write them to
`out/<name>/drift.json` so QA reads a verdict, not your gut:

```python
# inline drift gate — runs over out/<name>/frames/, writes out/<name>/drift.json
# 1. SEGMENT subject vs background per frame (alpha if RGBA, else luma threshold on the flat bg).
# 2. REGISTER: re-center every frame's subject centroid bbox to the median bbox with a Pillow
#    crop/paste — translate only (no warp, no scale of the real subject).
# 3. MEASURE drift against the reference (frame 0 for cyclic, the median for boomerang):
#      subject_shift_px = max per-frame centroid displacement AFTER registration
#      bg_delta         = mean abs background-region delta (0..1) between consecutive frames
#      id_drift         = 1 - mean SSIM over the subject bbox between consecutive frames
# 4. VERDICT in drift.json — PASS only if ALL hold:
#      subject_shift_px <= 3          (else: registration failure → flicker)
#      bg_delta         <= 0.04       (else: background re-noising → flicker)
#      id_drift         <= 0.12       (else: off-model drift → Regenerate, not Repair)
```

```json
{
  "mode": "A",
  "rung": "A1",
  "frames": 4,
  "subject_shift_px": 1.6,
  "bg_delta": 0.018,
  "id_drift": 0.07,
  "verdict": "PASS",
  "fail_reason": null
}
```

Routing the verdict (QA reads `drift.json`, does not re-judge by eye):

- **subject_shift / bg_delta over budget** → a *registration / encode-input* failure. Re-run the
  inline re-center pass; only if it still fails are the frames themselves bad.
- **id_drift over budget** → an *off-model* failure registration cannot fix. **Regenerate** the
  offending frame FROM the model sheet / base — never chain-edit it (Invariant 3).
- A4 past 2 frames almost always trips `id_drift`; that is the gate telling you the rung is too
  weak for this motion. Drop frames or escalate the rung — do not ship and hope.

The thresholds (`3px`, `0.04`, `0.12`) are the contract: tune them in the manifest if a register is
genuinely looser (撞色纯色 tolerates more bg_delta than a photo edit), but the verdict is always a
number QA can re-derive, never a feeling.

## A-theme vs A-edit (honesty)

```text
A-theme: invented subject → define a one-line identity block once, reuse VERBATIM every frame,
         vary only the action. Cleanest path; the default. Still goes through the drift gate.
A-edit:  user photo/avatar → NOT face-preserving. Generative editing re-synthesizes eye shape,
         cheekbones, skin; the more the pose/expression changes, the more it drifts — and id_drift
         in the gate is exactly that drift, made measurable. Cap ~2-3 variants off one selfie;
         beyond that it reads as "AI version of you" and the gate will say so.
A-face-anchor: user photo/avatar → best-effort same-person likeness. The face identity is the
         anchor, while scene/body/action/background may be redrawn per frame. Use this when the
         user explicitly accepts AI redraw for motion and composition but wants the frames to feel
         like the same person. Generate a model sheet or several branch edits, then select by
         face-consistency QA; if exact face is required, route back to B-photo-puppet.
```

Print the verbatim caveat before any A-edit run (the QA fails an A-edit delivery that omits it):
*"这是把你照片作为身份参考重新生成一组动图帧：脸会尽量保持像同一个人，但五官细节、皮肤和表情会被 AI 重绘；场景、身体动作和构图也可能重绘。要逐像素保留真实的脸，请改用 MODE B-photo-puppet。"*

## A-Face-Anchor Production Pattern

This is the hybrid the original A-edit wording used to miss:

```text
Input: one real portrait / avatar.
Goal: 2-8 frames where the face reads as the same person, while action, body, props,
      background, and sticker composition can change.

1. Extract an identity block from the photo:
   face shape, hairline/hair style, glasses, age range, skin tone, expression baseline,
   outfit/accessory if important.
2. Choose one sticker action loop:
   nod / shock / bow / wave / fall-flat / point / stamp / sleep.
3. Generate a model sheet or branch edits from the SAME reference:
   one sheet = same subject, same face identity, N poses, same lighting/register.
4. Generate 1-2 candidate sheets for the first smoke pass; only generate up to 4 in a high-budget
   batch after the user accepts the cost.
5. Slice every sheet into frames and run drift/registration checks.
6. Human/agent face-consistency QA:
   reject any sheet where one frame looks like a different person, even if the loop is pretty.
7. Ask the image model to render the sticker caption natively in every cell by default. Use
   `sheet_to_sticker.py` to slice/assemble/verify while preserving that native text. Composite
   programmatic text only as a repair or when the user explicitly requests animated overlay text.
8. Assemble and verify with the standard GIF pipeline; `sheet_to_sticker.py` does both by default.
9. Artifact handling: copy the final selected sheet(s) from `savedPath` into the project, make a
   small contact sheet if needed, and keep all future references as paths. Do not inspect or print
   raw image-generation JSON/base64 from the session log.
```

Prompt shape:

```text
Use the attached portrait as the identity reference. Create a 1x4 animated sticker model sheet.
Keep the same person's face identity across all four cells: same face shape, glasses, haircut,
hairline, skin tone, and overall likeness. Redraw the body pose, hands, props, and simple scene as
needed for the action. Same lighting, same sticker style, same background, same crop.

Action loop: {neutral -> surprised -> more surprised -> settle}
Render this exact Chinese caption natively in each cell: "{caption, ≤ 6 字}". Keep it large,
high-contrast, correct, and off the face. No extra text.
Important: consistent face identity across cells; no frame should look like a different person.
```

## Frame Count & Loop Design (2–8 is a feature)

Stickers loop forever and play tiny. **Target 2–8 frames.**

- **2 frames** — on/off: 眨眼 / 张嘴。Reads as a blink or talk.
- **3–4 frames** — a gesture: 挥手 / 点头 / 比心。Maps perfectly to a `1×4` model sheet.
- **6–8 frames** — a small cycle: bounce / breathing / hair sway.

**Ping-pong (boomerang) doubles frames for free** — play forward then reverse; the loop is
automatically seamless because the end equals the start. Use it for there-and-back motion
(blink / bob / nod). **NEVER ping-pong directional motion** — a one-way 挥手 that rewinds looks
broken; author a true cyclic loop instead. Record the choice as `loop_strategy`
(`directional | cyclic | boomerang`) in `manifest.json` (the frames + manifest contract is
documented in `render-pipeline.md`). Loop length 0.6–1.8s; keep motion in the first 70%, hold a
readable rest pose in the last 30% (the frame people screenshot). Pick the motion preset from the
chat moment with `motion-library.md` (Bank B is MODE A's home turf).

## Batch a Themed SET

A pack is many small loops — script it, do not hand-make each one. Declare the identity block
ONCE, reuse it pack-wide, drive a manifest, and run the drift gate on each loop. For image-gen
MODE A, batch conservatively; for low-cost packs, prefer Mode B or Mode C:

```text
IDENTITY = "chubby orange tabby, big eyes, tiny red scarf, flat style, white bg"
SEED     = 4242                                  # same seed across the whole pack
stickers = {                                     # name → ONE varied element per frame
  "wave":   ["arm down", "arm mid", "arm up", "arm mid"],   # directional → cyclic, no pingpong
  "blink":  ["eyes open", "eyes closed"],                   # there-and-back → pingpong
  "bounce": ["low", "mid", "high", "mid"],
}
# per loop: sheet_to_sticker.py → drift gate if needed → verified GIF
```

The model-sheet route can put several frames on one grid image and crop everything in one pass —
but each loop still clears its own drift gate before assembly. Mind the set-count guardrails when
batching (WeChat 16/24 all-animated-or-all-static; LINE 8/16/24 — see `platform-specs.md`) — a pack
is a SET, not 8 random loops. Do not generate a full A-face-anchor pack until an A-smoke proves the
style and face consistency are worth the spend.

## Hand-Off

Every A run emits the shared frame contract documented in `render-pipeline.md` —
`out/<name>/frames/f%04d.png` (RGBA, square, subject-centered, safe margins) + `drift.json`
(PASS required) + `manifest.json` with `mode: "A"`, `loop_strategy`, and native caption status.
Then encode and verify:

```bash
python3 scripts/assemble.py --in out/<name> --out out/<name>/wechat.gif --flatten FFFFFF
python3 scripts/verify_output.py --file out/<name>/wechat.gif --platform wechat
```

Use `--flatten RRGGBB` for platforms that drop alpha (WeChat / X); omit it to keep transparency
(Telegram / Discord). If a loop is over the platform byte cap, re-run `assemble.py` at a lower
`--fps` or a smaller `--size` until it clears `verify_output.py`. The scripts are Pillow-only — no
ffmpeg required; if `gifsicle` happens to be on PATH, `assemble.py` uses it to shrink further. The
assembler never knows how the frames were made; MODE A and MODE B converge on the exact same
pipeline.

If the agent can generate frames but cannot run a shell, it can produce the PNG sequence but
**cannot register, gate, encode, or batch** — it cannot prove the loop is on-model. Hand the
frames off for manual assembly (note the gate was not run) rather than faking a finished loop
(see the capability note in `SKILL.md`).
