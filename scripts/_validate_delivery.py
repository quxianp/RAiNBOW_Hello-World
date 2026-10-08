"""Validate the workflow YAML and cross-check the repo against acceptance rules."""
import json
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
fails = []

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
               "screenshot the GitHub language bar",
               "refresh the README asset block", "commit and push the assets",
               "upload assets"):
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

print()
if fails:
    print(f"FAILED ({len(fails)}):")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("ALL WORKFLOW/REPO CHECKS PASSED")
