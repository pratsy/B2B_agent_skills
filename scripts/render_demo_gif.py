#!/usr/bin/env python3
"""Render a captured terminal session to an animated GIF (no VHS/ffmpeg needed).

Capture a real session first (it builds a workspace from examples/demo/ and runs real
playbooks through your Claude login), then render it:

    python scripts/render_demo_gif.py --record docs/assets/demo-session.txt
    python scripts/render_demo_gif.py docs/assets/demo-session.txt -o docs/assets/demo.gif

Lines starting with "$ " are animated as typed commands; every other line is
output, shown exactly as captured. Requires Pillow (pip install pillow).
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any

DEMO_COMMANDS = [
    "ls docs/",
    "b2b-skills checkup northwind.example --text homepage.txt --answers answers.txt --docs docs/ --brief --provider claude-code",
]
DISPLAY_AS: dict[int, str] = {}
# The scorecard is wider than the GIF; the fixes already say what's wrong, so show the sources instead.
GIF_HIDDEN_COLUMNS = {"What we found"}
DEMO_DIR = Path(__file__).resolve().parents[1] / "examples" / "demo"

BG, FG, PROMPT, DIM, KEY, STR, NUM, BAR = "#1e1e2e", "#cdd6f4", "#a6e3a1", "#7f849c", "#89b4fa", "#f9e2af", "#fab387", "#181825"
COLS, ROWS, FONT_SIZE, PAD = 104, 34, 15, 22


def record(path: Path) -> None:
    """Create a throwaway workspace from examples/demo/ and run the demo commands in it, for real."""
    import shutil
    import tempfile

    ws = Path(tempfile.mkdtemp(prefix="b2b-demo-")) / "my-gtm"
    subprocess.run(["b2b-skills", "init", str(ws), "--yes"], check=True, capture_output=True)
    shutil.copy(DEMO_DIR / "company.md", ws / "company.md")
    shutil.copy(DEMO_DIR / "icp.json", ws / "gtm" / "icp.json")
    for name in ("win-loss-and-homepage.md", "leads.csv", "answers.txt", "homepage.txt"):
        shutil.copy(DEMO_DIR / name, ws / name)
    shutil.copytree(DEMO_DIR / "docs", ws / "docs")
    lines: list[str] = []
    for i, cmd in enumerate(DEMO_COMMANDS):
        lines.append(f"$ {DISPLAY_AS.get(i, cmd)}")
        out = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=600, cwd=ws)
        lines += out.stdout.rstrip("\n").splitlines()
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
    if TAG in line:
        chunks: list[tuple[str, str]] = []
        parts = line.split(TAG)
        chunks.append((parts[0], FG))
        for part in parts[1:]:
            chunks += [(part[1], DOT_COLOR.get(part[0], FG)), (part[2:], FG)]
        return chunks
    if line.lstrip().startswith("#"):
        return [(line, PROMPT if line.startswith("## ") else KEY)]
    m = re.match(r'^(\s*)("[^"]+")(:\s*)(.*)$', line)
    if not m:
        return [(line, FG)]
    indent, key, colon, rest = m.groups()
    value_color = STR if rest.startswith('"') else NUM if re.match(r"^-?\d", rest) else FG
    return [(indent, FG), (key, KEY), (colon, FG), (rest, value_color)]


TAG = "\x00"
DOTS = {
    "🟢": ("G", "●", "#a6e3a1"),
    "🟡": ("Y", "●", "#f9e2af"),
    "🟠": ("O", "●", "#fab387"),
    "🔴": ("R", "●", "#f38ba8"),
    "⚪": ("W", "○", "#7f849c"),
}
DOT_COLOR = {code: color for code, _, color in DOTS.values()}


def _tagged(cell: str) -> str:
    for emoji, (code, dot, _) in DOTS.items():
        cell = cell.replace(emoji, f"{TAG}{code}{dot}")
    return cell


def _visible_len(s: str) -> int:
    return len(re.sub(TAG + ".", "", s))


def _layout_tables(lines: list[str]) -> list[str]:
    """Markdown tables -> aligned columns that fit the terminal; emoji dots -> colored circles (tagged for _color)."""
    out: list[str] = []
    i = 0
    while i < len(lines):
        if not lines[i].lstrip().startswith("|"):
            out.append(lines[i])
            i += 1
            continue
        rows = []
        while i < len(lines) and lines[i].lstrip().startswith("|"):
            cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            if not all(set(c) <= set("-: ") for c in cells):
                rows.append([_tagged(c) for c in cells])
            i += 1
        ncol = max(len(r) for r in rows)
        rows = [r + [""] * (ncol - len(r)) for r in rows]
        keep = [c for c in range(ncol) if rows[0][c] not in GIF_HIDDEN_COLUMNS]
        rows, ncol = [[r[c] for c in keep] for r in rows], len(keep)
        natural = [max(_visible_len(r[c]) for r in rows) for c in range(ncol)]
        widths = [min(n, 23) for n in natural]
        widths[-1] = min(natural[-1], 52)  # "Based on": the sources are the point, so show them whole
        widest = max(range(ncol), key=lambda c: natural[c])  # the column with the most text gets the spare width
        widths[widest] = max(10, COLS - (sum(widths) - widths[widest]) - 2 * (ncol - 1))
        for r in rows:
            cells = []
            for c, cell in enumerate(r):
                if TAG not in cell and len(cell) > widths[c]:
                    cell = cell[: widths[c] - 1] + "…"
                cells.append(cell + " " * max(0, widths[c] - _visible_len(cell)))
            out.append("  ".join(cells).rstrip())
    return out


def _theme_palette() -> Any:
    """A fixed palette: each theme color plus anti-aliasing blends toward the background."""
    from PIL import Image

    def rgb(h: str) -> tuple[int, int, int]:
        return int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)

    bg = rgb(BG)
    colors = [bg, rgb(BAR)]
    for c in (FG, PROMPT, DIM, KEY, STR, NUM, "#f38ba8", "#f9e2af", "#a6e3a1"):
        target = rgb(c)
        colors += [tuple(round(b + (x - b) * k / 7) for b, x in zip(bg, target, strict=True)) for k in range(1, 8)]
    flat = [v for col in dict.fromkeys(colors) for v in col]
    pal = Image.new("P", (1, 1))
    pal.putpalette(flat + [0] * (768 - len(flat)))
    return pal


def render(session: Path, out: Path) -> None:
    from PIL import Image, ImageDraw

    font = _font()
    cw = font.getbbox("M")[2]
    lh = int(FONT_SIZE * 1.45)
    width, height = PAD * 2 + cw * COLS, PAD * 2 + 36 + lh * ROWS
    raw = session.read_text(encoding="utf-8").splitlines()
    lines = [ln.encode().decode("unicode_escape") if "\\u" in ln else ln for ln in raw]
    lines = [ln if ln.startswith("$ ") else ln.replace("**", "") for ln in lines]  # show markdown as a terminal would
    lines = _layout_tables(lines)
    wrapped: list[str] = []
    for ln in lines:
        if TAG in ln:  # laid-out table rows already fit; slicing would count the invisible color tags
            wrapped.append(ln)
            continue
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
    pending_output = 0
    for line in lines:
        if line.startswith("$ "):
            snap([*screen, "$ "], 500, cursor=True)
            cmd = line[2:]
            step = max(1, len(cmd) // 12)
            for i in range(step, len(cmd) + step, step):
                snap([*screen, "$ " + cmd[:i]], 45, cursor=True)
            screen.append(line)
            snap(screen, 900 if "run " in cmd else 350)
        else:
            screen.append(line)
            pending_output += 1
            if pending_output % 2 == 0:  # two lines per frame keeps the GIF small
                snap(screen, 110)
    snap(screen, 6000)
    paletted = [f.quantize(palette=_theme_palette(), dither=Image.Dither.NONE) for f in frames]
    paletted[0].save(out, save_all=True, append_images=paletted[1:], duration=durations, loop=0, optimize=True, disposal=1)
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
