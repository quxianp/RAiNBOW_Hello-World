#!/usr/bin/env python3
"""Look at the recording.

`scripts/measure_motion.py` answers "is anything moving?". It does not answer
"what is on screen", and that distinction cost this repository three commits and
a wrong fix.

The published GIF once spent 22 of its 33 seconds frozen. The measurement said so,
repeatedly and accurately, and the natural reading was that the animation was too
slow or the tape's sleep too long -- so the sleep was shortened, then lengthened,
then shortened again. The GIF was frozen because `run.sh` was crashing, and the
screen was showing:

    run.sh: line 279: FAST: unbound variable

which is a fact about pixels and not about coverage. One frame at t=16s settled
it. This script exists so that the next time someone reaches for a statistic
about a recording, the alternative is already written down.

Usage:
    python scripts/inspect_frames.py                    # contact sheet
    python scripts/inspect_frames.py --at 0,8,16,24     # specific times
    python scripts/inspect_frames.py --at 16 --out f.png
    python scripts/inspect_frames.py --gif other.gif
    python scripts/inspect_frames.py --json             # measurements only

With no `--at`, it samples evenly across the runtime and tiles the frames into a
contact sheet, which is the fastest way to see where a take goes wrong.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_GIF = ROOT / "assets" / "hello-world.gif"


def _module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load(gif: pathlib.Path):
    mm = _module("measure_motion", ROOT / "scripts" / "measure_motion.py")
    frames, durations = mm.load_frames(gif)
    return mm, frames, durations


def pick(frames, durations, times):
    """Return [(index, seconds)] for each requested time."""
    starts, acc = [], 0
    for d in durations:
        starts.append(acc / 1000.0)
        acc += d
    total = acc / 1000.0
    out = []
    for t in times:
        t = max(0.0, min(t, max(0.0, total - 0.001)))
        idx = 0
        for i, s in enumerate(starts):
            if s <= t:
                idx = i
            else:
                break
        out.append((idx, starts[idx]))
    return out


def contact_sheet(gif, frames, durations, times, out: pathlib.Path, cols=3):
    from PIL import Image, ImageDraw

    picks = pick(frames, durations, times)
    tiles = []
    for idx, t in picks:
        im = frames[idx].convert("RGB")
        w = 420
        h = max(1, int(im.height * w / im.width))
        im = im.resize((w, h), Image.LANCZOS)
        canvas = Image.new("RGB", (w, h + 22), (13, 17, 23))
        canvas.paste(im, (0, 22))
        d = ImageDraw.Draw(canvas)
        d.text((6, 5), f"t={t:5.1f}s   frame {idx}/{len(frames)}", fill=(200, 200, 200))
        tiles.append(canvas)

    rows = (len(tiles) + cols - 1) // cols
    tw = tiles[0].width
    th = tiles[0].height
    sheet = Image.new("RGB", (cols * tw + (cols + 1) * 8,
                              rows * th + (rows + 1) * 8), (13, 17, 23))
    for i, tile in enumerate(tiles):
        r, c = divmod(i, cols)
        sheet.paste(tile, (8 + c * (tw + 8), 8 + r * (th + 8)))
    sheet.save(out)
    print(f"wrote {out}  ({len(tiles)} frames, {sheet.width}x{sheet.height})")
    for idx, t in picks:
        print(f"  t={t:5.1f}s -> frame {idx}")


def measurements(gif, mm, frames, durations):
    covs = [mm.coverage_fast(frames[i], frames[i + 1], 8, 8)
            for i in range(len(frames) - 1)]
    frozen = [i for i, c in enumerate(covs) if c < 0.005]
    starts, acc = [], 0
    for d in durations:
        starts.append(acc / 1000.0)
        acc += d
    last_moving = max((i for i, c in enumerate(covs) if c >= 0.005), default=None)
    end = total(durations)
    probes = [0, end / 4, end / 2, 3 * end / 4, max(0.0, end - 0.1)]
    distinct = {}
    for idx, _ in pick(frames, durations, probes):
        distinct[f"{starts[idx]:.1f}s"] = _distinct_colours(frames[idx])
    return {
        "bytes": gif.stat().st_size,
        "frames": len(frames),
        "seconds": round(total(durations), 2),
        "mean_coverage_pct": round(sum(covs) / len(covs) * 100, 3),
        "frozen_transitions": len(frozen),
        "frozen_pct": round(len(frozen) / len(covs) * 100, 2),
        "last_moving_frame": last_moving,
        "motion_ends_at_s": round(starts[last_moving], 2) if last_moving is not None else 0.0,
        "distinct_colours_at": distinct,
    }


def total(durations) -> float:
    return sum(durations) / 1000.0


def _distinct_colours(frame, every: int = 7) -> int:
    """How many different colours are in this frame, on a sparse sample.

    Sampled rather than exhaustive on purpose. Counting every RGB triple in a
    420 000-pixel frame means building 420 000 three-byte slices, which takes
    long enough that the first version of this script timed out before printing
    anything. A frame that has collapsed to one colour has one colour on any
    sample, which is the only thing this number is used for.
    """
    raw = frame.convert("RGB").tobytes()
    return len({raw[i:i + 3] for i in range(0, len(raw), 3 * every)})


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gif", default=str(DEFAULT_GIF))
    ap.add_argument("--at", default="",
                    help="comma-separated times in seconds; default samples evenly")
    ap.add_argument("--samples", type=int, default=9)
    ap.add_argument("--cols", type=int, default=3)
    ap.add_argument("--out", default=None, help="output PNG (default assets/frames.png)")
    ap.add_argument("--json", action="store_true",
                    help="print measurements instead of writing a sheet")
    args = ap.parse_args()

    gif = pathlib.Path(args.gif)
    if not gif.exists():
        print(f"inspect-frames: no {gif}", file=sys.stderr)
        return 1

    mm, frames, durations = load(gif)
    if len(frames) < 2:
        print("inspect-frames: too few frames to inspect", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(measurements(gif, mm, frames, durations), indent=2))
        return 0

    if args.at.strip():
        times = [float(x) for x in args.at.split(",") if x.strip()]
    else:
        end = total(durations)
        n = max(1, args.samples)
        times = [end * i / max(1, n - 1) if n > 1 else 0.0 for i in range(n)]

    out = pathlib.Path(args.out) if args.out else (ROOT / "assets" / "frames.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    contact_sheet(gif, frames, durations, times, out, cols=max(1, args.cols))
    return 0


if __name__ == "__main__":
    sys.exit(main())
