#!/usr/bin/env python3
"""The committed GIF has to be a video.

CI runs `scripts/check_demo_motion.py` after recording, before publishing. That
closes the loop for the bot: it cannot commit a recording that does not move.

It does not close the loop for a person. A GIF can be committed by hand, or
restored from a backup, or checked out from a branch where it was already wrong,
and nothing local would object. So the same gate is asserted here, against
whatever is actually committed.

Skipped when the asset is absent, which is the normal state in a partial
checkout -- a missing demo is a packaging problem, and `validate_delivery.py`
already reports it as one. Failing here is reserved for a demo that is present
and static, which is the failure that has actually happened.

Thresholds are the ones in `scripts/check_demo_motion.py`, read from it rather
than repeated, so the test and the gate cannot drift apart.
"""

import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
GIF = ROOT / "assets" / "hello-world.gif"


def _gate():
    spec = importlib.util.spec_from_file_location(
        "check_demo_motion", ROOT / "scripts" / "check_demo_motion.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_committed_gif_is_animated():
    if not GIF.exists():
        return  # no asset in this checkout; validate_delivery.py reports that

    gate = _gate()
    result = gate.measure(GIF)
    if result is None:
        return  # too few frames to judge; not the same failure

    mean_pct, frozen_pct, frames, seconds = result

    assert frames >= 60, (
        f"assets/hello-world.gif has only {frames} frames over {seconds:.1f}s. "
        f"That is a slideshow, not a demo."
    )
    assert frozen_pct <= gate.MAX_FROZEN_PCT, (
        f"{frozen_pct:.1f} % of frame transitions are frozen, above the "
        f"{gate.MAX_FROZEN_PCT:.1f} % ceiling. The committed recording is "
        f"mostly a still image -- see logs/ERRORS.log E28 and E31."
    )
    assert mean_pct >= gate.MIN_MEAN_PCT, (
        f"mean motion coverage is {mean_pct:.2f} %, below the "
        f"{gate.MIN_MEAN_PCT:.1f} % floor. The recording moves too little to "
        f"read as animated."
    )


def test_committed_mp4_exists_and_is_not_tiny():
    mp4 = ROOT / "assets" / "hello-world.mp4"
    if not mp4.exists():
        return
    # A 30 s recording at any sane bitrate is far larger than this. The floor is
    # low on purpose: it exists to catch an accidentally-committed stub, not to
    # police the encoder.
    assert mp4.stat().st_size > 200_000, (
        f"assets/hello-world.mp4 is {mp4.stat().st_size:,} bytes, which is too "
        f"small to be a 30-second recording"
    )


def test_gate_thresholds_are_not_left_permissive():
    """The gate is only worth having if it can still fail.

    Someone under pressure to make a build green will widen a ceiling rather than
    fix the recording. This asserts the ceilings stay near the values that were
    chosen from real measurements, so that edit has to be deliberate.
    """
    gate = _gate()
    assert gate.MAX_FROZEN_PCT <= 55.0, (
        f"the frozen-transition ceiling is {gate.MAX_FROZEN_PCT:.1f} %. The "
        f"failures this gate exists for measured 84 % and 88 %; a ceiling above "
        f"55 % would wave through both."
    )
    assert gate.MIN_MEAN_PCT >= 2.0, (
        f"the mean-coverage floor is {gate.MIN_MEAN_PCT:.1f} %. The failing "
        f"recordings measured 1.79 % and 1.93 %; a floor under 2 % would wave "
        f"through both."
    )
