#!/usr/bin/env python3
"""Render a captured terminal session to an animated GIF (no VHS/ffmpeg needed).

Capture a real session first, then render it:

    python scripts/render_demo_gif.py --record docs/assets/demo-session.txt   # runs the demo commands
    python scripts/render_demo_gif.py docs/assets/demo-session.txt -o docs/assets/demo.gif

Lines starting with "$ " are animated as typed commands; every other line is
output, shown exactly as captured. Requires Pillow (pip install pillow).
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import textwrap
from pathlib import Path

DEMO_COMMANDS = [
    "b2b-skills list | head -5",
    "python3 -c \"import json;print(json.load(open('examples/fixtures/deal_risk_input.json'))['pillar_evidence']['economic_buyer'])\"",
    "b2b-skills run deal-risk-assessor -i examples/fixtures/deal_risk_input.json --provider claude-code",
]
DISPLAY_AS = {1: "jq -r .pillar_evidence.economic_buyer examples/fixtures/deal_risk_input.json"}

BG, FG, PROMPT, DIM, KEY, STR, NUM, BAR = "#1e1e2e", "#cdd6f4", "#a6e3a1", "#7f849c", "#89b4fa", "#f9e2af", "#fab387", "#181825"
COLS, ROWS, FONT_SIZE, PAD = 104, 34, 15, 22


def record(path: Path) -> None:
    lines: list[str] = []
    for i, cmd in enumerate(DEMO_COMMANDS):
        lines.append(f"$ {DISPLAY_AS.get(i, cmd)}")
        out = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=600)
        lines += (out.stdout + out.stderr).rstrip("\n").splitlines()
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"recorded {len(lines)} lines to {path}")


def _font():
    from PIL import ImageFont

    for candidate in ("/System/Library/Fonts/Menlo.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"):
        if os.path.exists(candidate):
            return ImageFont.truetype(candidate, FONT_SIZE)
    return ImageFont.load_default()


def _color(line: str) -> list[tuple[str, str]]:
    """Minimal JSON-ish highlighting: keys, strings, numbers."""
    import re

    if line.startswith("$ "):
        return [("$ ", PROMPT), (line[2:], FG)]
    m = re.match(r'^(\s*)("[^"]+")(:\s*)(.*)$', line)
    if not m:
        return [(line, FG)]
    indent, key, colon, rest = m.groups()
    value_color = STR if rest.startswith('"') else NUM if re.match(r"^-?\d", rest) else FG
    return [(indent, FG), (key, KEY), (colon, FG), (rest, value_color)]


def render(session: Path, out: Path) -> None:
    from PIL import Image, ImageDraw

    font = _font()
    cw = font.getbbox("M")[2]
    lh = int(FONT_SIZE * 1.45)
    width, height = PAD * 2 + cw * COLS, PAD * 2 + 36 + lh * ROWS
    raw = session.read_text(encoding="utf-8").splitlines()
    lines = [ln.encode().decode("unicode_escape") if "\\u" in ln else ln for ln in raw]
    wrapped: list[str] = []
    for ln in lines:
        if len(ln) <= COLS or ln.startswith("$ "):
            wrapped.append(ln[:COLS])
            continue
        indent = " " * (len(ln) - len(ln.lstrip()) + 2)
        wrapped += textwrap.wrap(ln, COLS, subsequent_indent=indent, drop_whitespace=False) or [ln]
    lines = wrapped

    frames: list[Image.Image] = []
    durations: list[int] = []

    def snap(screen: list[str], ms: int, cursor: bool = False) -> None:
        img = Image.new("RGB", (width, height), BG)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, width, 30], fill=BAR)
        for i, c in enumerate(("#f38ba8", "#f9e2af", "#a6e3a1")):
            d.ellipse([14 + i * 20, 9, 26 + i * 20, 21], fill=c)
        d.text((width // 2 - cw * 8, 7), "b2b-agent-skills", font=font, fill=DIM)
        visible = screen[-ROWS:]
        for row, text in enumerate(visible):
            x, y = PAD, 30 + PAD // 2 + row * lh
            for chunk, color in _color(text):
                d.text((x, y), chunk, font=font, fill=color)
                x += cw * len(chunk)
            if cursor and row == len(visible) - 1:
                d.rectangle([x + 2, y + 2, x + cw, y + lh - 4], fill=FG)
        frames.append(img)
        durations.append(ms)

    screen: list[str] = []
    for line in lines:
        if line.startswith("$ "):
            snap([*screen, "$ "], 500, cursor=True)
            cmd = line[2:]
            step = max(1, len(cmd) // 25)
            for i in range(step, len(cmd) + step, step):
                snap([*screen, "$ " + cmd[:i]], 45, cursor=True)
            screen.append(line)
            snap(screen, 900 if "run " in cmd else 350)
        else:
            screen.append(line)
            snap(screen, 60)
    durations[-1] = 6000
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=durations, loop=0, optimize=True)
    print(f"wrote {out} ({len(frames)} frames, {out.stat().st_size // 1024} KB)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("session", type=Path)
    parser.add_argument("-o", "--output", type=Path, default=Path("docs/assets/demo.gif"))
    parser.add_argument("--record", action="store_true", help="run the demo commands and write the session file")
    args = parser.parse_args()
    if args.record:
        record(args.session)
        return 0
    render(args.session, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
