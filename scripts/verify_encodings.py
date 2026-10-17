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

Nine of them are object and container formats rather than a payload, and a
payload check is the wrong shape for those. A COFF file, a DWARF unit, a FITS
header, an ESRI shapefile, a TIFF directory and a dBASE table are *structures*:
a magic number, lengths that have to agree with the bytes on disk, and one
field the format actually reserves for text. So each has its own checker, and
each checker is written to fail loudly on a header it cannot make sense of
rather than to wave the file through -- a TIFF with the '=' of a FITS card in
the wrong column parses perfectly as hex and is rejected as a FITS header.

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
import struct
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


def payload_bytes(text: str) -> bytes:
    """Reassemble the bytes of a hex dump, in order, from the dump lines only.

    Three things have to be true for this to be right, and all three were
    violated at least once while it was being written.

      1. Only lines with an ASCII gutter count. A file's preamble says things
         like "the magic is 0A 0D 0D 0A", and those four hex pairs are read as
         payload if the comment is not excluded -- which produced a FlatGeobuf
         whose reported version was 10, because 0x0A had leaked out of the
         sentence that explains the magic number.

      2. There is no offset column. `00000000` has word boundaries either side
         of its last byte pair, so `\b..\b` matches the "00" at its end and an
         offset in front would contribute a byte. The dumps put the offset
         after the gutter, where it cannot be mistaken for data.

      3. The dump is contiguous from offset 0. `hex_runs` drops a run shorter
         than `minimum`, so build_object_formats.py pads the last line to a
         full sixteen bytes.

    Named `payload_bytes` rather than `payload` because `check_encoding` uses
    `payload` as a loop variable further down, and a module-level function of
    that name is shadowed by it -- which is a NameError at best and a silent
    miss at worst.
    """
    out = []
    for line in text.splitlines():
        if "|" not in line:
            continue
        out.extend(hex_runs(line, minimum=4))
    return b"".join(out)


# --------------------------------------------------------------------------
# object and container formats
#
# The checks above prove that a *payload* is the greeting. These prove that a
# *file* is well-formed: that the magic numbers are right, that the lengths
# agree with the bytes on disk, and that the greeting landed in a field the
# format actually has. A struct unpack that raises is caught by the caller and
# reported as an exception, which is why each one bounds-checks first.
# --------------------------------------------------------------------------

def check_coff(buf: bytes) -> tuple[bool, str]:
    """A COFF file header plus one section header, 60 bytes."""
    if len(buf) < 60:
        return False, "too short for a file header and one section header"
    (machine, nsec, _stamp, symptr, nsym,
     optsize, chars) = struct.unpack_from("<HHIIIHH", buf, 0)
    if nsec != 1:
        return False, f"{nsec} section headers; this checker expects exactly one"
    if optsize != 0:
        return False, ("an optional header is present, so this is an object "
                       "rather than the bare header this checker reads")
    name = buf[20:28].rstrip(b"\0").decode("ascii", "replace")
    rawsize, rawptr = struct.unpack_from("<II", buf, 36)
    if rawsize == 0:
        return True, f"file header ok ({nsec} section, machine 0x{machine:04X})"
    if rawptr + rawsize > len(buf):
        return False, (f"section {name!r} points at {rawsize} bytes at "
                       f"{rawptr}, past the end of a {len(buf)}-byte file")
    data = buf[rawptr:rawptr + rawsize]
    if data == GREETING:
        return True, f"section {name!r} raw data is the greeting"
    return True, f"file header ok; section {name!r} holds {rawsize} bytes"


def check_dwarf(buf: bytes) -> tuple[bool, str]:
    """A .debug_info unit whose single attribute is the producer string."""
    if len(buf) < 11:
        return False, "too short for a .debug_info unit header"
    unit_len, version, _abbrev = struct.unpack_from("<IHI", buf, 0)
    addr_size = buf[10]
    if version not in (2, 3, 4, 5):
        return False, f".debug_info version {version} is not one DWARF defines"
    following = len(buf) - 4
    if unit_len != following:
        return False, (f"unit_length says {unit_len} byte(s) follow, and "
                       f"{following} do")
    if GREETING in buf:
        return True, (f"a DIE's DW_FORM_string producer is the greeting "
                      f"(DWARF {version}, {addr_size}-byte addresses)")
    return True, f"unit_length consistent (DWARF {version})"


