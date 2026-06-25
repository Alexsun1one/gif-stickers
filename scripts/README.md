# gif-stickers scripts

The deterministic render core. A GIF is bytes, not a prompt — so the agent writes/runs these.
**Pillow-only: no ffmpeg, gifsicle, or gifski required.** If `gifsicle` is on PATH, `assemble.py`
uses it to shrink the file further; otherwise it falls back to Pillow's own optimizer.

No image model runs here. Caption text is drawn programmatically, so it is always crisp; Mode A
sheets use `sheet_to_sticker.py` to add exact animated text after generation.

## Core scripts

| script | role |
| --- | --- |
| `sheet_to_sticker.py` | **Mode A** sheet handoff: slice a generated 1x4/2x4 sheet, bake animated caption text (`--text-motion pop|pulse|bounce|shake|none`), assemble, and verify. |
| `kinetic_text.py` | **Mode B** frame generator: composite a big stroked caption over the real photo (untouched) and animate it into RGBA frames + `manifest.json`. |
| `photo_puppet.py` | **Mode B** photo-motion generator: move the original photo pixels as one layer with optional caption/overlay. |
| `assemble.py` | frames + `manifest.json` → a small, seamlessly-looping GIF. `--flatten RRGGBB` for platforms that drop alpha (WeChat/X); transparent otherwise. |
| `verify_output.py` | refuse non-compliant output: asserts dimensions / file size / frame count / loop against a platform's caps, exits non-zero on breach. |

Mode A (generated frames) skips `kinetic_text.py` and runs `sheet_to_sticker.py` on the saved model
sheet. One interface, both modes.

## Tested end-to-end demo

```bash
# Mode B: animate the caption 笑死 over a photo, bounce, 12 frames @10fps, WeChat 240px
python3 kinetic_text.py --base photo.png --text 笑死 --preset bounce \
    --frames 12 --fps 10 --size 240 --out out/xiaosi
python3 assemble.py --in out/xiaosi --flatten FFFFFF --out out/xiaosi/wechat.gif
python3 verify_output.py --file out/xiaosi/wechat.gif --platform wechat
```

Verified result: `240x240 · 8 frames (held frames merged) · loop=0 · ~63KB · PASS wechat`.
Sample outputs are in `../examples/` (`demo-xiaosi-240.gif` flattened, `demo-zantong-transparent.gif`
transparent). A transparent variant:

```bash
python3 kinetic_text.py --base "" --text 赞同 --preset pop --frames 10 --fps 10 --size 240 --out out/zantong
python3 assemble.py --in out/zantong --out out/zantong/sticker.gif   # keeps transparency
```

Mode A sheet handoff:

```bash
python3 sheet_to_sticker.py --sheet sheet.png --grid 1x4 --caption 离谱 \
    --text-motion pop --platform wechat --loop cyclic --out out/lipu
```

## Notes / limits

- `--fps` is snapped to a GIF-safe value ({25,20,10,5,4,2}) so per-frame delays stay integer centiseconds.
- Transparent GIF is 1-bit alpha (hard edges); for soft alpha, export APNG/WEBM (see `../references/platform-specs.md`).
- These scripts are the portable reference path. For higher-quality palettes/encoding, swap in
  ffmpeg `palettegen/paletteuse` or `gifski` as described in `../references/render-pipeline.md`.
