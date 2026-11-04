#!/usr/bin/env python3
"""Render the ~38-second launch teaser (1080x1350 MP4, the LinkedIn/Instagram feed format).

The scorecard shown is the real checkup result for the fictional demo company in
examples/demo/ (see docs/assets/demo-session.txt).

    pip install pillow imageio-ffmpeg
    python scripts/render_teaser.py -o teaser.mp4
"""

from __future__ import annotations

import argparse
import os
import subprocess
from collections.abc import Callable
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1350, 30
BG, PANEL, FG, DIM, ACCENT = "#11111b", "#1e1e2e", "#cdd6f4", "#7f849c", "#a6e3a1"
BLUE, YELLOW, ORANGE, RED, GREEN = "#89b4fa", "#f9e2af", "#fab387", "#f38ba8", "#a6e3a1"

SANS = "/System/Library/Fonts/HelveticaNeue.ttc"
MONO = "/System/Library/Fonts/Menlo.ttc"
_fonts: dict[tuple[str, int, int], ImageFont.FreeTypeFont] = {}


def font(size: int, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    path = MONO if mono else SANS
    if not os.path.exists(path):  # Linux fallback
        path = "/usr/share/fonts/truetype/dejavu/DejaVuSans" + ("Mono" if mono else "") + ("-Bold" if bold else "") + ".ttf"
        index = 0
    else:
        index = 1 if bold else 0
    key = (path, size, index)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(path, size, index=index)
    return _fonts[key]


def ease(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def mix(c1: str, c2: str, a: float) -> tuple[int, int, int]:
    p = [int(c1[i : i + 2], 16) for i in (1, 3, 5)]
    q = [int(c2[i : i + 2], 16) for i in (1, 3, 5)]
    return tuple(round(p[i] + (q[i] - p[i]) * a) for i in range(3))  # type: ignore[return-value]


def text(
    d: ImageDraw.ImageDraw, t: float, start: float, xy: tuple[int, int], s: str, f, color: str = FG, anchor: str = "la", bg: str = BG
) -> None:
    """Draw text that fades and slides up into place, starting at `start` seconds into the scene."""
    a = ease((t - start) / 0.45)
    if a <= 0:
        return
    x, y = xy
    d.text((x, y + round(24 * (1 - a))), s, font=f, fill=mix(bg, color, a), anchor=anchor)


def wrap(s: str, f, width: int) -> list[str]:
    words, lines, cur = s.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if f.getlength(trial) <= width:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    return [*lines, cur] if cur else lines


def header(d: ImageDraw.ImageDraw) -> None:
    d.text((70, 70), "b2b-agent-skills", font=font(30, mono=True), fill=DIM)
    d.text((W - 70, 70), "open source", font=font(30, mono=True), fill=DIM, anchor="ra")


# --- scenes: each draws frame t (seconds since the scene started) ---------------------------


def s_hook(d, t):
    text(d, t, 0.1, (90, 430), "You're building", font(92, True))
    text(d, t, 0.1, (90, 535), "a B2B startup.", font(92, True))
    for i, role in enumerate(["No CMO.", "No Head of Sales.", "No RevOps."]):
        text(d, t, 1.0 + 0.45 * i, (90, 720 + 95 * i), role, font(72), RED)


def s_question(d, t):
    text(d, t, 0.1, (90, 520), "So who's checking", font(88, True))
    text(d, t, 0.1, (90, 625), "your go-to-market?", font(88, True))
    text(d, t, 1.0, (90, 790), "Most founders find out it was", font(48), DIM)
    text(d, t, 1.0, (90, 855), "broken a quarter too late.", font(48), DIM)


def s_reveal(d, t):
    text(d, t, 0.1, (90, 470), "Your AI GTM team,", font(96, True), ACCENT)
    text(d, t, 0.5, (90, 580), "before you can", font(96, True))
    text(d, t, 0.5, (90, 690), "hire one.", font(96, True))
    text(d, t, 1.4, (90, 880), "48 skills · CMO · Head of Sales · RevOps · Strategy", font(38), DIM)


QA = [
    ("2/10", "Who are your best customers, and why did they buy?", "Mid-market fintech. The VP Sales buys after a forecast miss."),
    ("4/10", "Where do your leads and customers come from today?", "Mostly my network and a few LinkedIn posts."),
    ("7/10", "How do you price, and how often do you discount?", "$500/month flat. I discount for almost everyone."),
]


def terminal(d, top: int, bottom: int) -> None:
    d.rounded_rectangle((60, top, W - 60, bottom), 28, fill=PANEL)
    for i, c in enumerate((RED, YELLOW, GREEN)):
        d.ellipse((100 + 38 * i, top + 32, 122 + 38 * i, top + 54), fill=c)


def s_terminal(d, t):
    text(d, t, 0.0, (90, 170), "1. Answer 10 questions", font(64, True))
    text(d, t, 0.0, (90, 250), "About 3 minutes. Plus your website.", font(40), DIM)
    terminal(d, 360, 1240)
    cmd = "b2b-skills checkup northwind.example"
    typed = cmd[: max(0, min(len(cmd), int((t - 0.4) * 32)))]
    d.text((110, 430), "$ ", font=font(34, mono=True), fill=ACCENT)
    d.text((160, 430), typed + ("▌" if t < 2.0 and int(t * 3) % 2 == 0 else ""), font=font(34, mono=True), fill=FG)
    y = 520
    for i, (n, q, a) in enumerate(QA):
        start = 1.7 + 1.35 * i
        qlines = wrap(f"{n}  {q}", font(32, mono=True), W - 230)
        for ln in qlines:
            text(d, t, start, (110, y), ln, font(32, mono=True), BLUE, bg=PANEL)
            y += 46
        for ln in wrap(a, font(32, mono=True), W - 270):
            text(d, t, start + 0.5, (150, y), ln, font(32, mono=True), FG, bg=PANEL)
            y += 46
        text(d, t, start + 0.5, (110, y - 46 * len(wrap(a, font(32, mono=True), W - 270))), ">", font(32, mono=True), ACCENT, bg=PANEL)
        y += 24
    text(d, t, 6.0, (110, y + 10), "Reading northwind.example ...", font(32, mono=True), DIM, bg=PANEL)


AREAS = [
    ("ICP", "CMO", 62),
    ("Product-market fit", "Strategy", 60),
    ("Positioning", "CMO", 43),
    ("Proof", "CMO", 0),
    ("Demand & channels", "Growth", 0),
    ("Pricing & value", "Strategy", 0),
    ("Sales motion", "Head of Sales", 29),
    ("Pipeline & RevOps", "RevOps", 0),
]


def band(score: int) -> str:
    return GREEN if score >= 70 else YELLOW if score >= 50 else ORANGE if score >= 30 else RED


def s_scorecard(d, t):
    text(d, t, 0.0, (90, 150), "2. Get an honest scorecard", font(62, True))
    a = ease((t - 0.4) / 1.6)
    if t > 0.4:
        d.text((90, 250), "GTM score", font=font(44), fill=DIM)
        d.text((90, 300), f"{round(24 * a)}", font=font(150, True), fill=RED)
        d.text((90 + font(150, True).getlength(f"{round(24 * a)}") + 14, 395), "/100", font=font(52), fill=DIM)
    text(d, t, 1.6, (480, 330), "Biggest risk: growth depends on", font(34), FG)
    text(d, t, 1.6, (480, 376), "the founder's network and", font(34), FG)
    text(d, t, 1.6, (480, 422), "discounted, low-priced deals.", font(34), FG)
    x0, bar_x, bar_w, y = 90, 520, 380, 560
    for i, (name, owner, score) in enumerate(AREAS):
        start = 0.8 + 0.22 * i
        text(d, t, start, (x0, y + 82 * i), name, font(38, True))
        text(d, t, start, (x0, y + 82 * i + 44), owner, font(26), DIM)
        if t > start:
            d.rounded_rectangle((bar_x, y + 82 * i + 12, bar_x + bar_w, y + 82 * i + 48), 18, fill=PANEL)
            fill = ease((t - start) / 1.0) * score / 100
            d.rounded_rectangle((bar_x, y + 82 * i + 12, bar_x + max(36, round(bar_w * fill)), y + 82 * i + 48), 18, fill=band(score))
            label = str(round(score * ease((t - start) / 1.0)))
            d.text((W - 90, y + 82 * i + 8), label, font=font(40, True), fill=band(score), anchor="ra")


FIXES = [
    ("Proof", "CMO", "Add one named customer result, a before/after number and a quote, next to the headline."),
    ("Pricing & value", "Strategy", "Stop default discounting. Tie price to the cost of a forecast miss."),
    ("Pipeline & RevOps", "RevOps", "Build roughly 3x pipeline coverage before the quarter ends."),
]


def s_fixes(d, t):
    text(d, t, 0.0, (90, 170), "3. Fix the top 3 things", font(64, True))
    text(d, t, 0.0, (90, 252), "Each with the next step to take.", font(40), DIM)
    y = 380
    for i, (area, owner, fix) in enumerate(FIXES):
        start = 0.5 + 0.7 * i
        lines = wrap(fix, font(40), W - 300)
        h = 110 + 52 * len(lines)
        a = ease((t - start) / 0.45)
        if a > 0:
            off = round(24 * (1 - a))
            d.rounded_rectangle((60, y + off, W - 60, y + h + off), 26, fill=mix(BG, PANEL, a))
            d.text((110, y + 30 + off), f"{i + 1}", font=font(64, True), fill=mix(PANEL, ACCENT, a))
            d.text((190, y + 34 + off), f"{area}  ·  {owner}", font=font(34, True), fill=mix(PANEL, BLUE, a))
            for j, ln in enumerate(lines):
                d.text((190, y + 88 + 52 * j + off), ln, font=font(40), fill=mix(PANEL, FG, a))
        y += h + 34


def s_trust(d, t):
    text(d, t, 0.1, (90, 480), "Every score quotes", font(78, True))
    text(d, t, 0.1, (90, 580), "your words or your site.", font(78, True))
    text(d, t, 1.0, (90, 760), "Unknown is never scored as zero.", font(52), ACCENT)
    text(d, t, 1.5, (90, 840), "No invented stats. Checked in code.", font(52), DIM)


def s_cta(d, t):
    text(d, t, 0.1, (90, 330), "Run your free", font(96, True))
    text(d, t, 0.1, (90, 440), "GTM checkup.", font(96, True), ACCENT)
    a = ease((t - 0.8) / 0.45)
    if a > 0:
        d.rounded_rectangle((60, 640, W - 60, 760), 26, fill=mix(BG, PANEL, a))
        d.text((110, 700), "$ pip install b2b-agent-skills", font=font(44, mono=True), fill=mix(PANEL, FG, a), anchor="lm")
    text(d, t, 1.3, (90, 830), "github.com/pratsy/B2B_agent_skills", font(46, True), BLUE)
    text(d, t, 1.8, (90, 930), "Free · MIT · runs on your Claude subscription", font(38), DIM)
    text(d, t, 2.4, (90, 1080), "Want help deploying it, or to contribute?", font(40), FG)
    text(d, t, 2.4, (90, 1135), "Comment or DM me.", font(40, True), ACCENT)


SCENES: list[tuple[Callable, float]] = [
    (s_hook, 3.6),
    (s_question, 3.4),
    (s_reveal, 3.6),
    (s_terminal, 7.6),
    (s_scorecard, 6.8),
    (s_fixes, 5.4),
    (s_trust, 3.8),
    (s_cta, 5.5),
]


def frames():
    fade = 0.3
    for draw, dur in SCENES:
        for k in range(round(dur * FPS)):
            t = k / FPS
            img = Image.new("RGB", (W, H), BG)
            d = ImageDraw.Draw(img)
            header(d)
            draw(d, t)
            if draw is not s_cta and t > dur - fade:  # fade to background before the next scene
                img = Image.blend(img, Image.new("RGB", (W, H), BG), (t - (dur - fade)) / fade)
            yield img


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("-o", "--output", default="teaser.mp4")
    ap.add_argument("--still", type=float, help="write a PNG of the frame at this second instead")
    args = ap.parse_args()
    if args.still is not None:
        for i, img in enumerate(frames()):
            if i == round(args.still * FPS):
                img.save(args.output)
                return
    import imageio_ffmpeg

    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow", "-movflags", "+faststart", args.output]  # fmt: skip
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    assert proc.stdin
    for img in frames():
        proc.stdin.write(img.tobytes())
    proc.stdin.close()
    proc.wait()
    print(f"wrote {args.output} ({Path(args.output).stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
