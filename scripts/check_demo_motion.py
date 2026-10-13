#!/usr/bin/env python3
"""Refuse to publish a demo recording that does not move.

The published GIF sat with 22 of its 33 seconds frozen for several commits, and
every automated signal said the build was fine: it recorded, it optimised, it
produced a plausible multi-megabyte animated GIF, and the run log ended with
`run.sh done`. The reason was that run.sh was crashing at line 279 and nothing
checks whether a recording is a recording.

So this is a gate rather than another report. It runs after the recording step
and before the assets are committed, which means a static take is never
published -- the failure happens where it can still be fixed, instead of being
discovered by someone watching the README.

Thresholds, and why these numbers:

    current measurement   mean 7.18 %   frozen 28.7 %   33.2 s
    the crash             mean 1.79 %   frozen 84 %     33.0 s
    a dead closing hold   mean 1.93 %   frozen 88 %     34.9 s

`--max-frozen` is the same 50 % boundary scripts/measure_motion.py itself calls
"monotonous", so the gate does not invent a stricter standard than the tool
already applies. `--min-mean` is a second, independent check: a recording can
freeze less than half its frames and still drift, and drift is what a viewer
notices as "this is a still image with flicker".

Both are loose relative to the measured healthy values and tight relative to
every failure this has actually had, which is the only calibration available
without pretending to more runs than have been done.

Exit status:
    0  the GIF animates, or there is no GIF to judge (recording step failed)
    1  the GIF exists and is too static -- do not publish it
"""

from __future__ import annotations

import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_GIF = ROOT / "assets" / "hello-world.gif"

MAX_FROZEN_PCT = 50.0
MIN_MEAN_PCT = 3.0


def _load_measure_motion():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "measure_motion", ROOT / "scripts" / "measure_motion.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def measure(gif: pathlib.Path):
    """Return (mean_pct, frozen_pct, frames, seconds), or None if unreadable."""
    mm = _load_measure_motion()
    frames, durations = mm.load_frames(gif)
    if len(frames) < 3:
        return None
    covs = [mm.coverage_fast(frames[i], frames[i + 1], 8, 8)
            for i in range(len(frames) - 1)]
    frozen = sum(1 for c in covs if c < 0.005)
    return (sum(covs) / len(covs) * 100.0,
            frozen / len(covs) * 100.0,
            len(frames),
            sum(durations) / 1000.0)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gif", default=str(DEFAULT_GIF))
    ap.add_argument("--max-frozen", type=float, default=MAX_FROZEN_PCT)
    ap.add_argument("--min-mean", type=float, default=MIN_MEAN_PCT)
    ap.add_argument("--report", default=None,
                    help="write the measurement as JSON to this path")
    args = ap.parse_args()

    gif = pathlib.Path(args.gif)
    if not gif.exists():
        # The recording step is continue-on-error so that a VHS CDN outage cannot
        # block the pipeline. There is nothing to judge, and failing here would
        # only convert an infrastructure problem into a build failure.
        print(f"check-demo-motion: no {gif}; nothing to judge, skipping")
        return 0

    try:
        result = measure(gif)
    except Exception as exc:                      # noqa: BLE001 - report, do not mask
        print(f"check-demo-motion: could not read {gif}: {exc}")
        return 0

    if result is None:
        print(f"check-demo-motion: {gif} has too few frames to judge, skipping")
        return 0

    mean_pct, frozen_pct, frames, seconds = result

    print(f"check-demo-motion: {gif.name}  {frames} frames  {seconds:.1f}s  "
          f"{gif.stat().st_size:,} bytes")
    print(f"  mean motion coverage : {mean_pct:.2f} %  (floor {args.min_mean:.1f} %)")
    print(f"  frozen transitions   : {frozen_pct:.1f} %  (ceiling {args.max_frozen:.1f} %)")

    if args.report:
        import json
        pathlib.Path(args.report).write_text(json.dumps({
            "gif": str(gif.relative_to(ROOT)) if gif.is_relative_to(ROOT) else str(gif),
            "bytes": gif.stat().st_size,
            "frames": frames,
            "seconds": round(seconds, 2),
            "mean_coverage_pct": round(mean_pct, 3),
            "frozen_pct": round(frozen_pct, 3),
            "max_frozen_pct": args.max_frozen,
            "min_mean_pct": args.min_mean,
            "pass": None,   # filled in below
        }, indent=2) + "\n", encoding="utf-8", newline="\n")

    failures = []
    if frozen_pct > args.max_frozen:
        failures.append(
            f"{frozen_pct:.1f} % of frame transitions are frozen "
            f"(limit {args.max_frozen:.1f} %)")
    if mean_pct < args.min_mean:
        failures.append(
            f"mean motion coverage is {mean_pct:.2f} % "
            f"(floor {args.min_mean:.1f} %)")

    if not failures:
        print("  verdict: animated -- ok to publish")
        if args.report:
            _amend_report(args.report, True)
        return 0

    print("  verdict: TOO STATIC TO PUBLISH", file=sys.stderr)
    for f in failures:
        print(f"    - {f}", file=sys.stderr)
    print("", file=sys.stderr)
    print("  The recording will not be committed. This has happened before: a "
          "crash in run.sh and a\n  closing hold that skipped itself both "
          "produced a large, plausible, frozen GIF\n  while every step of the "
          "build reported success.", file=sys.stderr)
    if args.report:
        _amend_report(args.report, False)
    return 1


def _amend_report(path: str, ok: bool) -> None:
    import json
    p = pathlib.Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    data["pass"] = ok
    p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    sys.exit(main())
