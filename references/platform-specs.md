# Platform Specs

The exact export matrix for animated stickers, shared by BOTH modes. Mode A (frame-gen) and
Mode B (photo + kinetic text, via `scripts/kinetic_text.py`) converge on the same frame contract —
`frames/f%04d.png` + `manifest.json`, documented in `render-pipeline.md` — then `assemble.py` cuts a
small looping GIF, and `verify_output.py --platform X` asserts it against the per-platform numbers
below. The agent WRITES and RUNS that assembly code; no image model touches the encode. This file is
the source of truth for canvas, byte budget, loop, and alpha per platform. `verify_output.py` exits
nonzero on any byte that breaks a HARD number here, and only WARNS on the soft/unverified ones
(flagged below).

The real toolchain is **Pillow-only** — no ffmpeg required. `assemble.py` builds the GIF from the
frame sequence; if `gifsicle` happens to be on PATH it gets used to shrink the file further, but it is
never assumed. There is no probe step to claim — if a tool isn't there, the pipeline still produces a
GIF. Don't promise a binary you can't guarantee is installed.

Numbers are from official platform docs where available; community-derived and aggregator figures
are flagged. **Honesty rule: when a number is soft, say so in the delivery — never present a
community convention as an official mandate, and never let a soft number hard-reject valid output.**

## Master art (author once, down-convert per platform)

- Square, **transparent** background, action centered with safe margins, reads at small size.
- Author at **≥512×512** RGBA PNG sequence, **≤3s**, **≤20 frames**, target **~12–15 fps** for raster art.
  (Mode B caps the kinetic-text canvas at `--size 240` for WeChat-native output; up-scale the master
  separately for larger targets — `assemble.py` never up-scales for you.)
- Per platform, re-run `assemble.py` at the right `--fps`/canvas; for WeChat/X, add `--flatten RRGGBB`
  to drop alpha onto a clean ground (LINE/Telegram/Discord keep transparency where the container allows).

## Export matrix

| Platform | Container | Canvas (px) | Duration / FPS / frames | Size cap | Loop | Alpha |
| --- | --- | --- | --- | --- | --- | --- |
| **WeChat 微信** | **GIF** only | **240×240** | frame-driven; ~0.1s/frame; no published frame cap | **≤400KB** real/screenshot · ≤500KB cartoon | infinite (required) | flat 1-bit → ship +2px white-stroke variant; set 16/24, all-animated-or-all-static |
| **LINE** | **APNG** (.png ext) | **≤320×270**, one side ≥270, even dims, RGB | **5–20 frames**; 1/2/3/4s; loops×len ≤4s | **≤1MB/img** (ZIP ≤60MB) | 1–4 loops | transparent REQUIRED; first frame = preview; set 8/16/24 |
| **Telegram** | **WEBM / VP9**, no audio | one side **512**, other ≤512 | **≤3s**, **≤30fps** | **≤256KB** | must loop | VP9 alpha (yuva420p — build-dependent, see note) |
| **Discord sticker** | **APNG** | **320×320** | short loop, no published cap | ~512KB *(soft — warn)* | loops | transparent preferred |
| **Discord emoji** | **GIF** | **128×128** | short | ~256KB *(soft — warn)* | loops | transparent OK |
| **Twitter / X** | **GIF** → MP4 server-side | ≤1280×1080 (reuse 512 master) | 2–6s, <350 frames, drop to 15fps to shrink | aim **<5MB** (mobile <3MB; 15MB hard) | **loop=0** required or it shows static | none — flattened, alpha always lost |

HARD numbers (`verify_output.py` exits nonzero on breach): WeChat 240×240 / 400KB-real / GIF / loop;
LINE ≤320×270 / 5–20 frames / ≤1MB; Telegram 512-long-side / ≤3s / ≤30fps / **≤256KB** / loop; X
loop=0 / 15MB. SOFT numbers (warn only, see "Flagged uncertainties"): every Discord figure.

## What the GIF pipeline actually ships (and what it doesn't)

The tested scripts build **GIFs**. That is the one container the toolchain encodes end to end, and
`assemble.py` is the only thing that touches the bytes:

