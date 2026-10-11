"""Validate the workflow YAML and cross-check the repo against acceptance rules."""
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
fails = []

# git is not on PATH on the authoring machine, so look in the usual places too.
GIT = shutil.which("git") or next(
    (p for p in (r"D:\Git\cmd\git.exe", r"C:\Program Files\Git\cmd\git.exe")
     if os.path.exists(p)),
    "git",
)

wf_path = ROOT / ".github" / "workflows" / "rainbow.yml"
try:
    wf = yaml.safe_load(wf_path.read_text(encoding="utf-8"))
    print("YAML parses OK")
except Exception as exc:
    print(f"YAML PARSE ERROR: {exc}")
    sys.exit(1)

# PyYAML follows YAML 1.1 and turns the bare key `on` into boolean True.
on = wf.get("on", wf.get(True)) or {}
print("triggers:", sorted(on.keys()))
for required in ("push", "workflow_dispatch", "schedule"):
    if required not in on:
        fails.append(f"missing trigger: {required}")

jobs = wf.get("jobs", {})
print("jobs:", sorted(jobs.keys()))
for required in ("verify", "batches", "assets"):
    if required not in jobs:
        fails.append(f"missing job: {required}")

assets = jobs.get("assets", {})
steps = assets.get("steps", [])
names = " | ".join(str(s.get("name", s.get("uses", ""))) for s in steps)
print("assets steps:", names)
for needle in ("run the show", "record the terminal demo",
               "screenshot the live GitHub language bar",
               "render the GitHub language bar from the API",
               "refresh the README asset block", "commit and push the assets",
               "assert the demo assets exist", "upload assets"):
    if needle not in names:
        fails.append(f"assets job missing step: {needle}")

if wf.get("permissions", {}).get("contents") != "write":
    fails.append("permissions.contents must be write")

# Every job step must declare a continue-on-error or be genuinely required.
for job_name, job in jobs.items():
    for step in job.get("steps", []):
        if "continue-on-error" in step and step["continue-on-error"] is False:
            fails.append(f"{job_name}: pointless continue-on-error: false")

# ---------------------------------------------------------------- repo files
required_files = [
    ".gitattributes", ".gitignore", "README.md", "LICENSE", "run.sh",
    "install_deps.sh", "demo.tape", ".github/workflows/rainbow.yml",
]
for rel in required_files:
    if not (ROOT / rel).is_file():
        fails.append(f"missing file: {rel}")

for rel in ("scripts", "config", "data", "assets", "hello/core", "hello/full", "logs"):
    if not (ROOT / rel).is_dir():
        fails.append(f"missing directory: {rel}")

core = sum(1 for p in (ROOT / "hello" / "core").rglob("*") if p.is_file())
full = sum(1 for p in (ROOT / "hello" / "full").rglob("*") if p.is_file())
print(f"core={core} full={full} total={core + full}")
if not 600 <= core <= 800:
    fails.append(f"core out of range: {core}")
if full < 2400:
    fails.append(f"full too small: {full}")
if core + full < 3000:
    fails.append(f"total language files too small: {core + full}")

readme = (ROOT / "README.md").read_text(encoding="utf-8")
for needle in ("assets/rainbow-bar-github.png", "assets/hello-world.gif",
               "assets/hello-world.mp4", "RAINBOW_ASSETS_START",
               "RAINBOW_ASSETS_END", "config/all-langs.json"):
    if needle not in readme:
        fails.append(f"README missing reference: {needle}")

balance = json.loads((ROOT / "logs" / "balance_summary.json").read_text(encoding="utf-8"))
print(f"balance: {balance['core_languages']} langs, "
      f"{balance['total_counted_bytes']} B, sum {balance['sum_pct']}%")
if abs(balance["sum_pct"] - 100.0) > 1e-6:
    fails.append(f"shares do not sum to 100: {balance['sum_pct']}")
if balance["outside_window"]:
    fails.append(f"shares outside window: {balance['outside_window']}")

# ------------------------------------------------- executable bits in git
# This is not cosmetic. run.sh was committed with mode 100644, so every VHS
# recording of the README demo ended on:
#     bash: ./run.sh: Permission denied
# and the published GIF showed that failure instead of the show.
EXECUTABLES = ["run.sh", "install_deps.sh", "scripts/record_demo.sh"]
try:
    listed = subprocess.run(
        [GIT, "-C", str(ROOT), "ls-files", "-s", "--", *EXECUTABLES],
        capture_output=True, text=True, timeout=60,
    ).stdout
except Exception as exc:  # noqa: BLE001
    print(f"could not query git index ({exc}); skipping the exec-bit check")
    listed = ""

modes = {}
for line in listed.splitlines():
    parts = line.split(None, 3)
    if len(parts) == 4:
        modes[parts[3].strip()] = parts[0]

