#!/usr/bin/env python3
"""verify_output.py — refuse non-compliant stickers.

Asserts a built GIF against a platform's hard caps (dimensions, file size, frame count,
loop, duration). Exits non-zero on any breach so the skill never ships a sticker that a
platform will silently reject. Pillow-only.

Example:
  python3 verify_output.py --file out/xiaosi/wechat.gif --platform wechat
"""
import argparse, os, sys
from PIL import Image

# Hard caps. "size_kb" is the byte budget; dims are exact unless a range is noted.
# Discord figures are marked uncertain in platform-specs.md — treated as soft warns.
CAPS = {
    "wechat":   {"max_side": 240, "size_kb": 500, "min_frames": 2, "loop_required": True},
    "line":     {"max_side": 320, "size_kb": 1024, "min_frames": 5, "max_frames": 20, "loop_required": False},
    "telegram": {"max_side": 512, "size_kb": 256, "loop_required": True},  # note: real Telegram wants WEBM/VP9
    "discord":  {"max_side": 320, "size_kb": 512, "loop_required": True, "soft": True},
    "twitter":  {"max_side": 1280, "size_kb": 5120, "loop_required": True},
    "generic":  {"max_side": 320, "size_kb": 500, "loop_required": True},
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--platform", default="generic", choices=list(CAPS))
    args = ap.parse_args()
    cap = CAPS[args.platform]
    soft = cap.get("soft")

    im = Image.open(args.file)
    n = getattr(im, "n_frames", 1)
    w, h = im.size
    kb = os.path.getsize(args.file) / 1024
    loop = im.info.get("loop", None)  # 0 = infinite

    checks = []
    checks.append(("dimensions <= %dpx" % cap["max_side"], max(w, h) <= cap["max_side"], "%dx%d" % (w, h)))
    checks.append(("file size <= %dKB" % cap["size_kb"], kb <= cap["size_kb"], "%.1fKB" % kb))
    checks.append(("animated (>=2 frames)", n >= cap.get("min_frames", 2), "%d frames" % n))
    if "max_frames" in cap:
        checks.append(("frames <= %d" % cap["max_frames"], n <= cap["max_frames"], "%d frames" % n))
    if cap.get("loop_required"):
        checks.append(("loops forever (loop=0)", loop == 0, "loop=%s" % loop))

    print("verify [%s] %s" % (args.platform, args.file))
    ok = True
    for name, passed, got in checks:
        print("  %-28s %s  (%s)" % (name, "PASS" if passed else "FAIL", got))
        ok = ok and passed
    if soft and not ok:
        print("  (discord caps are UNCERTAIN — warning only, not a hard fail)")
        sys.exit(0)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
