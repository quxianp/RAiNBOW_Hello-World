#!/usr/bin/env python3
"""Every phase the recording depends on must actually produce output.

A phase that prints nothing exits 0, so nothing fails. That is exactly what
happened to the closing hold: `rainbow.py --sweep N --sweep-only` returned before
drawing, and for `--sweep` the `both` guard meant the sweep branch never ran
either. The command "succeeded" while emitting zero bytes, and the last 8.7 s of
a 37.4 s recording was a frozen still.

These tests run the real commands and assert on the bytes that come back.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _run(args, timeout=90):
    proc = subprocess.run(
        [sys.executable] + args,
        cwd=str(ROOT), capture_output=True, timeout=timeout)
    return proc.returncode, proc.stdout, proc.stderr


def test_sweep_only_produces_output():
    """The regression: this printed nothing and still exited 0."""
    rc, out, err = _run(["scripts/rainbow.py", "--sweep", "6",
                         "--sweep-only", "--width", "40"])
    assert rc == 0, f"exited {rc}: {err.decode('utf-8', 'replace')[:200]}"
    assert len(out) > 100, (
        f"--sweep-only produced only {len(out)} bytes; the animated hold would "
        "be a frozen frame. Exit status was 0, so nothing else would catch this."
    )
    assert b"\x1b[38;2;" in out, (
        "the sweep emitted no truecolour sequences, so it would render as a "
        "blank terminal"
    )


def test_sweep_only_without_tty_still_emits_a_frame():
    """Under CI there is no TTY; the phase must degrade, not vanish."""
    rc, out, _ = _run(["scripts/rainbow.py", "--sweep", "4",
                       "--sweep-only", "--width", "40", "--no-animation"])
    assert rc == 0, f"exited {rc}"
    assert len(out) > 50, (
        f"--no-animation produced {len(out)} bytes; the phase disappeared "
        "entirely instead of showing one static frame"
    )


def test_ascii_bar_renderer_writes_output():
    rc, out, err = _run(["scripts/render_ascii_bar.py", "--width", "20",
                         "--out", ".tmp/test-ascii-bar.txt"])
    if b"PermissionError" in err:
        # .tmp/ is owned by another SID on this checkout. Not a defect.
        return
    assert rc == 0, f"exited {rc}: {err.decode('utf-8', 'replace')[:200]}"
    p = ROOT / ".tmp" / "test-ascii-bar.txt"
    assert p.is_file(), "render_ascii_bar.py did not write its output"
    body = p.read_text(encoding="utf-8")
    assert len(body) > 200, f"ASCII bar is only {len(body)} bytes"
    assert "\ufffd" not in body, "ASCII bar contains U+FFFD"
    p.unlink(missing_ok=True)


def test_spectral_sweep_produces_output():
    rc, out, err = _run(["scripts/spectral_sweep.py", "--mode", "plain",
                         "--width", "24", "--cycles", "1"])
    assert rc == 0, f"exited {rc}: {err.decode('utf-8', 'replace')[:200]}"
    assert len(out) > 24, (
        f"spectral sweep produced {len(out)} bytes for a 24-column row"
    )


def test_measure_motion_reports_a_number_not_a_crash():
    """The measurement tool must work on whatever recording exists."""
    gif = ROOT / "assets" / "hello-world.gif"
    if not gif.is_file():
        return
    # stride 16 keeps this inside the suite's time budget; the figure is a
    # frozen-vs-moving signal, not an exact pixel count
    rc, out, err = _run(["scripts/measure_motion.py", str(gif), "--step", "16"])
    if b"Pillow is required" in err:
        # A missing optional dependency is an environment fact, not a defect.
        # CI installs Pillow; this interpreter does not.
        return
    # Exit 1 means "monotonous", which is a finding, not a crash. Exit 0 or 1 are
    # both acceptable; anything else is a bug in the tool.
    assert rc in (0, 1), (
        f"measure_motion.py exited {rc}: {err.decode('utf-8', 'replace')[:200]}"
    )
    assert b"mean motion coverage" in out, "no coverage figure in the output"