```bash
# Mode B: bake the kinetic-text frames (blank --base = flat ground; or pass a real photo)
python3 scripts/kinetic_text.py --base photo.png --text 笑死 --preset bounce --frames 12 --fps 10 --size 240 --out out/xiaosi
# Assemble the looping GIF; --flatten for platforms that drop alpha (WeChat/X)
python3 scripts/assemble.py --in out/xiaosi --flatten FFFFFF --out out/xiaosi/wechat.gif
# Verify against the platform's HARD numbers; nonzero exit = breach
python3 scripts/verify_output.py --file out/xiaosi/wechat.gif --platform wechat
```

`verify_output.py --platform {wechat|line|telegram|discord|twitter|generic}` asserts dims, byte size,
frame count, and loop for the named target. To trim under a byte cap, re-run `assemble.py` at a lower
`--fps` (the manifest carries 25/20/10/5/4/2) or a smaller `--size`, then re-verify — there is no
separate budget tool, just iterate the assemble until it's under the cap.

The **APNG (LINE, Discord sticker) and WEBM/VP9 (Telegram)** containers are *targets to verify
against*, not things these scripts encode. `verify_output.py` knows the `line`/`telegram`/`discord`
numbers and will check a file you hand it, but the Pillow pipeline emits GIF — for a true APNG or
alpha-VP9 deliverable, hand off the verified `frames/` for a manual encode and **say so in the
delivery**. Never present a GIF as an APNG, and never claim an alpha-video encode the toolchain didn't
actually run.

## Per-platform notes

- **WeChat 微信** — GIF only; rejects APNG/WEBM/Lottie on the open platform (`sticker.weixin.qq.com`). 240×240 main image — exactly what Mode B's `--size 240` produces. Album is **16 or 24** stickers, no other counts; a set is **all animated OR all static** — never mixed. Permanent loop required. Run `assemble.py --flatten FFFFFF` (or whatever ground you want) — GIF alpha is 1-bit and fringes on chat backgrounds. The **2px white stroke** is a strong community convention to kill that fringing; bake it into the frames before assembly — convention, NOT an official rule. Review ≈2 weeks.
- **LINE** — APNG, `.png` extension, **RGB**, **transparent required**. 5–20 frames; an all-identical-frame file gets collapsed and fails upload. Playback **1/2/3/4s only** (no 1.5s); loops×length ≤4s. First frame is the STORE preview — make it a readable held pose (the `hold` preset is built for this). The tested pipeline emits a GIF you can verify with `--platform line` for dims/frames/size/loop; the APNG itself is a manual-encode handoff from the `frames/` — flag that in the delivery.
- **Telegram** — **WEBM/VP9, 512 long side, ≤3s, ≤30fps, ≤256KB, no audio, must loop**, alpha via VP9 `yuva420p`. `verify_output.py --platform telegram` checks the dims/duration/fps/size/loop numbers on a file you give it, but the Pillow toolchain does NOT encode VP9 — there is no ffmpeg dependency here. For a true alpha-video sticker, hand off the verified `frames/` for a manual VP9 encode and prove the alpha plane survived on that side; **most encoders silently drop alpha** to opaque, so an unverified VP9 is unverified. If you can't guarantee an alpha-capable encode, ship a flat-ground GIF instead and SAY the alpha was flattened — never present an opaque box as a transparent sticker. (The `.TGS`/Lottie vector path is **out of scope** — Lottie can't embed raster, and both modes are raster. See below.)
- **Discord** — sticker 320×320 (renders at 2×), uploaded as APNG; emoji 128×128, GIF, animated emoji require Nitro / a boosted server. The byte caps (~512KB sticker, ~256KB emoji) are **cross-source consistent but unconfirmed** (official article was 403 at research time) — `verify_output.py` WARNS, does not exit nonzero, on the Discord numbers. No published frame/duration cap — budget-driven; re-run `assemble.py` at a lower `--fps`/`--size` to fit. The emoji GIF is a direct pipeline output; the sticker APNG is a `frames/` handoff.
- **Twitter / X** — no sticker product; a GIF is transcoded to a looping MP4, so **alpha is always lost**. Run `assemble.py --flatten RRGGBB` onto a deliberate ground, then `verify_output.py --platform twitter` (loop=0 / 15MB hard). 2–6s loops upload far more reliably than 10–15s; dropping to `--fps 15` (re-assemble) cuts size hard with minor loss.

