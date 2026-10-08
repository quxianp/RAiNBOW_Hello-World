#!/usr/bin/env python3
"""Balance the byte share of every core language so the GitHub language bar
becomes an even rainbow.

GitHub Linguist paints each segment with width proportional to that language's
share of the *counted* bytes.  `.gitattributes` makes hello/core/ the only
counted path, so the only thing that matters there is: how many bytes does each
language own?  For an even rainbow every language must own exactly 1/N of the
counted total.

This script
  1. measures the natural size of every hello/core file,
  2. picks a target size (default: mean, rounded to a tidy number),
  3. rewrites each file with a per-language comment pad so that
     len(file) == target (within +/- PAD_TOLERANCE),
  4. writes logs/balance_report.txt with bytes, share and deviation per
     language, plus a simulated bar.

Comment syntax comes from the same table the generator uses, and any language
without comments is padded with whitespace / blank lines instead.

Usage: python3 scripts/balance_bytes.py [--target-bytes N] [--report]
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from generate_all_hello import (
        BLOCK_COMMENT,
        COMMENT,
        FILENAME_COMMENT,
        comment_style,
        comment_style_for,
    )
except Exception as exc:  # pragma: no cover
    print(f"! cannot import generator tables: {exc}", file=sys.stderr)
    raise

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "hello" / "core"
CONFIG = ROOT / "config"
LOGS = ROOT / "logs"
LOGS.mkdir(parents=True, exist_ok=True)

DEFAULT_TARGET = 2048
PAD_TOLERANCE = 0
MARKER = "rainbow-pad"
MIN_SHARE = 0.05
MAX_SHARE = 0.5


LINE_TOKENS = ("<!--", "/*", "(*", "//", "--", ";", "#", '"', "!", "%")
BLOCK_CLOSE = {"<!--": "-->", "/*": "*/", "(*": "*)"}


def style_from_content(text: str, ext: str, fname: str | None) -> tuple:
    """Detect the comment style from the file's own line-1 modeline.

    The generator pins every core file with a modeline in that language's
    comment dialect, so the pad must follow line 1 instead of re-guessing
    from the extension (whose table cannot be right for all 694 languages).
    """
    first = text.splitlines()[0] if text else ""
    for tok in LINE_TOKENS:
        if first.startswith(tok):
            if tok in BLOCK_CLOSE:
                return (None, tok, BLOCK_CLOSE[tok])
            return (tok, None, None)
    return comment_style_for(ext, fname)


def pad_lines(ext: str, name: str, colour: str | None, needed: int,
             fname: str | None = None, style: tuple | None = None) -> list[str]:
    """Build comment lines whose total encoded length is exactly `needed`."""
    line, bs, be = style if style is not None else comment_style_for(ext, fname)
    filler_bits = [
        "equal byte share keeps the language bar an even rainbow",
        "one segment per Linguist coloured language",
        f"{name} :: RAiNBOW_Hello-World",
        f"colour {colour or 'unassigned'} :: padded to {100.0 / 1:.0f}",
        "padding comment: byte balancing for the rainbow bar",
        "https://github.com/quxianp/RAiNBOW_Hello-World",
    ]
    out: list[str] = []
    i = 0

    def blen(s: str) -> int:
        # byte length: file size is counted in bytes, `len()` is characters
        return len(s.encode("utf-8"))

    # each iteration consumes as much as it can of the remaining budget
    while needed > 0:
        if line:
            prefix = f"{line} {MARKER} "
            tail = filler_bits[i % len(filler_bits)]
            i += 1
            room = needed - blen(prefix) - 1  # -1 for the newline
            if room < 0:
                # cannot fit even a short comment: use a bare marker line
                bare = f"{line} {MARKER}"
                if needed >= blen(bare) + 1:
                    out.append(bare + "\n")
                    needed -= blen(bare) + 1
                    continue
                out.append(" " * (needed - 1) + "\n")
                needed = 0
                break
            if room < 8:
                marker_line = f"{line} {MARKER}"
                out.append(marker_line + " " * (needed - blen(marker_line) - 1) + "\n")
                needed = 0
                break
            out.append(prefix + tail[:room] + "\n")
            needed -= blen(out[-1])
        elif bs:
            # block comments: keep every pad line self-contained
            # `f"{prefix}{filler} {be}\n"` -> prefix + room + space + be + nl
            prefix = f"{bs} {MARKER} "
            room = needed - blen(prefix) - blen(be) - 2
            if room < 0:
                # too small for filler: exact-length pad that still carries
                # the marker (so stripped_natural() recognises it as our pad)
                marked = f"{bs} {MARKER} {be}"
                if needed >= blen(marked) + 1:
                    out.append(marked + " " * (needed - blen(marked) - 1) + "\n")
                else:
                    out.append(" " * (needed - 1) + "\n")
                needed = 0
                break
            out.append(prefix + filler_bits[i % len(filler_bits)][:room] + f" {be}\n")
            i += 1
            needed -= blen(out[-1])
        else:
            # no comment syntax at all: whitespace padding keeps the file legal
            out.append("\n")
            needed -= 1
    return out


def build_pad(ext: str, name: str, colour: str | None, needed: int,
              fname: str | None = None, style: tuple | None = None) -> str:
    return "".join(pad_lines(ext, name, colour, needed, fname, style=style))


def stripped_natural(path: Path) -> int:
    """Size of the file without the pad lines this script appends.

    Measuring the padded file would make `target` ratchet upwards on every
    run (2048 -> 2049 -> 2050 ...), because an already-balanced file looks
    like a "natural" file that is too big.
    """
    text = path.read_bytes().decode("utf-8", "replace")
    lines = text.splitlines(keepends=True)
    keep_end = len(lines)
    while keep_end > 0:
        ln = lines[keep_end - 1]
        if MARKER in ln or ln.strip() == "":
            keep_end -= 1
        else:
            break
    return len("".join(lines[:keep_end]).encode("utf-8"))


def natural_sizes(rainbow: dict) -> list[dict]:
    rows = []
    for rec in rainbow["languages"]:
        path = ROOT / rec["path"]
        if not path.exists():
            continue
        size = stripped_natural(path)
        rows.append(
            {
                "language": rec["name"],
                "path": rec["path"],
                "abs": path,
                "ext": rec["extension"] or Path(rec["path"]).suffix,
                "colour": f"#{rec['color']}" if rec["color"] else None,
                "fname": Path(rec["path"]).name,
                "hue": rec.get("hue"),
                "natural": size,
            }
        )
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target-bytes", type=int, default=DEFAULT_TARGET)
    ap.add_argument("--report-only", action="store_true")
    ap.add_argument("--report", action="store_true", default=True)
    ap.add_argument(
        "--shard",
        default="",
        help="i/n: balance only this slice (CI batch mode; the shared "
        "report files are left alone)",
    )
    args = ap.parse_args()
    sharded = bool(args.shard)

    rainbow = json.loads((CONFIG / "rainbow_langs.json").read_text(encoding="utf-8", newline="\n"))
    if sharded and "/" in args.shard:
        idx_s, n_s = args.shard.split("/", 1)
        idx, n_shards = int(idx_s), int(n_s)
        langs = rainbow["languages"]
        start = (len(langs) * idx) // n_shards
        end = (len(langs) * (idx + 1)) // n_shards
        rainbow = {**rainbow, "languages": langs[start:end]}
    rows = natural_sizes(rainbow)
    if not rows:
        print("! no core files found; run scripts/generate_all_hello.py first")
        return 1

    n = len(rows)
    natural_mean = statistics.mean(r["natural"] for r in rows)
    # Never ratchet: the target is a constant unless a *stripped* natural file
    # is genuinely bigger than it (then every file pads up to that size).
    target = max(args.target_bytes, max(r["natural"] for r in rows))
    if target != args.target_bytes:
        print(f"! largest natural file forces target {target}")

    total = 0
    lines = []
    lines.append("byte balance report")
    lines.append("=" * 100)
    lines.append(f"core languages            : {n}")
    lines.append(f"natural mean size         : {natural_mean:.1f} bytes")
    lines.append(f"target size per language  : {target} bytes")
    lines.append(f"ideal share per language  : {100.0 / n:.4f} %")
    lines.append(f"allowed share window      : {MIN_SHARE} % - {MAX_SHARE} %")
    lines.append("")

    for r in rows:
        path = r["abs"]
        cur = path.stat().st_size
        if not args.report_only:
            need = target - cur
            if need != 0:
                if need > 0:
                    text = path.read_text(encoding="utf-8", newline="\n")
                    style = style_from_content(text, r["ext"], r.get("fname"))
                    pad = build_pad(r["ext"], r["language"], r["colour"], need,
                                    r.get("fname"), style=style)
                    text = text + pad
                else:
                    # shrink: drop existing padding lines, else fall back to a
                    # regenerated minimal file is not possible, so trim the
                    # reference/pad lines that this script owns.
                    text = shrink(path.read_text(encoding="utf-8", newline="\n"), r["ext"], need)
                if not text.endswith("\n"):
                    text += "\n"
                path.write_text(text, encoding="utf-8", newline="\n")
        size = path.stat().st_size
        total += size
        r["final"] = size
        r["share"] = 0.0

    shares = [r["final"] / total * 100.0 for r in rows] if total else []
    for r, s in zip(rows, shares):
        r["share"] = s
        r["deviation"] = s - 100.0 / n

    header = f"{'language':<34}{'path':<44}{'bytes':>8}{'share%':>10}{'dev%':>9}"
    lines.append(header)
    lines.append("-" * 100)
    for r in sorted(rows, key=lambda x: (x.get("hue") or 0, x["language"])):
        lines.append(
            f"{r['language'][:33]:<34}{r['path'][:43]:<44}"
            f"{r['final']:>8}{r['share']:>10.4f}{r['deviation']:>+9.4f}"
        )
    lines.append("-" * 100)
    lines.append(f"{'TOTAL':<78}{total:>8}{100.0:>10.4f}")
    lines.append("")
    if shares:
        lines.append(
            f"share min / max / stdev : {min(shares):.4f} % / "
            f"{max(shares):.4f} % / {statistics.pstdev(shares):.6f} pp"
        )
        bad = [r["language"] for r in rows if not (MIN_SHARE <= r["share"] <= MAX_SHARE)]
        lines.append(
            f"outside {MIN_SHARE}-{MAX_SHARE} % window : "
            + (", ".join(bad) if bad else "none")
        )
    lines.append("")
    lines.append("simulated GitHub language bar (one cell per core language)")
    bar = []
    for r in rows:
        bar.append(r["colour"] or "#808080")
    lines.append("  " + " ".join(bar[:64]))
    lines.append("  " + " ".join(bar[64:128]))
    for i in range(0, len(bar), 128):
        lines.append(f"  [{i:>4}-{min(i + 127, len(bar) - 1):>4}] {len(bar[i:i + 128])} segments")

    report = "\n".join(lines) + "\n"
    summary = {
        "core_languages": n,
        "target_bytes_each": target,
        "natural_mean_bytes": round(natural_mean, 2),
        "total_counted_bytes": total,
        "ideal_share_pct": round(100.0 / n, 6),
        "actual_share_min_pct": round(min(shares), 6) if shares else 0,
        "actual_share_max_pct": round(max(shares), 6) if shares else 0,
        "share_stdev_pp": round(statistics.pstdev(shares), 8) if shares else 0,
        "window_pct": [MIN_SHARE, MAX_SHARE],
        "outside_window": [
            r["language"] for r in rows if shares and not (MIN_SHARE <= r["share"] <= MAX_SHARE)
        ],
        "sum_pct": round(sum(shares), 6),
    }
    if not sharded:
        # shard mode leaves the shared reports alone: they describe the
        # whole bar, not one CI batch
        (LOGS / "balance_report.txt").write_text(report, encoding="utf-8", newline="\n")
        (LOGS / "balance_summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(f"core languages : {n}")
    print(f"target bytes   : {target} (natural mean {natural_mean:.1f})")
    print(f"total counted  : {total} bytes")
    print(f"share          : min {summary['actual_share_min_pct']}% "
          f"max {summary['actual_share_max_pct']}% "
          f"ideal {summary['ideal_share_pct']}%")
    print(f"sum of shares  : {summary['sum_pct']}%")
    print(f"outside window : {len(summary['outside_window'])}")
    if not sharded:
        print("wrote logs/balance_report.txt, logs/balance_summary.json")
    return 0


def shrink(text: str, ext: str, need: int) -> str:
    """Remove `-need` bytes from the padding this script previously appended."""
    if need >= 0:
        return text
    keep = len(text) + need  # need is negative
    if keep <= 0:
        return ""
    cut = text[:keep]
    if not cut.endswith("\n"):
        # keep a trailing newline: the write guard would re-add one and a
        # 1-byte shrink would cancel out to a no-op
        cut = text[:keep - 1] + "\n" if keep >= 2 else "\n"
    return cut


if __name__ == "__main__":
    sys.exit(main())
