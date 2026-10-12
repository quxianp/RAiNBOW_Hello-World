#!/usr/bin/env python3
"""A dependency-free test runner for this repository.

    python scripts/run_tests.py
    python scripts/run_tests.py -v
    python scripts/run_tests.py tests/test_bar_invariants.py

Why hand-rolled rather than pytest: the acceptance job already installs a
specific dependency set and runs on two Python versions. Adding a test
framework to that mix means one more thing that can break the gate for reasons
unrelated to the repository. A runner that only uses the standard library cannot
be the reason CI goes red.

Discovers ``tests/test_*.py``, imports each, calls every ``test_*`` function it
finds, and reports pass/fail with the traceback for failures. Tests receive no
arguments; anything they need should be computed or cached at module level.

Exit status is 0 only if every test passed.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / "tests"


def load(path: Path):
    """Import a test module by path, without needing it on sys.path."""
    name = f"rainbow_test_{path.stem}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def discover(paths: list[str]) -> list[Path]:
    if paths:
        out = []
        for p in paths:
            path = Path(p)
            if not path.is_absolute():
                path = ROOT / path
            out.append(path)
        return out
    if not TESTS.is_dir():
        return []
    return sorted(TESTS.glob("test_*.py"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="*", help="specific test files to run")
    ap.add_argument("-v", "--verbose", action="store_true")
    ap.add_argument("-q", "--quiet", action="store_true")
    args = ap.parse_args()

    files = discover(args.paths)
    if not files:
        print("no tests found", file=sys.stderr)
        return 1

    passed = failed = skipped = 0
    failures: list[tuple[str, str]] = []
    started = time.time()

    for path in files:
        rel = path.relative_to(ROOT)
        if not args.quiet:
            print(f"\n{rel}")
        try:
            mod = load(path)
        except Exception:
            failed += 1
            failures.append((str(rel), traceback.format_exc()))
            print("  ERROR importing module")
            continue

        names = [n for n in dir(mod) if n.startswith("test_")]
        for name in names:
            fn = getattr(mod, name)
            if not callable(fn):
                continue
            try:
                fn()
            except AssertionError as exc:
                failed += 1
                failures.append((f"{rel}::{name}",
                                 traceback.format_exc()))
                print(f"  FAIL {name}: {exc or '(assertion)'}")
            except Exception:
                failed += 1
                failures.append((f"{rel}::{name}", traceback.format_exc()))
                print(f"  ERROR {name}")
            else:
                passed += 1
                if args.verbose:
                    print(f"  ok   {name}")

    elapsed = time.time() - started
    print("\n" + "=" * 60)
    print(f"{passed} passed, {failed} failed in {elapsed:.2f}s")

    if failures:
        print()
        for name, tb in failures:
            print(f"--- {name}")
            print(tb)

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())