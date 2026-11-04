"""An original soundtrack for the launch teaser, synthesized in code (no samples, no licensing).

Tempo is set so a bar is 1.75 s: the hook builds over the first two scenes, the beat drops on
"Your AI GTM team" (7.0 s), drums step out for the trust message, and come back for the call to action.

    pip install numpy scipy
    python scripts/teaser_music.py -o teaser.wav --seconds 39.7
"""

from __future__ import annotations

import argparse
import wave

import numpy as np
from scipy.signal import butter, lfilter

SR = 44100
BAR = 1.75
BEAT = BAR / 4
DROP, BREAK_START, BREAK_END = 7.0, 30.4, 34.2
# Am - F - C - G, as MIDI notes (root, third, fifth)
CHORDS = [(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)]


def hz(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


def lowpass(x: np.ndarray, cutoff: float) -> np.ndarray:
    b, a = butter(2, cutoff / (SR / 2))
    return lfilter(b, a, x)


def highpass(x: np.ndarray, cutoff: float) -> np.ndarray:
    b, a = butter(2, cutoff / (SR / 2), btype="high")
    return lfilter(b, a, x)


def saw(f: float, t: np.ndarray) -> np.ndarray:
    return 2 * ((f * t) % 1.0) - 1


def place(track: np.ndarray, sound: np.ndarray, at: float) -> None:
    i = int(at * SR)
    if i >= len(track):
        return
    n = min(len(sound), len(track) - i)
    track[i : i + n] += sound[:n]


def env(n: int, attack: float, decay: float) -> np.ndarray:
    t = np.arange(n) / SR
    return np.minimum(1.0, t / max(attack, 1e-4)) * np.exp(-t / decay)


def render(seconds: float, seed: int = 7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    pad, arp, bass, kick, hats, clap, fx = (np.zeros(n) for _ in range(7))
    drums_on = lambda s: DROP <= s < BREAK_START or s >= BREAK_END  # noqa: E731

    bars = int(np.ceil(seconds / BAR))
    for b in range(bars):
        start = b * BAR
        chord = CHORDS[b % 4]
        # pad: detuned saws, soft attack, darker in the intro and the breakdown
        m = int(BAR * SR)
        t = np.arange(m) / SR
        tone = sum(saw(hz(note) * d, t) for note in chord for d in (0.997, 1.003))
        e = np.minimum(1, t / 0.35) * np.minimum(1, (BAR - t) / 0.2)
        place(pad, lowpass(tone * e, 1400 if drums_on(start) else 900) * 0.05, start)
        # arpeggio: 16th-note plucks over the chord, an octave up
        pattern = [0, 1, 2, 1, 0, 2, 1, 2]
        for k in range(16):
            at = start + k * BEAT / 4
            if at < 3.5 and k % 2:  # sparser in the first two bars
                continue
            note = chord[pattern[k % 8]] + 12 + (12 if k % 8 == 6 else 0)
            q = int(0.22 * SR)
            tq = np.arange(q) / SR
            pl = (np.sin(2 * np.pi * hz(note) * tq) + 0.35 * np.sign(np.sin(2 * np.pi * hz(note) * tq))) * env(q, 0.003, 0.07)
            place(arp, pl * 0.11, at)
        if not drums_on(start):
            continue
        # bass: off-beat eighths on the root
        for k in range(8):
            if k % 2 == 0:
                continue
            at = start + k * BEAT / 2
            q = int(BEAT / 2 * SR)
            tq = np.arange(q) / SR
            f = hz(chord[0] - 24)
            tone = np.tanh(2.5 * np.sin(2 * np.pi * f * tq)) * env(q, 0.005, 0.12)
            place(bass, tone * 0.32, at)
        for k in range(4):
            at = start + k * BEAT
            q = int(0.35 * SR)
            tq = np.arange(q) / SR
            sweep = 2 * np.pi * np.cumsum(50 + 110 * np.exp(-tq / 0.03)) / SR
            place(kick, np.sin(sweep) * env(q, 0.001, 0.12) * 0.75, at)
            hq = int(0.05 * SR)
            place(hats, highpass(rng.standard_normal(hq), 7000) * env(hq, 0.001, 0.015) * 0.12, at + BEAT / 2)
            if k in (1, 3) and start >= 18.2:  # claps join at the scorecard
                cq = int(0.18 * SR)
                c = lowpass(highpass(rng.standard_normal(cq), 900), 3500) * env(cq, 0.001, 0.05)
                place(clap, c * 0.25, at)

    # risers into the drop and out of the breakdown: noise swelling over one bar
    for end in (DROP, BREAK_END):
        q = int(BAR * SR)
        swell = np.linspace(0, 1, q) ** 2
        place(fx, highpass(rng.standard_normal(q), 2500) * swell * 0.12, end - BAR)
    # an impact on the drop
    q = int(1.2 * SR)
    tq = np.arange(q) / SR
    place(fx, np.sin(2 * np.pi * 45 * tq) * env(q, 0.002, 0.4) * 0.5, DROP)

    left = pad + kick + bass + clap + fx + 0.75 * arp + 1.15 * hats
    right = pad + kick + bass + clap + fx + 1.15 * arp + 0.75 * hats
    mix = np.stack([left, right], axis=1)
    mix /= np.max(np.abs(mix)) + 1e-9
    mix = np.tanh(1.4 * mix) / np.tanh(1.4) * 0.85
    fade_in, fade_out = int(0.4 * SR), int(2.0 * SR)
    mix[:fade_in] *= np.linspace(0, 1, fade_in)[:, None]
    mix[-fade_out:] *= np.linspace(1, 0, fade_out)[:, None]
    return mix


def write_wav(path: str, audio: np.ndarray) -> None:
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((audio * 32767).astype("<i2").tobytes())


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("-o", "--output", default="teaser.wav")
    ap.add_argument("--seconds", type=float, default=39.7)
    args = ap.parse_args()
    write_wav(args.output, render(args.seconds))
    print(f"wrote {args.output}")