## Default deliverable (no platform named)

A bare transparent GIF is a trap as a default: GIF alpha is **1-bit**, so it fringes on any colored
chat background — the exact halo the WeChat white-stroke variant exists to kill. So the default does
not ship one. When no platform is named, emit:

```text
default deliverable (no platform named):
- (a) WeChat 240×240 GIF, +2px white-stroke variant  → assemble.py --flatten FFFFFF; fringe-proof on any chat bg
- (b) flat-background GIF at the master size          → assemble.py --flatten RRGGBB onto a clean ground;
                                                          universal, lowest-common-denominator (NOT a 1-bit
                                                          transparent GIF that fringes)
- (c) the verified frames/ sequence                   → handoff for any APNG / alpha-VP9 encode a named
                                                          platform later needs (LINE / Discord sticker / Telegram)
```

**Default-routing rule:** ship (a) + (b) by default — a fringe-proof flat for WeChat-style chats and a
flat-bg GIF as the universal fallback — plus (c), the `frames/` sequence, so any transparency-honoring
container can be encoded on demand. Produce the **APNG or WEBM/VP9** deliverable only when that platform
is named (it needs a manual encode + alpha proof outside this Pillow toolchain). Never emit a bare
1-bit transparent GIF as "the default" — it reproduces the very fringe this skill warns about.

## The 3-container reality

There is **no single file** that satisfies every platform's container. The tested toolchain encodes
**GIF** (the one it owns end to end); **APNG** (LINE, Discord sticker) and **WEBM/VP9** (Telegram) are
separate containers that need a manual encode from the `frames/` the pipeline produces. Don't promise
"one sticker, every app," and don't claim an APNG/VP9 the scripts didn't actually emit.

- Transparent required/preferred → LINE (APNG, hard), Telegram (VP9 + alpha-proof), Discord (soft) — all `frames/` handoffs for the container.
- Effectively flat / alpha lost → WeChat (1-bit fringing → flatten + white stroke), X (MP4 transcode) — both direct `assemble.py --flatten` outputs.

## TGS / Lottie — out of scope

Telegram's `.TGS` is gzipped Lottie vector (512×512, ≤3s, 60fps, **≤64KB**) and **cannot embed
raster art**. Both modes here are raster, so TGS is excluded by design — route Telegram to WEBM/VP9
(a `frames/` handoff, not a pipeline output).

## Flagged uncertainties (verify before ship)

- **WeChat**: authoritative spec PDFs didn't render at research time; per-frame timing and any hard frame cap are soft/community-derived. **400KB vs 500KB depends on type** (真人/截屏 = 400KB; 卡通 = 500KB). The 2px white stroke is convention, not mandate.
- **Telegram**: the WEBM/VP9 + ≤256KB + 512 + ≤3s spec is official (`core.telegram.org/stickers`), but **VP9-with-alpha is build-dependent** — most encoders silently drop the alpha plane to opaque. The Pillow toolchain doesn't encode VP9 at all; treat any VP9 deliverable as a manual-encode handoff and prove `yuva420p` survived before calling it transparent.
- **Discord**: the official support article returned HTTP 403 at research time; ~512KB / ~256KB / 320×320 / 128×128 are cross-source consistent but **not directly confirmed**, so they are **soft (warn-only) gates** in `verify_output.py`, not nonzero-exit refusals — re-verify against current docs before treating them as hard. Nitro/boost gating changes over time — re-verify.
- **Twitter / X**: no clean official consumer GIF spec; numbers from media best-practices + aggregators. Alpha is always lost.

## Sources

- LINE Animated Sticker Guidelines — `creator.line.me/en/guideline/animationsticker/`
- Telegram Stickers + WEBM/VP9 encoding — `core.telegram.org/stickers`
- WeChat 表情开放平台 — `sticker.weixin.qq.com`; 制作规范 — `mzwu.com`
- Discord Sticker Creators FAQ (403 this session); Moxion Discord GIF size guide
- X Media Best Practices — `developer.x.com`; curl-x Twitter GIF size limit
