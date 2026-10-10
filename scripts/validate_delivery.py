"""Validate the workflow YAML and cross-check the repo against acceptance rules."""
import json
import os
import pathlib
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

print()
if fails:
    print(f"FAILED ({len(fails)}):")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("ALL WORKFLOW/REPO CHECKS PASSED")
