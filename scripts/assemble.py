#!/usr/bin/env python3
"""assemble.py — deterministic frames -> looping GIF assembler.

Consumes the frame contract (a dir with frames/f%04d.png + manifest.json) produced by
EITHER mode (Mode A generated frames, or Mode B kinetic_text.py) and encodes a small,
seamlessly-looping GIF. Pillow-only by default (zero external deps, max portability); if
`gifsicle` is on PATH it is used to optimize the file further.

The assembler never knows how the frames were made — one interface, both modes.

Example:
  python3 assemble.py --in out/xiaosi --platform wechat --out out/xiaosi/wechat.gif
"""
import argparse, glob, json, os, shutil, subprocess, sys
from PIL import Image

# centiseconds per frame must be an integer (GIF limitation); pick fps that divides 100.
SAFE_FPS = {25, 20, 10, 5, 4, 2}


def load_frames(indir):
    files = sorted(glob.glob(os.path.join(indir, "frames", "f*.png")))
    if not files:
        raise SystemExit("no frames in %s/frames" % indir)
    return [Image.open(f).convert("RGBA") for f in files]


def seamless(frames, loop_kind):
    if loop_kind == "boomerang":
        # there-and-back: avoids a hard cut for directional motion
        return frames + frames[-2:0:-1]
    return frames  # cyclic: caller designed last->first to blend


def to_gif(frames, fps, out, flatten_bg):
    if fps not in SAFE_FPS:
        fps = min(SAFE_FPS, key=lambda x: abs(x - fps))
    duration = round(1000 / fps)  # ms; integer centiseconds when fps divides 100
    # quantize each frame to a shared adaptive palette; keep 1 index for transparency
    if flatten_bg:
        bg = Image.new("RGBA", frames[0].size, flatten_bg + (255,))
        flat = [Image.alpha_composite(bg, f).convert("RGB") for f in frames]
        pal = flat[0].quantize(colors=256, method=Image.MEDIANCUT)
        seq = [im.quantize(palette=pal, dither=Image.FLOYDSTEINBERG) for im in flat]
        seq[0].save(out, save_all=True, append_images=seq[1:], loop=0,
                    duration=duration, optimize=True, disposal=1)
    else:
        # transparent GIF: reserve palette index 0 for alpha
        seq = []
        for f in frames:
            p = f.convert("RGBA")
            alpha = p.split()[3]
            q = p.convert("RGB").quantize(colors=255, method=Image.MEDIANCUT)
            q.paste(255, mask=alpha.point(lambda a: 255 if a < 128 else 0))
            q.info["transparency"] = 255
            seq.append(q)
        seq[0].save(out, save_all=True, append_images=seq[1:], loop=0,
                    duration=duration, transparency=255, disposal=2, optimize=True)
    return duration


def optimize(path):
    if shutil.which("gifsicle"):
        subprocess.run(["gifsicle", "-O3", "--batch", path], check=False)
        return "gifsicle -O3"
    return "pillow optimize (gifsicle not found)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="indir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--fps", type=int, default=0, help="0 = read from manifest")
    ap.add_argument("--flatten", default="", help="hex like FFFFFF to flatten alpha (WeChat/X); blank = keep transparency")
    args = ap.parse_args()

    man = {}
    mp = os.path.join(args.indir, "manifest.json")
    if os.path.exists(mp):
        man = json.load(open(mp, encoding="utf-8"))
    fps = args.fps or man.get("fps", 12)
    loop_kind = man.get("loop_kind") or man.get("loop_strategy", "cyclic")
    frames = seamless(load_frames(args.indir), loop_kind)
    flat = tuple(int(args.flatten[i:i+2], 16) for i in (0, 2, 4)) if args.flatten else None
    dur = to_gif(frames, fps, args.out, flat)
    opt = optimize(args.out)
    im = Image.open(args.out)
    n = getattr(im, "n_frames", 1)
    kb = os.path.getsize(args.out) / 1024
    print("GIF: %s  %dx%d  %d frames  %dms/frame  %.1fKB  [%s]" %
          (args.out, im.size[0], im.size[1], n, dur, kb, opt))


if __name__ == "__main__":
    main()
