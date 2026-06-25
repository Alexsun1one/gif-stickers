#!/usr/bin/env python3
"""stickman.py — code-rendered character frames (Mode C: no image model, near-zero cost).

Draws a parametric stick figure performing an action, with a name/word caption, across N
frames — then hand to assemble.py for the GIF. Pure Pillow: no image model, tiny files,
deliberately low-res. This is the cheapest sticker path and works in ANY agent with a shell.

Example:
  python3 stickman.py --action wave --name 正在逐渐AI化 --word 你好 --frames 12 --size 240 --out out/wave
  python3 assemble.py --in out/wave --flatten FFFFFF --out out/wave/s.gif
"""
import argparse, json, math, os
from PIL import Image, ImageDraw, ImageFont

FONTS = ["/System/Library/Fonts/STHeiti Medium.ttc", "/System/Library/Fonts/Hiragino Sans GB.ttc",
         "/System/Library/Fonts/PingFang.ttc", "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc"]
PALETTES = {  # one accent per sticker keeps it cheap + on-brand
    "wave": ((255, 240, 232), (40, 40, 40), (240, 90, 90)),
    "clap": ((232, 245, 255), (40, 40, 40), (60, 150, 230)),
    "cheer": ((255, 250, 225), (40, 40, 40), (245, 170, 40)),
    "jump": ((235, 250, 235), (40, 40, 40), (70, 190, 110)),
}


def font(px):
    for p in FONTS:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, px)
            except Exception: pass
    return ImageFont.load_default()


def limb(d, x0, y0, ang_deg, length, w, fill):
    a = math.radians(ang_deg)
    x1, y1 = x0 + length * math.sin(a), y0 - length * math.cos(a)
    d.line([(x0, y0), (x1, y1)], fill=fill, width=w)
    return x1, y1


def pose(action, t):
    """t in 0..1 over the loop. Returns joint angles (deg) + body bob (px frac)."""
    s = math.sin(t * 2 * math.pi)
    if action == "wave":   # right arm up, hand waving
        return dict(armL=200, armR=35 + 18 * s, legL=200, legR=160, bob=0)
    if action == "clap":   # arms swing together/apart in front
        sp = 30 + 35 * abs(s)
        return dict(armL=180 + sp, armR=180 - sp, legL=200, legR=160, bob=0)
    if action == "cheer":  # both arms up, little hop
        return dict(armL=215 - 8 * s, armR=145 + 8 * s, legL=205, legR=155, bob=-0.03 * (0.5 + 0.5 * s))
    if action == "jump":   # legs tuck, whole body bobs
        up = max(0, s)
        return dict(armL=215, armR=145, legL=200 - 25 * up, legR=160 + 25 * up, bob=-0.10 * up)
    return dict(armL=200, armR=160, legL=200, legR=160, bob=0)


def draw(action, name, word, size, i, n, pal):
    S = size; bg, ink, accent = pal
    im = Image.new("RGBA", (S, S), bg + (255,))
    d = ImageDraw.Draw(im)
    t = i / max(n, 1)
    p = pose(action, t)
    bob = p["bob"] * S
    cx = S / 2
    head_r = S * 0.085
    head_cy = S * 0.27 + bob
    shoulder = (cx, S * 0.36 + bob)
    hip = (cx, S * 0.55 + bob)
    w = max(3, round(S * 0.022))
    # body
    d.line([shoulder, hip], fill=ink, width=w)
    # head
    d.ellipse([cx - head_r, head_cy - head_r, cx + head_r, head_cy + head_r], outline=ink, width=w, fill=bg + (255,))
    # arms (accent) + legs (ink)
    limb(d, shoulder[0], shoulder[1], p["armL"], S * 0.17, w, accent)
    limb(d, shoulder[0], shoulder[1], p["armR"], S * 0.17, w, accent)
    limb(d, hip[0], hip[1], p["legL"], S * 0.18, w, ink)
    limb(d, hip[0], hip[1], p["legR"], S * 0.18, w, ink)
    # name (small, top) + word (big, bottom), stroked for legibility
    nf = font(round(S * 0.085)); wf = font(round(S * 0.20))
    st = max(2, round(S * 0.02))
    d.text((cx, S * 0.07), name, font=nf, anchor="mm", fill=ink, stroke_width=st, stroke_fill=bg + (255,))
    d.text((cx, S * 0.86), word, font=wf, anchor="mm", fill=accent, stroke_width=st + 2, stroke_fill=(255, 255, 255, 255))
    return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--action", default="wave", choices=["wave", "clap", "cheer", "jump"])
    ap.add_argument("--name", default="")
    ap.add_argument("--word", required=True)
    ap.add_argument("--frames", type=int, default=12)
    ap.add_argument("--fps", type=int, default=10)
    ap.add_argument("--size", type=int, default=200)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    pal = PALETTES.get(a.action, PALETTES["wave"])
    os.makedirs(os.path.join(a.out, "frames"), exist_ok=True)
    for i in range(a.frames):
        draw(a.action, a.name, a.word, a.size, i, a.frames, pal).save(
            os.path.join(a.out, "frames", "f%04d.png" % i))
    json.dump({"mode": "C", "action": a.action, "fps": a.fps, "size": a.size,
               "frames": a.frames, "loop_kind": "cyclic", "text": a.word},
              open(os.path.join(a.out, "manifest.json"), "w"), ensure_ascii=False, indent=2)
    print("stickman: %d frames -> %s (%s, '%s')" % (a.frames, a.out, a.action, a.word))


if __name__ == "__main__":
    main()