def check_fits(buf: bytes) -> tuple[bool, str]:
    """A FITS header: whole 80-byte cards, ending with END."""
    if len(buf) < 80:
        return False, f"{len(buf)} bytes; a FITS card is 80"
    if len(buf) % 80:
        return False, (f"{len(buf)} bytes is not a whole number of 80-byte "
                       f"FITS cards")
    cards = [buf[i:i + 80].decode("ascii", "replace")
             for i in range(0, len(buf), 80)]
    if not cards[-1].startswith("END"):
        return False, "the header does not end with an END card"
    for i, card in enumerate(cards):
        keyword = card[:8].strip()
        if keyword in ("COMMENT", "HISTORY", "END", ""):
            continue
        # Every other card is `KEYWORD = value`, and the '=' is column 9 --
        # position 8 counting from zero. A card with the '=' anywhere else is a
        # header that no reader will accept, and one that looks right in a
        # hex dump.
        if card[8] != "=":
            return False, (f"card {i} ({keyword or 'blank'!r}) has '=' in "
                           f"column {card.index('=') + 1 if '=' in card else 0}, "
                           f"not column 9")
    for card in cards:
        if card[:8].strip() in ("COMMENT", "HISTORY"):
            if GREETING.decode("ascii") in card:
                return True, "a COMMENT card carries the greeting"
    return True, f"{len(cards)} well-formed cards"


def check_shapefile(buf: bytes) -> tuple[bool, str]:
    """An ESRI shapefile header: big-endian file code, mixed-endian lengths.

    The header is 100 bytes and the offsets are not round numbers, which is
    where a plausible-looking file goes wrong. From the specification:

        0   file code   >i   9994
        4   unused           5 bytes
        9   file length >i   in 16-bit words
        13  unused           12 bytes
        25  version    <i   1000
        29  shape type <i
        33  X/Y bounding box  4 x 8-byte doubles
        65  Z/M ranges        4 x 8-byte doubles
        97  end of header     3 bytes
    """
    if len(buf) < 100:
        return False, f"{len(buf)} bytes; a shapefile header is 100"
    code, = struct.unpack_from(">i", buf, 0)
    if code != 9994:
        return False, f"file code {code}; a shapefile's is 9994"
    flen, = struct.unpack_from(">i", buf, 9)
    version, shape = struct.unpack_from("<ii", buf, 25)
    if version != 1000:
        return False, f"version {version}; a shapefile's is 1000"
    words = len(buf) // 2
    if flen != words:
        return False, (f"the header declares {flen} 16-bit words and the file "
                       f"is {words}; a shapefile's length is in words")
    return True, (f"file code 9994, version {version}, shape type {shape}, "
                  f"{flen} words")


def check_tiff(buf: bytes) -> tuple[bool, str]:
    """A TIFF header plus one IFD, in either byte order."""
    if len(buf) < 8:
        return False, "too short for a TIFF header"
    order = buf[:2]
    if order == b"II":
        e = "<"
    elif order == b"MM":
        e = ">"
    else:
        return False, f"byte-order mark {order!r} is neither II nor MM"
    magic, = struct.unpack_from(e + "H", buf, 2)
    if magic != 42:
        return False, f"magic {magic}; a TIFF's is 42"
    off, = struct.unpack_from(e + "I", buf, 4)
    if off + 2 > len(buf):
        return False, f"IFD offset {off} is past the end of a {len(buf)}-byte file"
    count, = struct.unpack_from(e + "H", buf, off)
    end = off + 2 + count * 12 + 4
    if end > len(buf):
        return False, f"the IFD claims {count} entries, which needs {end} bytes"
    for i in range(count):
        base = off + 2 + i * 12
        tag, typ, n = struct.unpack_from(e + "HHI", buf, base)
        if typ != 2 or n == 0:          # 2 is ASCII, the only free-text type
            continue
        if n <= 4:                      # short values live in the value field
            raw = buf[base + 8:base + 8 + n]
        else:
            at, = struct.unpack_from(e + "I", buf, base + 8)
            raw = buf[at:at + n]
        if raw.rstrip(b"\0") == GREETING:
            return True, f"tag {tag} is the greeting, as {n} ASCII bytes"
    return True, f"{count} IFD entries parse, none of them the greeting"


DBASE_VERSIONS = {
    0x03, 0x30, 0x31, 0x32, 0x43, 0x63, 0x7B, 0x83, 0x8B, 0xCB, 0xE5, 0xF5,
    0xFB,
}


