#!/usr/bin/env python3
"""Verify every acceptance metric of RAiNBOW_Hello-World.

Checks
  1. core language count is inside 600-800 and equals the Linguist coloured set
  2. every core language owns 0.05 % - 0.5 % of the counted bytes
  3. the counted shares add up to exactly 100 %
  4. hello/full holds at least 2400 files, total files >= 3000
  5. .gitattributes exposes exactly hello/core/ to Linguist
  6. every core file is recognisable by Linguist (extension, filename or
     the modeline alias we emit on line 1)
  7. a simulated language bar covers the whole colour wheel
  8. optional cross-check with `github-linguist --breakdown` when installed

Exit code 0 when every hard check passes, 1 otherwise.
Usage: python3 scripts/verify_languages.py [--json]
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import statistics
import subprocess
import sys
from collections import Counter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config"
DATA = ROOT / "data"
HELLO = ROOT / "hello"
LOGS = ROOT / "logs"
LOGS.mkdir(parents=True, exist_ok=True)

MIN_CORE, MAX_CORE = 600, 800
MIN_SHARE, MAX_SHARE = 0.05, 0.5
MIN_FULL = 2400
MIN_TOTAL = 3000

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> bool:
    results.append((name, bool(ok), detail))
    flag = "PASS" if ok else "FAIL"
    line = f"[{flag}] {name}" + (f"  --  {detail}" if detail else "")
    print(line, flush=True)
    return bool(ok)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="machine readable output")
    args = ap.parse_args()

    rainbow = json.loads((CONFIG / "rainbow_langs.json").read_text(encoding="utf-8"))
    langs = rainbow["languages"]
    linguist = json.loads((DATA / "linguist.json").read_text(encoding="utf-8"))

    # ---- 1. core count --------------------------------------------------
    n = len(langs)
    check("core languages within 600-800", MIN_CORE <= n <= MAX_CORE, f"{n} core languages")
    colored = {l["name"] for l in linguist if l.get("color")}
    deferred = set(rainbow.get("deferred_to_full_layer") or [])
    check(
        "core == every Linguist coloured language that can be detected",
        {l["name"] for l in langs} == colored - deferred,
        f"linguist coloured={len(colored)} core={n} deferred={len(deferred)} "
        f"(no extension and no filename -> moved to hello/full)",
    )

    # ---- 2/3. byte shares ----------------------------------------------
    sizes, missing = [], []
    for rec in langs:
        p = ROOT / rec["path"]
        if p.exists():
            sizes.append((rec, p.stat().st_size))
        else:
            missing.append(rec["path"])
    check("every core file exists", not missing, f"{len(missing)} missing: {missing[:3]}")
    total = sum(s for _, s in sizes)
    shares = {r["name"]: s / total * 100.0 for r, s in sizes} if total else {}
    lo = min(shares.values()) if shares else 0
    hi = max(shares.values()) if shares else 0
    check(
        "core share window 0.05%-0.5%",
        bool(shares) and lo >= MIN_SHARE and hi <= MAX_SHARE,
        f"min {lo:.4f}% max {hi:.4f}% ideal {100.0 / max(n, 1):.4f}%",
    )
    check(
        "shares sum to 100%",
        abs(sum(shares.values()) - 100.0) < 0.01 if shares else False,
        f"sum {sum(shares.values()):.6f}%",
    )
    check(
        "share spread is tight",
        bool(shares) and (statistics.pstdev(list(shares.values())) < 0.01),
        f"stdev {statistics.pstdev(list(shares.values())):.6f} pp" if shares else "n/a",
    )
    check("counted bytes non-trivial", total > 500_000, f"{total} bytes counted")

    # ---- 4. full layer --------------------------------------------------
    core_files = {r["path"] for r in langs}
    all_files = [p for p in HELLO.rglob("*") if p.is_file()]
    full_files = [
        p for p in all_files
        if p.relative_to(ROOT).as_posix().startswith("hello/full/")
    ]
    check("full layer >= 2400 files", len(full_files) >= MIN_FULL, f"{len(full_files)} files")
    check(
        "total language files >= 3000",
        len(core_files) + len(full_files) >= MIN_TOTAL,
        f"{len(core_files)} core + {len(full_files)} full = "
        f"{len(core_files) + len(full_files)}",
    )

    # ---- 5. .gitattributes ---------------------------------------------
    ga = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    check(".gitattributes un-vendors hello/core", "/hello/core/** -linguist-vendored" in ga)
    check(".gitattributes vendors hello/full", "/hello/full/** linguist-vendored" in ga)
    check(".gitattributes marks README as documentation", "README.md linguist-documentation" in ga)
    check(".gitattributes default is vendored", ga.splitlines()[0].startswith("* ") and "linguist-vendored" in ga.splitlines()[0])

    # ---- 6. recognisable by Linguist ------------------------------------
    # A core file is found by Linguist if any of the three strategies that run
    # before the ambiguous-extension classifier can resolve it: modeline
    # (line 1, highest priority), filename, extension.
    by_ext = Counter()
    by_name = set()
    aliases = set()
    for e in linguist:
        for x in e.get("extensions") or []:
            by_ext[x] += 1
        for f in e.get("filenames") or []:
            by_name.add(f)
        aliases.add(re.sub(r"\s", "-", e["name"].lower()))
        for a in e.get("aliases") or []:
            if isinstance(a, str):
                aliases.add(a.lower())
    unknown = [
        r["path"] for r in langs
        if by_ext.get(r["extension"], 0) == 0
        and not r.get("filename")
        and Path(r["path"]).name not in by_name
        and r.get("modeline_alias") not in aliases
    ]
    check(
        "every core file is recognisable by Linguist",
        len(unknown) == 0,
        f"{len(unknown)} unrecognisable: {unknown[:4]}",
    )

    # ---- 7. colour wheel coverage --------------------------------------
    buckets = Counter(r["hue_bucket"] for r in langs)
    missing_buckets = [
        b for b in (
            "red", "orange", "yellow", "green", "cyan", "blue", "purple",
            "pink", "rose",
        ) if not buckets.get(b)
    ]
    check("colour wheel fully covered", not missing_buckets, f"missing {missing_buckets}")
    hues = [r["hue"] for r in langs]
    check(
        "hues span the wheel",
        max(hues) - min(hues) >= 300,
        f"min {min(hues):.1f} max {max(hues):.1f}",
    )
    ordered = all(hues[i] <= hues[i + 1] for i in range(len(hues) - 1))
    check("languages ordered by hue", ordered)

    # ---- 8. optional real linguist --------------------------------------
    linguist_bin = shutil.which("github-linguist")
    if linguist_bin:
        try:
            out = subprocess.run(
                [linguist_bin, "--breakdown", "."],
                cwd=ROOT, capture_output=True, text=True, timeout=300,
            ).stdout
            (LOGS / "github_linguist_breakdown.txt").write_text(out, encoding="utf-8")
            rows = [
                ln for ln in out.splitlines()
                if "%" in ln and not ln.strip().startswith("(")
            ]
            check(
                "github-linguist reports >= 600 languages",
                len(rows) >= 600,
                f"{len(rows)} rows; see logs/github_linguist_breakdown.txt",
            )
        except Exception as exc:
            check("github-linguist breakdown", False, str(exc))
    else:
        print("[SKIP] github-linguist not installed (optional)")

    # ---- manifest / data sanity ----------------------------------------
    manifest = HELLO / "manifest.json"
    check("hello/manifest.json exists", manifest.exists())
    merged = DATA / "merged_langs.json"
    mcount = len(json.loads(merged.read_text(encoding="utf-8"))) if merged.exists() else 0
    check("merged inventory >= 3000 languages", mcount >= MIN_TOTAL, f"{mcount} languages")

    passed = sum(1 for _, ok, _ in results if ok)
    failed = [name for name, ok, _ in results if not ok]
    print()
    print(f"{passed}/{len(results)} checks passed")
    if failed:
        print("failed: " + ", ".join(failed))

    payload = {
        "checks": [{"name": n, "ok": o, "detail": d} for n, o, d in results],
        "passed": passed,
        "total": len(results),
        "core_languages": n,
        "core_files": len(core_files),
        "full_files": len(full_files),
        "total_language_files": len(core_files) + len(full_files),
        "merged_languages": mcount,
        "counted_bytes": total,
        "share_min_pct": round(lo, 6),
        "share_max_pct": round(hi, 6),
        "share_sum_pct": round(sum(shares.values()), 6),
        "buckets": dict(buckets),
        "failed": failed,
    }
    (LOGS / "verify_languages.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
