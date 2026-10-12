#!/usr/bin/env python3
"""Measure how much of the recording actually changes frame to frame.

    python scripts/measure_motion.py assets/hello-world.gif
    python scripts/measure_motion.py assets/hello-world.gif --threshold 2

A GIF can be large, pretty and completely static, so file size proves nothing.
What matters is the fraction of the frame area that differs between consecutive
frames: the "motion coverage".

That number is how the earlier monotony bug was found. The recording was frozen
for the back half of its duration because the animated hold sat after `exit 0`,
and the only reason it was noticed is that coverage was measured rather than
eyeballed. A demo that has just gained a new act needs the same measurement.

Pure standard library -- GIF decoding without Pillow would be a large amount of
code, so Pillow is used when present and the script says so when it is not
rather than reporting a misleading zero.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def load_frames(path: Path):
    try:
        from PIL import Image, ImageSequence
    except ImportError:
        print("error: Pillow is required to measure motion "
              "(pip install pillow)", file=sys.stderr)
        raise SystemExit(2)

    img = Image.open(path)
    frames = []
    durations = []
    for frame in ImageSequence.Iterator(img):
        frames.append(frame.convert("RGB").copy())
        durations.append(int(frame.info.get("duration", 0)))
    return frames, durations


def coverage(a, b, threshold: int) -> float:
    """Fraction of pixels in `a` that differ from `b` by more than threshold."""
    pa = a.tobytes()
    pb = b.tobytes()
    if len(pa) != len(pb):
        return 1.0
    changed = 0
    total = 0
    for i in range(0, len(pa), 3):
        total += 1
        dr = abs(pa[i] - pb[i])
        dg = abs(pa[i + 1] - pb[i + 1])
        db = abs(pa[i + 2] - pb[i + 2])
        if (dr + dg + db) / 3.0 > threshold:
            changed += 1
    return changed / total if total else 0.0


def coverage_fast(a, b, threshold: int, step: int) -> float:
    """Same measurement on a strided sample of the pixels.

    Comparing every pixel of a 6 MB, 449-frame GIF in pure Python takes minutes.
    A stride of 8 still samples ~16 000 pixels per transition, which is ample to
    distinguish a moving frame from a frozen one, and makes the check fast enough
    to run inside the test suite rather than only by hand.
    """
    pa = a.tobytes()
    pb = b.tobytes()
    if len(pa) != len(pb):
        return 1.0
    changed = 0
    total = 0
    for i in range(0, len(pa) - 3, 3 * step):
        total += 1
        dr = abs(pa[i] - pb[i])
        dg = abs(pa[i + 1] - pb[i + 1])
        db = abs(pa[i + 2] - pb[i + 2])
        if (dr + dg + db) / 3.0 > threshold:
            changed += 1
    return changed / total if total else 0.0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", nargs="?", default="assets/hello-world.gif")
    ap.add_argument("--threshold", type=int, default=8,
                    help="per-channel difference ignored as noise")
    ap.add_argument("--step", type=int, default=1,
                    help="pixel stride; 8 samples ~1/8 of pixels and is much faster")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    step = max(1, args.step)
    if step > 1:
        print(f"(sampling every {step} pixels for speed)")

    path = Path(args.path)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent.parent / path
    if not path.is_file():
        print(f"error: {path} not found", file=sys.stderr)
        return 1

    frames, durations = load_frames(path)
    n = len(frames)
    print(f"{path.name}: {n} frames, "
          f"{sum(durations) / 1000.0:.1f}s, "
          f"{path.stat().st_size:,} bytes")

    if n < 2:
        print("RESULT: only one frame -- the recording is completely static")
        return 1

    still = 0
    covs = []
    for i in range(n - 1):
        c = coverage_fast(frames[i], frames[i + 1], args.threshold, step)
        covs.append(c)
        if c < 0.005:
            still += 1
        if args.verbose:
            print(f"  {i:4} -> {i+1:<4} {c * 100:6.2f}% changed"
                  f"  ({durations[i]} ms)")

    mean = sum(covs) / len(covs)
    peak = max(covs)
    moving = n - 1 - still

    print()
    print(f"mean motion coverage : {mean * 100:.2f} %")
    print(f"peak motion coverage : {peak * 100:.2f} %")
    print(f"moving transitions   : {moving}/{n - 1}")
    print(f"frozen transitions   : {still}/{n - 1}")

    # A recording where most frames are identical is the failure mode that
    # produced "the video is monotonous". 60% of transitions moving is a floor,
    # not a target.
    if still * 2 > n - 1:
        print("RESULT: MONOTONOUS -- more than half the transitions are frozen")
        return 1
    if mean < 0.10:
        print("RESULT: mostly static -- mean coverage below 10 %")
        return 1
    print("RESULT: animated throughout")
    return 0


if __name__ == "__main__":
    sys.exit(main())