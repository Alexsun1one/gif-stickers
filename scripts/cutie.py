#!/usr/bin/env python3
"""cutie.py — code-rendered CUTE blob mascot frames (Mode C, polished, no image model).

Upgrade from stickman: a round squishy 团子 with big eyes, blush, per-emotion faces, and
squash-&-stretch bounce. Polish comes from SUPERSAMPLING (render at 3x, downscale with
LANCZOS = clean anti-aliased edges) + a soft drop shadow. Meme-y overlays (tears, sparkles,
hearts, sweat) per emotion. Pure Pillow. Hand frames to assemble.py for the GIF.

Example:
  python3 cutie.py --emotion laugh --name 正在逐渐AI化 --frames 14 --size 240 --out out/laugh
  python3 assemble.py --in out/laugh --flatten FFF7E0 --out out/laugh/s.gif
"""
import argparse, json, math, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONTS = ["/System/Library/Fonts/PingFang.ttc", "/System/Library/Fonts/STHeiti Medium.ttc",
         "/System/Library/Fonts/Hiragino Sans GB.ttc", "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc"]

# emotion -> (bg, body, accent, eyes, mouth, overlay, motion, default word)
EMO = {
    "agree": ("#FFF3E0", "#FFE6BE", "#FF8FA3", "happy",  "smile", "sparkle", "bounce", "对对对"),
    "laugh": ("#FFF7E0", "#FFEFB0", "#FF7A59", "squint", "open",  "tears",   "shake",  "笑死"),
    "flat":  ("#EEF3F6", "#D8E3EA", "#8AA0AE", "dead",   "flat",  "none",    "melt",   "摆烂"),
    "emo":   ("#E9EDF8", "#CCD8F2", "#6E84C7", "teary",  "frown", "raincloud","slow",  "emo了"),
    "cheer": ("#FFF1DD", "#FFE0AE", "#FF8C42", "happy",  "smile", "sparkle", "bounce", "冲鸭"),
    "love":  ("#FFEAF0", "#FFD6E0", "#FF5C8A", "happy",  "cat",   "hearts",  "bounce", "么么哒"),
    "sleep": ("#EFEAF8", "#DCD2F0", "#8E7CC3", "closed", "smile", "zzz",     "slow",   "晚安"),
    "shy":   ("#FFF0EC", "#FFE0D6", "#F08A6E", "happy",  "cat",   "sweat",   "bounce", "嘿嘿"),
}


def font(px):
    for p in FONTS:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, px)
            except Exception:
                try: return ImageFont.truetype(p, px, index=0)
                except Exception: pass
    return ImageFont.load_default()


def hx(s):
    s = s.lstrip("#"); return tuple(int(s[i:i+2], 16) for i in (0, 2, 4))


def lighten(c, f=0.25):
    return tuple(min(255, round(v + (255 - v) * f)) for v in c)


def draw_eye(d, x, y, r, style, ink):
    if style == "happy":   # round eye with highlight
        d.ellipse([x-r, y-r, x+r, y+r], fill=ink)
        hl = r*0.4; d.ellipse([x-hl*0.3, y-r*0.7, x-hl*0.3+hl, y-r*0.7+hl], fill=(255,255,255))
    elif style == "squint":  # ^ ^ happy squint
        d.arc([x-r, y-r*0.6, x+r, y+r*1.2], 200, 340, fill=ink, width=max(2, round(r*0.45)))
    elif style == "dead":    # flat dead eyes (横线)
        d.line([(x-r, y), (x+r, y)], fill=ink, width=max(2, round(r*0.45)))
    elif style == "teary":   # round + glassy bottom highlight
        d.ellipse([x-r, y-r, x+r, y+r], fill=ink)
        d.ellipse([x-r*0.6, y, x+r*0.6, y+r*0.9], fill=(180, 210, 255))
    elif style == "closed":  # u u sleeping (downward arc)
        d.arc([x-r, y-r*1.2, x+r, y+r*0.6], 20, 160, fill=ink, width=max(2, round(r*0.45)))


