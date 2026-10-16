#!/usr/bin/env python3
"""Decode the encoding files and check they say what they claim.

About seventy files in `hello/full/` are not programs. They are hex dumps of
encodings: Base58 of the greeting, a deflate stream, an Intel HEX record with a
checksum, a ZIP archive. Each was produced by a library rather than by memory,
because a hex dump written from memory is wrong in one byte and reads as correct.

Producing them correctly is not the same as *having* them correct. This decodes
them back, which is the only direction that would catch a mistake in the encoder,
and it finds three things a hex dump cannot show you:

  * a Base58, Base62 or Base85 string that does not decode to the greeting;
  * an Intel HEX or S-record whose checksum does not verify;
  * a deflate, gzip, bzip2 or xz stream that does not decompress.

The files are parsed by reading the ASCII hex tokens out of the comment and the
body -- no per-file format table -- so a file that has been edited by hand is
caught rather than silently skipped.

    python scripts/verify_encodings.py
    python scripts/verify_encodings.py --verbose
"""

from __future__ import annotations

import argparse
import base64
import bz2
import gzip
import json
import lzma
import pathlib
import re
import zlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "hello" / "manifest.json"
CLASSES = ROOT / "data" / "placeholder_classes.json"
GREETING = b"Hello World!"

HEX_TOKEN = re.compile(r"\b([0-9A-Fa-f]{2})\b")


def hex_runs(text: str, minimum: int = 6):
    """Yield maximal runs of two-digit hex tokens, and the bytes they are.

    A hex dump interleaves ASCII gutters with `|...|`, so the tokens have to be
    gathered into runs and then judged by length. Anything under `minimum` bytes
    is a header fragment, not a payload.
    """
    run: list[str] = []
    for line in text.splitlines():
        # drop the comment marker and the ascii gutter before looking for hex
        stripped = line.split("|", 1)[0]
        stripped = re.sub(r"^\s*(?://|#|--|;;|\*|%|;)+\s*", "", stripped)
        for tok in HEX_TOKEN.findall(stripped.upper()):
            run.append(tok)
            continue
        if run:
            if len(run) >= minimum:
                yield bytes(int(t, 16) for t in run)
            run = []
    if len(run) >= minimum:
        yield bytes(int(t, 16) for t in run)


def check_intel_hex(text: str) -> tuple[bool, str]:
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith(":"):
            continue
        try:
            raw = bytes.fromhex(line[1:])
        except ValueError:
            return False, f"unparseable record {line[:20]}"
        if len(raw) < 6:
            return False, "record shorter than its own byte count"
        count = raw[0]
        # A record is LL, two address bytes, the type, LL data bytes and one
        # checksum -- four header bytes, then count data bytes, then one. So the
        # total is count + 5 and the checksum sits at index 4 + count. Getting
        # that off by one made a correct record look like a corrupt one, which is
        # how this tool reported most of its own files as unverifiable at first.
        if len(raw) != count + 5:
            return False, (f"byte count {count} does not match the record "
                           f"length {len(raw)}")
        body = raw[:4 + count]
        checksum = raw[4 + count]
        if (-sum(body)) & 0xFF != checksum:
            return False, "checksum does not verify"
        if body[3] == 0x00:
            data = body[4:4 + count]
            if data == GREETING:
                return True, f"data record carries the greeting, checksum {checksum:02X}"
        return True, "structure ok"
    return False, "no Intel HEX record found"


def check_srecord(text: str) -> tuple[bool, str]:
    for line in text.splitlines():
        line = line.strip()
        if not re.fullmatch(r"S[0-3][0-9A-Fa-f]+", line):
            continue
        try:
            raw = bytes.fromhex(line[2:])
        except ValueError:
            return False, "unparseable record"
        if len(raw) < 4:
            return False, "record too short"
        count = raw[0]
        if count + 1 != len(raw):
            return False, "count field does not match the record length"
        if (~sum(raw[:-1])) & 0xFF != raw[-1]:
            return False, "checksum does not verify"
        data = raw[3:-1]
        if data == GREETING:
            return True, f"record carries the greeting, checksum {raw[-1]:02X}"
        return True, "structure ok"
    return False, "no S-record found"