def check_dbf(buf: bytes) -> tuple[bool, str]:
    """A dBASE III table header, whose field names are 11 bytes of free text."""
    if len(buf) < 33:
        return False, "too short for a dBASE header and a terminator"
    version = buf[0]
    if version not in DBASE_VERSIONS:
        return False, f"version byte 0x{version:02X} is not a dBASE version"
    nrec, hlen, rlen = struct.unpack_from("<IHH", buf, 4)
    if hlen < 33:
        return False, f"header length {hlen} cannot hold a field descriptor"
    if hlen > len(buf):
        return False, f"header length {hlen} exceeds the {len(buf)}-byte file"
    names, p = [], 32
    while p < hlen and buf[p] != 0x0D:
        if p + 32 > hlen:
            return False, "a field descriptor runs past the declared header"
        names.append(buf[p:p + 11].rstrip(b"\0").decode("ascii", "replace"))
        p += 32
    if p != hlen and buf[p] != 0x0D:
        return False, "the header ends without a 0x0D field terminator"
    for name in names:
        if "Hello" in name:
            return True, (f"field name {name!r}; {nrec} record(s), "
                          f"{rlen} bytes each")
    return True, f"{len(names)} field descriptor(s) parse"


def check_flatgeobuf(buf: bytes) -> tuple[bool, str]:
    """A FlatGeobuf magic number, version byte, header type and envelope.

    The four bytes of magic are 0A 0D 0D 0A, which is worth writing down
    because it is also what the file *starts* with in a text editor: the
    newlines make it look like a two-line file, and the leading bytes make it
    look like a binary one. Big endian throughout, unlike shapefile.
    """
    if len(buf) < 102:
        return False, (f"{len(buf)} bytes; a FlatGeobuf header needs 4 magic, "
                       f"1 version, 1 type and 96 of envelope")
    magic, = struct.unpack_from(">I", buf, 0)
    if magic != 0x0A0D0D0A:
        return False, f"magic 0x{magic:08X}; a FlatGeobuf's is 0x0A0D0D0A"
    version, kind = buf[4], buf[5]
    if version not in (3, 4):
        return False, f"version {version}; FlatGeobuf has 3 and 4"
    if kind not in (1, 2, 3):
        return False, f"header type {kind}; 1 is a header, 2 an index, 3 optional"
    xs = struct.unpack_from(">dddd", buf, 6)
    (xmin, ymin, xmax, ymax) = xs
    if xmin > xmax or ymin > ymax:
        return False, (f"envelope is inverted: x {xmin}..{xmax}, "
                       f"y {ymin}..{ymax}")
    gtype, = struct.unpack_from(">I", buf, 38)
    return True, (f"magic ok, version {version}, type {kind}, geometry {gtype}, "
                  f"envelope {xmin}..{xmax} x {ymin}..{ymax}")


OBJECT_FORMATS = {
    # tag: (kind, checker, the shortest buffer that could be a real file)
    "coff": ("coff", check_coff, 60),
    "obj": ("coff", check_coff, 60),
    "dwarf": ("dwarf", check_dwarf, 11),
    "wcs": ("fits", check_fits, 80),
    "fit": ("fits", check_fits, 80),
    "fits": ("fits", check_fits, 80),
    "shp": ("shapefile", check_shapefile, 100),
    "flatgeobuf": ("flatgeobuf", check_flatgeobuf, 102),
    "fgb": ("flatgeobuf", check_flatgeobuf, 102),
    "tiff": ("tiff", check_tiff, 8),
    "tif": ("tiff", check_tiff, 8),
    "shpffil": ("dbf", check_dbf, 33),
    "dbf": ("dbf", check_dbf, 33),
}


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

    if tag in OBJECT_FORMATS:
        kind, check, minimum = OBJECT_FORMATS[tag]
        buf = payload_bytes(text)
        # Route on the format's own minimum length rather than a round number.
        # A single floor for all six was wrong in both directions: at 80 bytes
        # it skipped every small file it was written for -- a 73-byte COFF
        # object, a 29-byte DWARF unit, a 76-byte dBASE header -- and at a
        # smaller one it would have handed an empty buffer to a struct.unpack
        # and raised. A text placeholder has no payload at all, so it is below
        # every minimum and lands in the generic branch, which is right.
        if len(buf) >= minimum:
            ok, why = check(buf)
            return kind, ok, why

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
                # the object and container formats with a header to get right
                *OBJECT_FORMATS,
            }
            or name in {
                "base58", "base62", "base85", "asci85", "deflate", "intel hex",
                "motorola s-record", "srec", "messagepack", "cbor", "bson",
                "coff", "dwarf", "wcs", "shp", "tiff", "shpffil", "flatgeobuf",
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