def draw_mouth(d, cx, cy, w, style, ink, accent):
    if style == "smile":
        d.arc([cx-w*0.5, cy-w*0.4, cx+w*0.5, cy+w*0.7], 15, 165, fill=ink, width=max(2, round(w*0.16)))
    elif style == "open":  # big laughing open mouth
        d.pieslice([cx-w*0.5, cy-w*0.2, cx+w*0.5, cy+w*0.9], 10, 170, fill=hx("#7a3b3b"))
        d.chord([cx-w*0.5, cy+w*0.15, cx+w*0.5, cy+w*0.9], 0, 180, fill=hx("#ff8aa0"))  # tongue
    elif style == "flat":
        d.line([(cx-w*0.35, cy+w*0.2), (cx+w*0.35, cy+w*0.2)], fill=ink, width=max(2, round(w*0.14)))
    elif style == "frown":
        d.arc([cx-w*0.5, cy+w*0.2, cx+w*0.5, cy+w*1.1], 195, 345, fill=ink, width=max(2, round(w*0.16)))
    elif style == "cat":  # ω mouth
        r = w*0.22
        d.arc([cx-r*2, cy, cx, cy+r*1.4], 0, 180, fill=ink, width=max(2, round(w*0.13)))
        d.arc([cx, cy, cx+r*2, cy+r*1.4], 0, 180, fill=ink, width=max(2, round(w*0.13)))


def overlay(d, kind, S, cx, cy, bw, t, accent):
    a = accent
    if kind == "sparkle":
        for k, (ox, oy) in enumerate([(-0.42, -0.34), (0.40, -0.40), (0.46, 0.08)]):
            ph = (t + k*0.33) % 1.0; sc = 0.5 + 0.5*math.sin(ph*2*math.pi)
            r = bw*0.10*sc + bw*0.03; x, y = cx+ox*S, cy+oy*S
            for ang in (0, 90):
                dx, dy = math.cos(math.radians(ang))*r, math.sin(math.radians(ang))*r
                d.line([(x-dx, y-dy), (x+dx, y+dy)], fill=a, width=max(2, round(r*0.5)))
    elif kind == "tears":
        for side in (-1, 1):
            prog = t % 1.0
            x = cx + side*bw*0.30 + side*prog*bw*0.5; y = cy - bw*0.05 + prog*bw*0.7
            r = bw*0.07
            d.ellipse([x-r, y-r*1.3, x+r, y+r], fill=hx("#7fc4ff"))
    elif kind == "hearts":
        for k in range(3):
            ph = (t + k*0.33) % 1.0; x = cx + (k-1)*bw*0.36; y = cy - bw*0.55 - ph*bw*0.5
            r = bw*0.11*(1-ph*0.4)
            d.ellipse([x-r, y-r*0.7, x, y+r*0.3], fill=a); d.ellipse([x, y-r*0.7, x+r, y+r*0.3], fill=a)
            d.polygon([(x-r, y), (x+r, y), (x, y+r*1.2)], fill=a)
    elif kind == "sweat":
        x = cx + bw*0.46; y = cy - bw*0.42 + (t % 1.0)*bw*0.2; r = bw*0.08
        d.ellipse([x-r, y-r*1.3, x+r, y+r], fill=hx("#7fc4ff"))
    elif kind == "zzz":
        for k in range(3):
            ph = (t + k*0.3) % 1.0; x = cx + bw*0.4 + k*bw*0.16; y = cy - bw*0.5 - ph*bw*0.5
            zf = font(round(bw*(0.22 - k*0.04)))
            d.text((x, y), "Z", font=zf, fill=accent, anchor="mm")
    elif kind == "raincloud":
        x, y = cx, cy - bw*0.62
        for ox in (-0.18, 0, 0.18):
            d.ellipse([x+ox*bw-bw*0.18, y-bw*0.12, x+ox*bw+bw*0.18, y+bw*0.14], fill=hx("#9fb0cc"))
        for k in range(3):
            ph = (t + k*0.33) % 1.0; rx = x + (k-1)*bw*0.18
            d.line([(rx, y+bw*0.12+ph*bw*0.2), (rx, y+bw*0.22+ph*bw*0.2)], fill=hx("#7fa0d8"), width=max(2, round(bw*0.03)))


def motion(kind, t):
    """return (dx_frac, dy_frac, squash) ; squash>1 = wider/shorter."""
    s = math.sin(t*2*math.pi)
    if kind == "bounce":
        up = abs(math.sin(t*math.pi)); return 0, -0.10*up, 1 + 0.12*(1-up) - 0.06*up
    if kind == "shake":
        return 0.03*math.sin(t*2*math.pi*2), -0.02*abs(s), 1 + 0.04*s
    if kind == "melt":
        return 0, 0.04*abs(s), 1.22
    if kind == "slow":
        return 0, -0.02*(0.5+0.5*s), 1 + 0.02*s
    return 0, 0, 1