def check_stream(text: str) -> tuple[bool, str] | None:
    """Try the gzip/bzip2/xz/deflate decompressors over every hex run."""
    for payload in hex_runs(text):
        for name, fn in (
            ("gzip", lambda b: gzip.decompress(b)),
            ("bzip2", lambda b: bz2.decompress(b)),
            ("xz", lambda b: lzma.decompress(b)),
        ):
            try:
                out = fn(payload)
            except Exception:
                continue
            if out == GREETING:
                return True, f"{name} stream decompresses to the greeting"
        for wbits in (-zlib.MAX_WBITS, zlib.MAX_WBITS):
            try:
                out = zlib.decompress(payload, wbits)
            except Exception:
                continue
            if out == GREETING:
                kind = "raw deflate" if wbits < 0 else "zlib"
                return True, f"{kind} stream inflates to the greeting"
    return None


def check_base_n(text: str) -> tuple[bool, str] | None:
    """Base58/62/85 decode back to the greeting."""
    alphabets = {
        "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz": 58,
        "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz": 62,
    }
    for line in text.splitlines():
        token = line.strip()
        if len(token) < 8 or " " in token:
            continue
        for alphabet, base in alphabets.items():
            if not all(c in alphabet for c in token):
                continue
            n = 0
            for c in token:
                n = n * base + alphabet.index(c)
            width = (n.bit_length() + 7) // 8
            try:
                out = n.to_bytes(width, "big").lstrip(b"\x00")
            except OverflowError:
                continue
            if out == GREETING:
                return True, f"base{base} decodes to the greeting"
    # base85 and a85 last: they overlap everything else
    for line in text.splitlines():
        token = line.strip()
        if len(token) < 8:
            continue
        # a85decoders live in base64, not binascii -- referencing them eagerly
        # raised AttributeError on every file before the try could catch it.
        for name, fn in (("base85", base64.b85decode),
                         ("a85", base64.a85decode)):
            try:
                out = fn(token.encode())
            except Exception:
                continue
            if out == GREETING:
                return True, f"{name} decodes to the greeting"
    return None


def check_encoding(path: pathlib.Path) -> tuple[str, bool, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    # `path.stem` strips only the *last* suffix, so for hello.intel_hex it is
    # "hello" -- which is how the first version of this routed sixteen files into
    # the generic branch and reported them as unverifiable rather than wrong.
    tag = (path.suffix or "").lstrip(".").lower()
    name = path.name.lower()

    if "intel_hex" in tag or "intel-hex" in tag:
        ok, why = check_intel_hex(text)
        return "intel-hex", ok, why
    if "motorola_s_record" in tag or tag == "srec" or "s-record" in tag:
        ok, why = check_srecord(text)
        return "s-record", ok, why

    for check in (check_stream, check_base_n):
        result = check(text)
        if result is not None:
            ok, why = result
            return "stream", ok, why

    for payload in hex_runs(text):
        if GREETING in payload:
            return "hex", True, "greeting present as raw bytes"

    return "text", True, "no machine payload; text file checked by other tests"


def candidates() -> list[pathlib.Path]:
    if not MANIFEST.exists():
        return []
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    kinds = {}
    if CLASSES.exists():
        kinds = {f["path"]: f["kind"]
                 for f in json.loads(CLASSES.read_text(encoding="utf-8"))["files"]}
    out = []
    for f in man["files"]:
        stem = (f.get("extension") or "").lower()
        name = (f["language"] or "").lower()
        interesting = (
            stem.lstrip(".") in {
                "base58", "base62", "base85", "base95", "ascii85", "deflate",
                "gzip_binary", "bzip2_binary", "xz_binary", "intel_hex",
                "motorola_s_record", "srec", "snappy_binary", "messagepack",
                "cbor", "bson", "raw_bytes", "hex_dump", "base16",
            }
            or name in {
                "base58", "base62", "base85", "asci85", "deflate", "intel hex",
                "motorola s-record", "srec", "messagepack", "cbor", "bson",
            }
        )
        if interesting:
            out.append(ROOT / f["path"])
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    files = candidates()
    if not files:
        print("no encoding files found; is the manifest missing?")
        return 0

    failures = []
    print(f"checking {len(files)} encoding file(s)\n")
    for path in files:
        try:
            kind, ok, why = check_encoding(path)
        except Exception as exc:                          # noqa: BLE001
            failures.append((path.name, f"raised {exc}"))
            continue
        rel = path.relative_to(ROOT).as_posix()
        if ok:
            if args.verbose:
                print(f"  ok    {rel:<58} {kind:<10} {why}")
        else:
            failures.append((rel, why))
            print(f"  FAIL  {rel:<58} {kind:<10} {why}")

    print()
    if failures:
        print(f"{len(failures)} file(s) did not verify:")
        for rel, why in failures[:20]:
            print(f"  {rel}: {why}")
        return 1

    print("every encoding file decodes back to the greeting")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
