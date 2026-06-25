#!/usr/bin/env python3
"""photo_puppet.py — face-preserving Mode B photo motion.

Turns one real photo into a short looping GIF frame sequence by moving the
original pixels deterministically: scale, rotate, translate, and overlay simple
effects/text. No image model touches the face, so this is the route for
"make the photo move, but keep the same face".

Outputs the same frame contract as the other producers:
  out/name/frames/f0000.png ...
  out/name/manifest.json
"""
import argparse, json, math, os
from PIL import Image, ImageDraw, ImageFont

SAFE_FPS = [25, 20, 10, 5, 4, 2]
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


def cover_crop(photo, size, scale=1.0):
    target = round(size * scale)
    bw, bh = photo.size
    s = max(target / bw, target / bh)
    im = photo.resize((round(bw * s), round(bh * s)), Image.LANCZOS)
    x = (im.width - target) // 2
    y = (im.height - target) // 2
    return im.crop((x, y, x + target, y + target))


def ease_out_back(t):
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def photo_motion(action, i, n, size):
    phase = (i / max(n, 1)) * math.tau
    t = i / max(n - 1, 1)
    if action == "nod":
        return 1.11, 0, math.sin(phase * 2) * size * 0.018, math.sin(phase * 2) * 2.2
    if action == "shake":
        settle = max(0, 1 - t * 0.9)
        return 1.12, math.sin(i * 2.6) * size * 0.035 * settle, 0, math.sin(i * 2.6) * 1.8 * settle
    if action == "bob":
        return 1.10, 0, math.sin(phase) * size * 0.025, math.sin(phase) * 0.8
    if action == "pop":
        settle = min(t / 0.72, 1)
        return 1.04 + 0.08 * ease_out_back(settle), 0, 0, 0
    if action == "stamp":
        hit = math.exp(-((t - 0.22) ** 2) / 0.012)
        return 1.08 + hit * 0.055, 0, hit * size * 0.018, -hit * 1.2
    if action == "slide":
        return 1.12, math.sin(phase) * size * 0.045, 0, math.sin(phase) * 1.2
    if action == "sleep":
        return 1.09, 0, math.sin(phase) * size * 0.014, -2.0
    if action == "question":
        return 1.11, math.sin(phase * 2) * size * 0.012, -math.sin(phase) * size * 0.012, math.sin(phase * 2) * 1.2
    return 1.10, 0, 0, 0


def paste_photo(canvas, photo, scale, dx, dy, angle):
    S = canvas.size[0]
    im = cover_crop(photo, S, scale)
    if angle:
        im = im.rotate(angle, resample=Image.BICUBIC, expand=False)
    x = round((S - im.width) / 2 + dx)
    y = round((S - im.height) / 2 + dy)
    canvas.paste(im, (x, y))


def draw_text(frame, text, font, font_px, pos, cap_ratio):
    if not text:
        return
    S = frame.size[0]
    stroke = max(2, round(S * 0.04))
    ty = round(S * (0.16 if pos == "top" else 0.84))
    d = ImageDraw.Draw(frame)
    d.text(
        (S / 2, ty),
        text,
        font=font,
        anchor="mm",
        fill=(255, 255, 255, 255),
        stroke_width=stroke,
        stroke_fill=(18, 18, 18, 255),
    )


def draw_overlay(frame, overlay, i, n):
    if overlay == "none":
        return
    S = frame.size[0]
    d = ImageDraw.Draw(frame, "RGBA")
    phase = (i / max(n, 1)) * math.tau
    if overlay == "question":
        font = load_font("", round(S * 0.22))
        wobble = math.sin(phase * 2) * 7
        d.text((S * 0.76, S * 0.18 + wobble), "?", font=font, anchor="mm",
               fill=(255, 255, 255, 235), stroke_width=round(S * 0.03),
               stroke_fill=(18, 18, 18, 255))
    elif overlay == "sparkle":
        for k, (x, y) in enumerate([(0.78, 0.23), (0.68, 0.34), (0.86, 0.38)]):
            r = round(S * (0.018 + 0.02 * (0.5 + 0.5 * math.sin(phase + k))))
            cx, cy = round(S * x), round(S * y)
            d.line((cx - r, cy, cx + r, cy), fill=(255, 230, 90, 230), width=3)
            d.line((cx, cy - r, cx, cy + r), fill=(255, 230, 90, 230), width=3)
    elif overlay == "zzz":
        font = load_font("", round(S * 0.13))
        for k in range(3):
            y = S * (0.22 - 0.05 * k) - (i % n) * 1.5
            x = S * (0.74 + 0.045 * k)
            d.text((x, y), "Z", font=font, anchor="mm", fill=(255, 255, 255, 210),
                   stroke_width=round(S * 0.018), stroke_fill=(18, 18, 18, 230))
    elif overlay == "speed":
        for k in range(5):
            y = S * (0.28 + k * 0.08)
            x0 = S * (0.72 + 0.03 * math.sin(phase + k))
            d.line((x0, y, S * 0.96, y - S * 0.03), fill=(255, 255, 255, 130), width=3)
    elif overlay == "sweat":
        x = S * 0.76
        y = S * (0.26 + 0.03 * math.sin(phase))
        d.ellipse((x - 8, y - 12, x + 8, y + 12), fill=(90, 190, 255, 210), outline=(18, 18, 18, 210), width=2)


def render(args):
    S = args.size
    os.makedirs(os.path.join(args.out, "frames"), exist_ok=True)
    photo = Image.open(args.base).convert("RGB")
    font_px = round(S * args.cap_ratio)
    font = load_font(args.font, font_px)
    for i in range(args.frames):
        frame = Image.new("RGB", (S, S), (255, 255, 255))
        scale, dx, dy, angle = photo_motion(args.action, i, args.frames, S)
        paste_photo(frame, photo, scale, dx, dy, angle)
        draw_overlay(frame, args.overlay, i, args.frames)
        draw_text(frame, args.text, font, font_px, args.pos, args.cap_ratio)
        frame.save(os.path.join(args.out, "frames", "f%04d.png" % i))
    manifest = {
        "mode": "B",
        "submode": "photo-puppet",
        "action": args.action,
        "overlay": args.overlay,
        "fps": args.fps,
        "size": S,
        "frames": args.frames,
        "loop_kind": args.loop,
        "text": args.text,
        "face_truth": "original photo pixels transformed only; no generative face resynthesis",
        "frame_glob": "frames/f%04d.png",
    }
    json.dump(manifest, open(os.path.join(args.out, "manifest.json"), "w"),
              ensure_ascii=False, indent=2)
    print("wrote %d photo-puppet frames + manifest.json to %s" % (args.frames, args.out))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--text", default="")
    ap.add_argument("--action", default="bob",
                    choices=["nod", "shake", "bob", "pop", "stamp", "slide", "sleep", "question"])
    ap.add_argument("--overlay", default="none",
                    choices=["none", "question", "sparkle", "zzz", "speed", "sweat"])
    ap.add_argument("--frames", type=int, default=12)
    ap.add_argument("--fps", type=int, default=10, choices=SAFE_FPS)
    ap.add_argument("--size", type=int, default=240)
    ap.add_argument("--pos", default="bottom", choices=["top", "bottom"])
    ap.add_argument("--loop", default="cyclic", choices=["cyclic", "boomerang", "directional"])
    ap.add_argument("--cap-ratio", type=float, default=0.34)
    ap.add_argument("--font", default="")
    ap.add_argument("--out", required=True)
    render(ap.parse_args())
