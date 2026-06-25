#!/usr/bin/env python3
"""sheet_to_sticker.py - Mode A sheet -> frames -> GIF -> verify.

This is the low-output Mode A handoff path. Give it one generated model sheet
(usually 1x4 or 2x4), and it writes the shared frame contract, optionally bakes a
crisp caption, assembles the GIF, and verifies it against a platform cap.
"""
import argparse
import json
import math
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SAFE_FPS = [25, 20, 10, 5, 4, 2]
FONT_CANDIDATES = [
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Bold.otf",
]
PLATFORMS = ["wechat", "line", "telegram", "discord", "twitter", "generic"]


def parse_grid(value):
    raw = value.lower().replace("*", "x")
    parts = raw.split("x")
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("grid must look like 1x4 or 2x4")
    rows, cols = int(parts[0]), int(parts[1])
    if rows <= 0 or cols <= 0:
        raise argparse.ArgumentTypeError("grid rows/cols must be positive")
    return rows, cols


def parse_cells(value, total):
    if not value:
        return list(range(total))
    cells = []
    for part in value.split(","):
        idx = int(part.strip())
        if idx < 0 or idx >= total:
            raise SystemExit("cell index %d outside grid 0..%d" % (idx, total - 1))
        cells.append(idx)
    return cells


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


def square_fit(cell, size):
    cell = cell.convert("RGBA")
    side = min(cell.size)
    x = (cell.width - side) // 2
    y = (cell.height - side) // 2
    cell = cell.crop((x, y, x + side, y + side))
    if cell.size != (size, size):
        cell = cell.resize((size, size), Image.LANCZOS)
    return cell


def draw_caption(frame, text, font, pos, i, n, motion):
    if not text:
        return frame
    frame = frame.convert("RGBA")
    size = frame.size[0]
    layer = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    stroke = max(2, round(size * 0.04))
    y = round(size * (0.16 if pos == "top" else 0.84))
    draw.text(
        (size / 2, y),
        text,
        font=font,
        anchor="mm",
        fill=(255, 255, 255, 255),
        stroke_width=stroke,
        stroke_fill=(18, 18, 18, 255),
    )
    phase = i / max(n - 1, 1)
    active = min(phase / 0.72, 1.0)
    dx = dy = 0
    scale = 1.0
    if motion == "pop":
        scale = 0.84 + 0.16 * ease_out_back(active)
    elif motion == "bounce":
        dy = round(-size * 0.045 * (1 - active) * abs(math.sin(active * math.pi)))
        scale = 0.96 + 0.04 * ease_out_back(active)
    elif motion == "shake":
        dx = round(size * 0.028 * (1 - active) * math.sin(i * 2.9))
    elif motion == "pulse":
        scale = 1.0 + 0.045 * math.sin((i / max(n, 1)) * math.tau)
    if scale != 1.0:
        w = max(1, round(size * scale))
        h = max(1, round(size * scale))
        scaled = layer.resize((w, h), Image.LANCZOS)
        layer = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        layer.alpha_composite(scaled, ((size - w) // 2 + dx, (size - h) // 2 + dy))
    elif dx or dy:
        shifted = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        shifted.alpha_composite(layer, (dx, dy))
        layer = shifted
    frame.alpha_composite(layer)
    return frame


def write_frames(args):
    rows, cols = args.grid
    total = rows * cols
    cells = parse_cells(args.cells, total)
    out = Path(args.out)
    frames_dir = out / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    for old in frames_dir.glob("f*.png"):
        old.unlink()

    sheet = Image.open(args.sheet).convert("RGBA")
    cell_w = sheet.width // cols
    cell_h = sheet.height // rows
    font = load_font(args.font, round(args.size * args.cap_ratio)) if args.caption else None

    written = []
    for n, idx in enumerate(cells):
        row, col = divmod(idx, cols)
        box = (col * cell_w, row * cell_h, (col + 1) * cell_w, (row + 1) * cell_h)
        frame = square_fit(sheet.crop(box), args.size)
        if font:
            frame = draw_caption(frame, args.caption, font, args.pos, n, len(cells), args.text_motion)
        path = frames_dir / ("f%04d.png" % n)
        frame.save(path)
        written.append(path)

    manifest = {
        "name": args.name,
        "mode": "A",
        "submode": "sheet",
        "source_sheet": os.path.abspath(args.sheet),
        "grid": "%dx%d" % (rows, cols),
        "cells": cells,
        "fps": args.fps,
        "size": args.size,
        "frames": len(written),
        "loop_kind": args.loop,
        "loop_strategy": args.loop,
        "text": args.caption,
        "text_baked": bool(args.caption),
        "text_motion": args.text_motion if args.caption else "none",
        "chat_moment": args.chat_moment,
        "frame_glob": "frames/f%04d.png",
    }
    with open(out / "manifest.json", "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
    return written


def run_tool(cmd):
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.stdout.strip():
        print(proc.stdout.strip())
    if proc.returncode != 0:
        if proc.stderr.strip():
            print(proc.stderr.strip(), file=sys.stderr)
        raise SystemExit(proc.returncode)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", required=True)
    ap.add_argument("--grid", type=parse_grid, default=parse_grid("1x4"))
    ap.add_argument("--cells", default="", help="row-major cells, e.g. 0,1,2,3")
    ap.add_argument("--name", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--caption", default="")
    ap.add_argument("--text-motion", default="pop",
                    choices=["none", "pop", "bounce", "shake", "pulse"])
    ap.add_argument("--chat-moment", default="")
    ap.add_argument("--pos", default="bottom", choices=["top", "bottom"])
    ap.add_argument("--cap-ratio", type=float, default=0.34)
    ap.add_argument("--font", default="")
    ap.add_argument("--fps", type=int, default=10, choices=SAFE_FPS)
    ap.add_argument("--size", type=int, default=240)
    ap.add_argument("--loop", default="cyclic", choices=["cyclic", "boomerang", "directional"])
    ap.add_argument("--platform", default="generic", choices=PLATFORMS)
    ap.add_argument("--flatten", default="auto", help="auto, blank, or hex RRGGBB")
    ap.add_argument("--gif-name", default="")
    ap.add_argument("--no-assemble", action="store_true")
    ap.add_argument("--no-verify", action="store_true")
    args = ap.parse_args()

    if not args.name:
        args.name = Path(args.sheet).stem

    written = write_frames(args)
    print("frames: %d -> %s" % (len(written), os.path.join(args.out, "frames")))
    print("manifest: %s" % os.path.join(args.out, "manifest.json"))
    if args.no_assemble:
        return

    script_dir = Path(__file__).resolve().parent
    gif_name = args.gif_name or ("%s.gif" % args.platform)
    gif_path = os.path.join(args.out, gif_name)
    flatten = args.flatten
    if flatten == "auto":
        flatten = "FFFFFF" if args.platform in {"wechat", "twitter"} else ""

    assemble_cmd = [
        sys.executable,
        str(script_dir / "assemble.py"),
        "--in",
        args.out,
        "--out",
        gif_path,
        "--fps",
        str(args.fps),
    ]
    if flatten:
        assemble_cmd.extend(["--flatten", flatten])
    run_tool(assemble_cmd)

    if not args.no_verify:
        run_tool([
            sys.executable,
            str(script_dir / "verify_output.py"),
            "--file",
            gif_path,
            "--platform",
            args.platform,
        ])


if __name__ == "__main__":
    main()
