#!/usr/bin/env python3
"""kinetic_text.py — Mode B frame generator.

Composite a big, stroked caption over a base image (the user's real photo, untouched)
and animate the TEXT across N frames. No image model; text is drawn programmatically so
it is always crisp. Outputs zero-padded RGBA PNG frames + manifest.json (the frame
contract that assemble.py consumes).

Pillow-only; no ffmpeg needed at this step.

Example:
  python3 kinetic_text.py --base photo.png --text 笑死 --preset bounce \
      --frames 12 --fps 12 --size 240 --out out/xiaosi
"""
import argparse, json, math, os, sys
from PIL import Image, ImageDraw, ImageFont

# CJK-capable fonts to try, in order. Override with --font.
FONT_CANDIDATES = [
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Bold.otf",
]


def load_font(path, px):
    paths = [path] if path else FONT_CANDIDATES
    for p in paths:
        if p and os.path.exists(p):
            try:
                return ImageFont.truetype(p, px)
            except Exception:
                continue
    raise SystemExit("No usable CJK font found. Pass --font /path/to/font.ttf")


def ease_out_back(t):
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def text_xform(preset, i, n, size):
    """Return (dx, dy, scale, alpha) for frame i. Motion lives in the first 70%,
    then settles to a held rest pose (the frame people screenshot)."""
    settle = 0.7
    t = min(i / max(n - 1, 1) / settle, 1.0)  # 0..1 then clamps (rest)
    if preset == "pop":
        return 0, 0, max(0.05, ease_out_back(t)), 1.0
    if preset == "bounce":
        dy = -abs(math.sin(t * math.pi)) * size * 0.12 * (1 - t * 0.4)
        return 0, dy, 1.0, 1.0
    if preset == "shake":
        amp = size * 0.04 * (1 - t)
        return math.sin(i * 1.9) * amp, 0, 1.0, 1.0
    if preset == "flash":
        return 0, 0, 1.0, 0.35 + 0.65 * (0.5 + 0.5 * math.sin(i * 1.3))
    if preset == "hold":
        # Keep "hold" visibly calm, but not byte-identical across frames.
        # Otherwise GIF optimizers collapse the loop to a single static frame.
        pulse = 0.93 + 0.07 * (0.5 + 0.5 * math.sin(i * math.pi / 2))
        return 0, 0, 1.0, pulse
    return 0, 0, 1.0, 1.0


def render(args):
    S = args.size
    os.makedirs(os.path.join(args.out, "frames"), exist_ok=True)
    # base: the real photo, untouched, fitted to SxS (cover-crop, never distort)
    if args.base and os.path.exists(args.base):
        base = Image.open(args.base).convert("RGBA")
        bw, bh = base.size
        scale = max(S / bw, S / bh)
        base = base.resize((round(bw * scale), round(bh * scale)), Image.LANCZOS)
        x = (base.width - S) // 2; y = (base.height - S) // 2
        base = base.crop((x, y, x + S, y + S))
    else:
        base = Image.new("RGBA", (S, S), (245, 240, 232, 255))  # flat ground fallback

    font_px = round(S * args.cap_ratio)
    font = load_font(args.font, font_px)
    stroke = max(2, round(S * 0.035))
    ty = round(S * (0.16 if args.pos == "top" else 0.84))

    paths = []
    for i in range(args.frames):
        dx, dy, sc, alpha = text_xform(args.preset, i, args.frames, S)
        frame = base.copy()
        # render the (possibly scaled) caption on its own layer, then paste
        layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        fpx = max(8, round(font_px * sc))
        f = load_font(args.font, fpx) if sc != 1.0 else font
        d.text((S / 2 + dx, ty + dy), args.text, font=f, anchor="mm",
               fill=(255, 255, 255, round(255 * alpha)),
               stroke_width=stroke, stroke_fill=(20, 20, 20, round(255 * alpha)))
        frame.alpha_composite(layer)
        p = os.path.join(args.out, "frames", "f%04d.png" % i)
        frame.save(p)
        paths.append(p)

    manifest = {
        "mode": "B", "preset": args.preset, "fps": args.fps, "size": S,
        "frames": args.frames, "loop_kind": args.loop, "text": args.text,
        "frame_glob": "frames/f%04d.png",
    }
    json.dump(manifest, open(os.path.join(args.out, "manifest.json"), "w"),
              ensure_ascii=False, indent=2)
    print("wrote %d frames + manifest.json to %s" % (len(paths), args.out))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="", help="base photo (Mode B); blank = flat ground")
    ap.add_argument("--text", required=True)
    ap.add_argument("--preset", default="bounce", choices=["pop", "bounce", "shake", "flash", "hold"])
    ap.add_argument("--frames", type=int, default=12)
    ap.add_argument("--fps", type=int, default=10, choices=[25, 20, 10, 5, 4, 2])
    ap.add_argument("--size", type=int, default=240)
    ap.add_argument("--pos", default="bottom", choices=["top", "bottom"])
    ap.add_argument("--loop", default="cyclic", choices=["cyclic", "boomerang", "directional"],
                    help="loop kind passed to assemble.py (boomerang doubles frames there-and-back)")
    ap.add_argument("--cap-ratio", type=float, default=0.30, help="cap-height as fraction of canvas")
    ap.add_argument("--font", default="")
    ap.add_argument("--out", required=True)
    render(ap.parse_args())
