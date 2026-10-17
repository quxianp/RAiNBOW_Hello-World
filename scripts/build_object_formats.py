#!/usr/bin/env python3
"""Build the object-format files from their own field definitions.

Six of this repository's entries are binary formats whose *only* free text is
somewhere inside a header: a COFF section's raw data, a DWARF DIE's producer
string, a FITS COMMENT card, a TIFF ASCII tag, a dBASE field name. A shapefile
has nowhere at all, and gets the honest treatment instead.

None of them can be written by hand. Not "hard to write by hand" -- a header is
a dozen fields in a specified order, and transcribing one produces a file that
is wrong in exactly one byte, which looks identical to a correct one in every
diff and every screenshot. So each is built here from the specification's own
field widths, and the output is a hex dump with an ASCII gutter rather than
binary, because a file in this repository has to stay reviewable.

Three of the six put the greeting in a field the format actually reserves for
text, and one (the shapefile) cannot. The distinction is the point of the
exercise, so `--check` re-derives every buffer from scratch and compares it
byte for byte against the template already in the generator: a file that was
hand-edited afterwards is a diff, not a silent change.

    python scripts/build_object_formats.py --emit .tmp/object_batch.json
    python scripts/build_object_formats.py --check
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
GEN = ROOT / "scripts" / "generate_all_hello.py"

GREETING = b"Hello World!"


# --------------------------------------------------------------------------
# hex dump rendering
# --------------------------------------------------------------------------

def hexdump(buf: bytes, comment: str = "//") -> str:
    """Sixteen bytes a line, with an ASCII gutter and the offset outboard.

    The offset goes *after* the gutter on purpose. `verify_encodings.py`
    gathers hex tokens with ``\\b..\\b``, and `00000000` has word boundaries
    either side of its last byte pair -- so an offset column in front would
    contribute a stray ``00`` to the payload and every structural check would
    read a file one byte longer than it is.
    """
    out = []
    for off in range(0, len(buf), 16):
        chunk = buf[off:off + 16]
        tokens = " ".join(f"{b:02X}" for b in chunk)
        gutter = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        out.append(f"{comment} {tokens:<47} |{gutter}|   <- {off:04X}")
    return "\n".join(out)


# --------------------------------------------------------------------------
# the formats
# --------------------------------------------------------------------------

def build_coff() -> bytes:
    """A COFF object: 20-byte file header, one 40-byte section header, data.

    Field widths are from the Microsoft PE/COFF specification. `SizeOfRawData`
    and `PointerToRawData` are written to be consistent with the buffer that
    follows them, which is the part a hand-written header gets wrong: a
    section whose declared size and pointer do not agree with the file is a
    link error in every linker and reads perfectly in a hex dump.
    """
    header = struct.pack(
        "<HHIIIHH",
        0x014C,                      # Machine: IMAGE_FILE_MACHINE_I386
        1,                           # NumberOfSections
        0,                           # TimeDateStamp: no clock in a build file
        0,                           # PointerToSymbolTable: none
        0,                           # NumberOfSymbols
        0,                           # SizeOfOptionalHeader: this is an object
        0x0102,                      # EXECUTABLE_IMAGE | 32BIT_MACHINE
    )
    section = (
        b".text\x00\x00\x00"
        + struct.pack("<IIIIIIHHI",
                     len(GREETING),  # VirtualSize
                     0,               # VirtualAddress
                     len(GREETING),  # SizeOfRawData
                     60,              # PointerToRawData: 20 + 40
                     0, 0,            # relocations, line numbers
                     0, 0,
                     0x60500020)      # CODE | EXECUTE | READ | IMAGE
    )
    return header + section + GREETING


def build_dwarf() -> bytes:
    """A DWARF 4 `.debug_info` unit whose one attribute is the producer.

    `unit_length` counts everything after itself, which is the field that
    decides whether a reader trusts the rest of the unit.
    """
    abbrev = b"\x01\x11\x00\x25\x08\x00\x00"   # one abbrev: compile_unit, string
    del abbrev                                # referenced by offset 0, not inlined
    tail = struct.pack("<HI", 4, 0) + b"\x08" + GREETING + b"\x00"
    return struct.pack("<I", len(tail)) + tail


def _card(text: str) -> bytes:
    """One FITS header card, blank-padded to its mandatory 80 bytes."""
    raw = text.encode("ascii")
    if len(raw) > 80:
        raise ValueError(f"FITS card is {len(raw)} bytes: {text!r}")
    return raw.ljust(80)


def build_wcs() -> bytes:
    """A FITS header describing a world coordinate system.

    Every card is exactly 80 bytes, the value is right-justified to end in
    column 30, and the header ends with END. The greeting goes in a COMMENT
    card, which is the one card kind with no '=' in it at all.
    """
    return b"".join([
        _card("SIMPLE  =                    T"),
        _card("BITPIX  =                    8"),
        _card("NAXIS   =                    2"),
        _card("WCSAXES =                    2"),
        _card("CTYPE1  = 'RA---TAN'"),
        _card("CTYPE2  = 'DEC--TAN'"),
        _card("COMMENT   Hello World!"),
        _card("END"),
    ])


def build_shapefile() -> bytes:
    """An ESRI shapefile holding one Null Shape.

    There is nowhere in this format to put a greeting: the 5 unused header
    bytes are specified as zero, the bbox holds four doubles, and a Null Shape
    record is four bytes of shape type. So the file is a real header and the
    comment says where a greeting would go if the format allowed one.
    """
    body = struct.pack("<ii", 0, 0)
    head = struct.pack(">i", 9994) + b"\x00" * 5
    head += struct.pack(">i", (100 + len(body)) // 2) + b"\x00" * 12
    head += struct.pack("<ii", 1000, 0)
    head += struct.pack("<dddd", 0.0, 0.0, 0.0, 0.0)
    head += b"\x00" * 32
    head += b"\x00" * 3
    assert len(head) == 100, len(head)
    return head + body


def build_tiff() -> bytes:
    """A little-endian TIFF whose ImageDescription is the greeting.

    Tag 270 with type 2 (ASCII) is the field the specification defines for
    human-readable text, so this is the one of the six that puts the greeting
    somewhere a reader will actually show it.
    """
    text = GREETING + b"\x00"
    ifd_off = 8
    str_off = ifd_off + 2 + 12 + 4
    head = b"II" + struct.pack("<H", 42) + struct.pack("<I", ifd_off)
    ifd = struct.pack("<H", 1)
    ifd += struct.pack("<HHII", 270, 2, len(text), str_off)
    ifd += struct.pack("<I", 0)
    return head + ifd + text


def build_dbf() -> bytes:
    """A dBASE III table with one character field called HelloWorld.

    Field names are eleven bytes and that is the whole free-text budget the
    format offers. Ten characters of it fit, so this is the closest a dBASE
    file gets to greeting you.
    """
    nfields, rec_len = 1, 11
    hlen = 32 + nfields * 32 + 1
    head = bytearray(hlen)
    head[0] = 0x03                     # dBASE III without a memo file
    head[1:4] = bytes((126, 1, 1))     # YY MM DD, last update
    struct.pack_into("<I", head, 4, 0)             # records: none
    struct.pack_into("<H", head, 8, hlen)
    struct.pack_into("<H", head, 10, rec_len + 1)   # record length, incl. the 0x20
    head[32:42] = b"HelloWorld"        # field name, 11 bytes, NUL-padded
    head[43] = ord("C")                # type: character
    struct.pack_into("<H", head, 48, 11)            # field length
    head[hlen - 1] = 0x0D              # end of the field descriptors
    return bytes(head) + b" " * rec_len


BUILDERS = {
    "coff": ("COFF", build_coff),
    "dwarf": ("DWARF", build_dwarf),
    "wcs": ("WCS", build_wcs),
    "shp": ("SHP", build_shapefile),
    "tiff": ("TIFF", build_tiff),
    "shpffil": ("SHPFFIL", build_dbf),
}


# --------------------------------------------------------------------------
# the comment that goes above each dump
# --------------------------------------------------------------------------

def preamble(key: str, buf: bytes) -> str:
    n = len(buf)
    common = (
        f"// {key}: {n} bytes, dumped sixteen at a time.\n"
        "//\n"
        "// The bytes below are not hand-written. They are built from the\n"
        "// format's own field widths by scripts/build_object_formats.py, and\n"
        "// scripts/verify_encodings.py reads the fields back by name -- the\n"
        "// magic number, the lengths, the offsets. A hex dump written from\n"
        "// memory is wrong in one byte and looks exactly like a correct one.\n"
        "//\n"
    )
    return {
        "coff": (
            "// COFF: the Common Object File Format, twenty bytes of file\n"
            "// header and forty of section header before any data.\n"
            "//\n"
            "// Machine i386, one section, no optional header -- that last one is\n"
            "// what makes this an object rather than an image. The greeting\n"
            "// `Hello World!` is the section's raw data, and SizeOfRawData and\n"
            "// PointerToRawData are both thirteen and sixty for it.\n"
            "//\n"
        ),
        "dwarf": (
            "// DWARF: the debugging information format, and this is a complete\n"
            "// `.debug_info` unit -- unit_length, version 4, the abbreviation\n"
            "// offset it compiles against, an eight-byte address size, and one\n"
            "// DIE whose DW_AT_producer is a DW_FORM_string.\n"
            "//\n"
            "// The producer string is the greeting `Hello World!`, and\n"
            "// unit_length is the count of everything after itself, which is how\n"
            "// a reader knows whether to believe the rest.\n"
            "//\n"
        ),
        "wcs": (
            "// WCS: a World Coordinate System is not a file format of its own.\n"
            "// It is a set of FITS header keywords -- CTYPE1, CTYPE2, CRVAL1 --\n"
            "// and a `.wcs` file is a FITS header carrying them.\n"
            "//\n"
            "// Eight cards, eighty bytes each. Every card puts '=' in column 9\n"
            "// and its value right-justified so it ends in column 30, and the\n"
            "// header ends with END. COMMENT is the one card kind with no '=' at\n"
            "// all, which is why `Hello World!` goes in one of those.\n"
            "//\n"
        ),
        "shp": (
            "// SHP: an ESRI shapefile. The header is one hundred bytes and\n"
            "// mixes byte orders: the file code and the file length are big\n"
            "// endian, everything after them is little endian.\n"
            "//\n"
            "// There is no greeting in this file, because there is nowhere in\n"
            "// the format to put one. The five unused header bytes are\n"
            "// specified as zero, the bounding box holds four doubles, and the\n"
            "// Null Shape record that follows is four bytes of shape type. A\n"
            "// `Hello World!` in any of them would be a file no reader accepts,\n"
            "// so this one is a correct header with nothing to say.\n"
            "//\n"
            "// File code 9994, version 1000, shape type 0, and the length in\n"
            "// 16-bit words that the format -- not the byte count.\n"
            "//\n"
        ),
        "tiff": (
            "// TIFF: an image format with a real field for human-readable text.\n"
            "// Tag 270, ImageDescription, type 2, ASCII, thirteen bytes plus\n"
            "// the NUL that terminates an ASCII count.\n"
            "//\n"
            "// This is the one of these six whose greeting a reader will\n"
            "// actually display: `Hello World!` in thirteen bytes, which is\n"
            "// what `identify` prints and what a browser's image panel shows.\n"
            "// Little endian, magic 42, one IFD entry, and the next-IFD\n"
            "// pointer is zero because there is no second one.\n"
            "//\n"
        ),
        "shpffil": (
            "// SHPFFIL: the attribute table that sits beside a shapefile --\n"
            "// a .dbf, in dBASE III.\n"
            "//\n"
            "// A dBASE table has eleven bytes per field name and that is the\n"
            "// whole of its free-text budget, so `Hello World!` gets the ten\n"
            "// characters that fit. The date in bytes 2-4 is there because the\n"
            "// format requires it, and the header ends with a 0x0D.\n"
            "//\n"
        ),
    }[key] + common


# --------------------------------------------------------------------------
# emit / check
# --------------------------------------------------------------------------

def batch() -> dict[str, str]:
    out: dict[str, str] = {}
    for key, (language, build) in BUILDERS.items():
        buf = build()
        out[language] = f"{preamble(key, buf)}\n{hexdump(buf)}\n"
    return out


def generator_templates() -> dict[str, str]:
    src = GEN.read_text(encoding="utf-8")
    start = src.index("HELLO: dict[str, str] = {")
    end = src.index("\n}\n", start)
    out: dict[str, str] = {}
    for line in src[start:end].splitlines():
        m = re.match(r'\s{4}"((?:[^"\\]|\\.)*)"\s*:\s*(.*),\s*$', line)
        if m:
            try:
                out[m.group(1)] = json.loads(m.group(2))
            except ValueError:
                pass
    return out


def check() -> list[str]:
    have = generator_templates()
    problems = []
    for language, want in batch().items():
        got = have.get(language.lower())
        if got is None:
            problems.append(f"{language}: no template in the generator")
        elif got != want:
            problems.append(f"{language}: differs from the bytes the "
                            f"specification builds ({len(got)} vs {len(want)} "
                            f"characters)")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--emit", metavar="PATH",
                    help="write the batch JSON for add_templates.py")
    ap.add_argument("--check", action="store_true",
                    help="compare the generator's templates with the built bytes")
    args = ap.parse_args()

    if args.emit:
        payload = batch()
        pathlib.Path(args.emit).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8", newline="\n")
        print(f"wrote {len(payload)} object-format template(s) to {args.emit}")
        for language, text in sorted(payload.items()):
            print(f"  {language:<10} {len(text):>5} characters")
        return 0

    if args.check:
        problems = check()
        if problems:
            print(f"{len(problems)} object-format file(s) are not what the "
                  f"specifications build:")
            for p in problems:
                print(f"  {p}")
            return 1
        print("every object-format file matches the bytes its format defines")
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())