def render_frame(emo, name, word, S, i, n, SS=3):
    bg, body, accent, eye, mouth, ov, mot, _ = EMO[emo]
    bgc, bc, ac = hx(bg), hx(body), hx(accent)
    W = S*SS
    im = Image.new("RGBA", (W, W), bgc + (255,))
    t = i / n
    dx, dy, sq = motion(mot, t)
    cx = W/2 + dx*W
    bw = W*0.46*sq; bh = W*0.46/sq
    cy = W*0.46 + dy*W
    # soft shadow
    sh = Image.new("RGBA", (W, W), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    sd.ellipse([cx-bw*0.5, cy+bh*0.42, cx+bw*0.5, cy+bh*0.62], fill=(60, 60, 70, 70))
    sh = sh.filter(ImageFilter.GaussianBlur(W*0.012)); im.alpha_composite(sh)
    d = ImageDraw.Draw(im)
    ink = (60, 55, 60)
    # body + top highlight + little feet
    d.ellipse([cx-bw*0.5, cy-bh*0.5, cx+bw*0.5, cy+bh*0.5], fill=bc, outline=ink, width=max(2, round(W*0.006)))
    d.ellipse([cx-bw*0.34, cy-bh*0.44, cx+bw*0.10, cy-bh*0.10], fill=lighten(bc, 0.45))  # highlight
    for s_ in (-1, 1):
        d.ellipse([cx+s_*bw*0.22-bw*0.10, cy+bh*0.40, cx+s_*bw*0.22+bw*0.10, cy+bh*0.56], fill=bc, outline=ink, width=max(1, round(W*0.004)))
    # blush
    bl = Image.new("RGBA", (W, W), (0, 0, 0, 0)); bd = ImageDraw.Draw(bl)
    for s_ in (-1, 1):
        bd.ellipse([cx+s_*bw*0.30-bw*0.10, cy+bh*0.05, cx+s_*bw*0.30+bw*0.10, cy+bh*0.05+bh*0.10], fill=ac+(120,))
    im.alpha_composite(bl)
    # eyes + mouth
    er = bw*0.085
    draw_eye(d, cx-bw*0.20, cy-bh*0.06, er, eye, ink)
    draw_eye(d, cx+bw*0.20, cy-bh*0.06, er, eye, ink)
    draw_mouth(d, cx, cy+bh*0.16, bw*0.42, mouth, ink, ac)
    overlay(d, ov, W, cx, cy, bw, t, ac)
    # name (top) + word (bottom pill)
    nf = font(round(W*0.072)); wf = font(round(W*0.165))
    if name:
        d.text((W/2, W*0.06), name, font=nf, anchor="mm", fill=ink, stroke_width=max(2, round(W*0.012)), stroke_fill=(255, 255, 255))
    # word on a soft white pill
    bb = d.textbbox((0, 0), word, font=wf); tw, th = bb[2]-bb[0], bb[3]-bb[1]
    py = W*0.86; pad = W*0.04
    pill = Image.new("RGBA", (W, W), (0, 0, 0, 0)); pd = ImageDraw.Draw(pill)
    pd.rounded_rectangle([W/2-tw/2-pad, py-th/2-pad*0.7, W/2+tw/2+pad, py+th/2+pad*0.7], radius=W*0.06, fill=(255, 255, 255, 235))
    pill = pill.filter(ImageFilter.GaussianBlur(W*0.004))
    im.alpha_composite(pill)
    d.text((W/2, py), word, font=wf, anchor="mm", fill=ac, stroke_width=max(2, round(W*0.01)), stroke_fill=(255, 255, 255))
    return im.resize((S, S), Image.LANCZOS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emotion", default="agree", choices=list(EMO))
    ap.add_argument("--name", default="")
    ap.add_argument("--word", default="")
    ap.add_argument("--frames", type=int, default=14)
    ap.add_argument("--fps", type=int, default=10)
    ap.add_argument("--size", type=int, default=240)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    word = a.word or EMO[a.emotion][7]
    os.makedirs(os.path.join(a.out, "frames"), exist_ok=True)
    for i in range(a.frames):
        render_frame(a.emotion, a.name, word, a.size, i, a.frames).save(os.path.join(a.out, "frames", "f%04d.png" % i))
    json.dump({"mode": "C", "emotion": a.emotion, "fps": a.fps, "size": a.size,
               "frames": a.frames, "loop_kind": "cyclic", "text": word},
              open(os.path.join(a.out, "manifest.json"), "w"), ensure_ascii=False, indent=2)
    print("cutie: %d frames -> %s (%s, '%s')" % (a.frames, a.out, a.emotion, word))


if __name__ == "__main__":
    main()