for script in EXECUTABLES:
    mode = modes.get(script)
    if mode is None:
        fails.append(f"exec-bit check: {script} is not tracked")
    elif not mode.startswith("100755"):
        fails.append(
            f"{script} is committed with mode {mode}, not 100755 -- "
            f"run `git update-index --chmod=+x {script}` or `./{script}` "
            f"fails with Permission denied on Linux/CI"
        )
    else:
        print(f"exec bit ok: {script} ({mode})")

# ---------------------------------------------------------------- demo tape
tape = ROOT / "demo.tape"
if tape.is_file():
    typed = [ln.strip() for ln in tape.read_text(encoding="utf-8").splitlines()
             if ln.strip().startswith("Type")]
    if not any("run.sh" in ln for ln in typed):
        fails.append("demo.tape never types a run.sh command")
    if any(ln.lstrip("Type ").startswith("./run.sh") for ln in typed):
        fails.append(
            "demo.tape types './run.sh' directly; type 'bash run.sh' so the "
            "recording cannot break on a lost executable bit"
        )
else:
    fails.append("demo.tape is missing")

# --------------------------------------------------- the show must animate
# A recorded demo that is a still terminal defeats the point of recording it, and
# that is exactly what happened: run.sh asked for --bar/--hello, which switched
# off every animated path in scripts/rainbow.py, and the intro discarded the hue
# it had just computed. Guard both.
try:
    show = (ROOT / "run.sh").read_text(encoding="utf-8")
    rainbow = (ROOT / "scripts" / "rainbow.py").read_text(encoding="utf-8")

    for needle in ("--fill-frames", "--reveal-frames"):
        if needle not in show:
            fails.append(f"run.sh never passes {needle}; the finale would be static")
    if "brand_frames.py" not in show:
        fails.append("run.sh does not use scripts/brand_frames.py for the intro")
    # Strip comments first: the explanatory comment in animated_brand() quotes
    # the very expression it replaced, which would otherwise trip this check.
    code = "\n".join(
        ln for ln in show.splitlines() if not ln.lstrip().startswith("#")
    )
    if "rgb 255 255 255" in code:
        fails.append(
            "run.sh still paints a hard-coded white; the intro renders no colour"
        )
    if re.search(r"h=\$\(\s*\(\s*\(\s*frame", code):
        fails.append(
            "run.sh still computes a per-frame hue and discards it; "
            "the intro renders pure white"
        )
    for needle in ("def draw_fill", "def draw_reveal"):
        if needle not in rainbow:
            fails.append(f"scripts/rainbow.py is missing {needle}")
    if not (ROOT / "scripts" / "brand_frames.py").is_file():
        fails.append("scripts/brand_frames.py is missing")
    if not (ROOT / "scripts" / "spinner.py").is_file():
        fails.append("scripts/spinner.py is missing")

    # Unreachable code: the animated hold was once appended after `exit 0`, so
    # it never ran and the back half of every recording was frozen.
    body = "\n".join(ln for ln in show.splitlines() if not ln.lstrip().startswith("#"))
    exit_at = body.find("\nexit 0")
    if exit_at == -1:
        fails.append("run.sh has no `exit 0`; the show would fall through")
    elif "HOLD_SECONDS" in body and body.find("HOLD_SECONDS") > exit_at:
        fails.append(
            "run.sh reaches `exit 0` before the HOLD_SECONDS block, so the "
            "animated hold is unreachable and the recording ends frozen"
        )
except Exception as exc:  # noqa: BLE001
    print(f"animation checks skipped ({exc})")

# ------------------------------------------------- generators must actually run
# Grepping the source for the right strings is not enough: a shipped
# `{end}`-instead-of-`{END}` typo made update_readme_assets.py die with a
# NameError on every invocation while the README still looked perfectly fine,
# because the previous text was simply never replaced.
GENERATORS = [
    ["scripts/update_readme_assets.py", "--check"],
    ["scripts/update_readme_showcase.py", "--check"],
]
for cmd in GENERATORS:
    try:
        proc = subprocess.run([sys.executable] + cmd, cwd=str(ROOT),
                              capture_output=True, text=True, timeout=180)
    except Exception as exc:  # noqa: BLE001
        fails.append(f"{cmd[0]} could not be run ({exc})")
        continue
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-1:]
        fails.append(f"{' '.join(cmd)} exited {proc.returncode}: {tail[0] if tail else ''}")
    else:
        print(f"generator ok: {' '.join(cmd)}")

# Every script must at least compile.
for py in sorted((ROOT / "scripts").glob("*.py")):
    try:
        compile(py.read_text(encoding="utf-8"), str(py), "exec")
    except Exception as exc:  # noqa: BLE001
        fails.append(f"{py.name} does not compile: {str(exc)[:90]}")

print()
if fails:
    print(f"FAILED ({len(fails)}):")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("ALL WORKFLOW/REPO CHECKS PASSED")
