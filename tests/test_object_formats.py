#!/usr/bin/env python3
"""The object-format checkers must reject a bad header, not just accept a good one.

A verifier that only proves the happy path is decoration. Each of the six
structure checkers added for the COFF, DWARF, FITS, shapefile, TIFF and dBASE
files is exercised twice: once with a buffer built from the format's own field
widths, and once with a single field corrupted -- the magic number, a length
that disagrees with the file, an offset past the end.

The reason to insist on the second case is a property these files share with
everything else in this repository's history. A wrong byte inside a hex dump is
invisible to the eye and invisible to every other check in the suite: the file
has the right size, the right modeline, and the greeting somewhere in it. The
only thing that can catch it is a checker that knows what the field means. A
checker that returns True for anything it cannot parse is not that.
"""

import importlib.util
import pathlib
import struct

ROOT = pathlib.Path(__file__).resolve().parent.parent

_spec = importlib.util.spec_from_file_location(
    "verify_encodings", ROOT / "scripts" / "verify_encodings.py")
V = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(V)

GREETING = V.GREETING


def _ready():
    return (ROOT / "hello" / "manifest.json").exists()


# --------------------------------------------------------------------------
# builders: each one fills in the format's fields from its own definition, so
# a good buffer is good by construction rather than by transcription.
# --------------------------------------------------------------------------

def coff() -> bytes:
    header = struct.pack("<HHIIIHH", 0x014C, 1, 0, 0, 0, 0, 0x0102)
    section = (b".text\x00\x00\x00"
               + struct.pack("<IIIIIIHHI",
                             len(GREETING), 0, len(GREETING), 60,
                             0, 0, 0, 0, 0x60500020))
    return header + section + GREETING


def dwarf() -> bytes:
    tail = struct.pack("<HI", 4, 0) + b"\x08" + GREETING + b"\x00"
    return struct.pack("<I", len(tail)) + tail


def fits() -> bytes:
    cards = [
        b"SIMPLE  =                    T",
        b"BITPIX  =                    8",
        b"NAXIS   =                    2",
        b"WCSAXES =                    2",
        b"COMMENT   Hello World!",
        b"END",
    ]
    out = b""
    for c in cards:
        assert len(c) <= 80, c
        out += c.ljust(80)
    return out


def shapefile() -> bytes:
    body = struct.pack("<ii", 0, 0)          # a Null Shape record: type only
    total = 100 + len(body)
    head = struct.pack(">i", 9994)                       # offset 0
    head += b"\x00" * 5                                  # offset 4, unused
    head += struct.pack(">i", total // 2)                 # offset 9, in words
    head += b"\x00" * 12                                 # offset 13, unused
    head += struct.pack("<ii", 1000, 0)                   # offset 25
    head += struct.pack("<dddd", 0.0, 0.0, 0.0, 0.0)     # offset 33, X/Y
    head += b"\x00" * 32                                 # offset 65, Z/M
    head += b"\x00" * 3                                  # offset 97, end
    assert len(head) == 100, len(head)
    return head + body


def tiff() -> bytes:
    text = GREETING + b"\x00"
    e = "<"
    # 8-byte header, then a 1-entry IFD, then the string the entry points at.
    ifd_off = 8
    str_off = ifd_off + 2 + 12 + 4
    head = b"II" + struct.pack(e + "H", 42) + struct.pack(e + "I", ifd_off)
    ifd = struct.pack(e + "H", 1)
    ifd += struct.pack(e + "HHII", 270, 2, len(text), str_off)  # ImageDescription
    ifd += struct.pack(e + "I", 0)                            # no next IFD
    return head + ifd + text


def dbf() -> bytes:
    fields = 2
    hlen = 32 + fields * 32 + 1
    head = bytearray(hlen)
    head[0] = 0x03                       # dBASE III without a memo file
    head[1:4] = bytes((126, 1, 1))       # a date, which the header must carry
    struct.pack_into("<I", head, 4, 0)             # record count
    struct.pack_into("<H", head, 8, hlen)          # header length
    struct.pack_into("<H", head, 10, 1 + 11)       # record length
    name = b"HelloWorld"
    head[32:32 + len(name)] = name
    head[32 + 11] = ord("C")             # type: character
    head[32 + 16] = 20                   # length
    head[32 + 32] = ord("N")
    head[32 + 32 + 16] = 1
    head[hlen - 1] = 0x0D                 # end of field descriptors
    return bytes(head) + b" " * (1 + 11)


BUILDERS = {
    "coff": coff, "dwarf": dwarf, "fits": fits, "shapefile": shapefile,
    "tiff": tiff, "dbf": dbf,
}
CHECKS = {
    "coff": V.check_coff, "dwarf": V.check_dwarf, "fits": V.check_fits,
    "shapefile": V.check_shapefile, "tiff": V.check_tiff, "dbf": V.check_dbf,
}


def test_every_builder_has_a_checker():
    assert set(BUILDERS) == set(CHECKS), (
        f"a format is built but not checked: {set(BUILDERS) - set(CHECKS)}")


def test_a_correct_buffer_is_accepted_and_the_greeting_is_found():
    for name, build in BUILDERS.items():
        ok, why = CHECKS[name](build())
        assert ok, f"{name}: {why}"
        assert why.strip(), f"{name} accepted but said nothing about the file"


def test_the_three_that_have_a_text_field_name_it():
    """COFF, FITS and TIFF can carry the greeting; the other three cannot.

    Asserted separately because it is the interesting half. A checker that
    reports "structure ok" is right, but a *file* that quietly puts the
    greeting somewhere the format does not read would be a lie.
    """
    for name, needle in (("coff", "is the greeting"),
                         ("fits", "carries the greeting"),
                         ("tiff", "is the greeting")):
        ok, why = CHECKS[name](BUILDERS[name]())
        assert ok and needle in why, f"{name}: {why}"
    for name in ("dwarf", "shapefile", "dbf"):
        ok, why = CHECKS[name](BUILDERS[name]())
        assert ok, f"{name}: {why}"
    # DWARF and dBASE have a free-text field too -- just not where it looked.
    assert "producer" in CHECKS["dwarf"](dwarf())[1]
    assert "HelloWorld" in CHECKS["dbf"](dbf())[1]


def test_a_wrong_magic_number_is_rejected():
    cases = {
        "coff": lambda b: b[:2] + struct.pack("<H", 0x8664) + b[4:],  # x86-64
        "shapefile": lambda b: struct.pack(">i", 9995) + b[4:],
        "tiff": lambda b: b[:2] + struct.pack("<H", 43) + b[4:],
        "dbf": lambda b: b"\x07" + b[1:],
    }
    for name, corrupt in cases.items():
        ok, why = CHECKS[name](corrupt(BUILDERS[name]()))
        assert not ok, f"{name} accepted a file with the wrong magic number: {why}"


def test_a_length_that_disagrees_with_the_file_is_rejected():
    cases = {
        "shapefile": lambda b: b[:8] + struct.pack(">i", 9) + b[12:],
        "dwarf": lambda b: b[:4] + struct.pack("<I", 999) + b[8:],
        "dbf": lambda b: b[:8] + struct.pack("<H", 7) + b[10:],
        "fits": lambda b: b[:-1],
    }
    for name, corrupt in cases.items():
        ok, why = CHECKS[name](corrupt(BUILDERS[name]()))
        assert not ok, f"{name} accepted a header whose length is wrong: {why}"


def test_an_offset_past_the_end_is_rejected():
    for name, corrupt in (
        ("tiff", lambda b: b[:4] + struct.pack("<I", 9999) + b[8:]),
        ("coff", lambda b: b[:36] + struct.pack("<I", 4096) + b[40:]),
    ):
        ok, why = CHECKS[name](corrupt(BUILDERS[name]()))
        assert not ok, f"{name} accepted an offset that points nowhere: {why}"


def test_a_fits_card_with_the_equals_in_the_wrong_column_is_rejected():
    """The check that a hex dump cannot do for you.

    Moving the '=' one column left changes no byte count and no hex token, so
    every other check in this repository passes. Only a reader that knows
    FITS puts '=' in column 9 will notice.
    """
    buf = bytearray(fits())
    card = bytearray(buf[0:80])
    card[8:9] = b" "
    card[7:8] = b"="
    buf[0:80] = card
    ok, why = V.check_fits(bytes(buf))
    assert not ok, f"a misplaced '=' was accepted: {why}"


def test_the_payload_join_is_not_silent_about_its_assumption():
    """`payload` assumes a contiguous dump from offset 0 -- so say so.

    The dump offset itself must not be mistaken for payload: `00000000` is
    eight hex digits and matches no \\b..\\b pair, which is the only reason
    joining the runs is safe.
    """
    text = ("// 48 65 6C 6C 6F 20 57 6F 72 6C 64 21 00 00 00 00"
            "  |Hello World!....|   <- 0000\n")
    assert V.payload_bytes(text) == GREETING + b"\x00\x00\x00\x00", V.payload_bytes(text)
    # An offset column would contribute a token: "00000000" has word boundaries
    # either side of its last byte pair, so `00` is extracted from it. The dumps
    # this path reads therefore carry no offset column, and the offset is
    # written after the ASCII gutter where it cannot be mistaken for payload.
    assert list(V.hex_runs("00000000: 48 65 6C")) == [], (
        "an offset column would be read as payload")


def test_object_formats_are_routed_by_extension():
    for ext in ("coff", "dwarf", "wcs", "shp", "tiff", "shpffil"):
        assert ext in V.OBJECT_FORMATS, f"{ext} has no checker registered"


def test_check_encoding_dispatches_on_the_suffix_not_the_language():
    """The `path.stem` bug, named so it cannot come back.

    `hello.tiff`.stem is `hello`, not `tiff`. Routing on the stem put sixteen
    files into the generic branch once already. A file that is still a text
    placeholder is routed to the generic branch on purpose -- there is no
    payload for a struct to read -- so this asserts about the ones that have
    real bytes.
    """
    if not _ready():
        return
    routed = 0
    for f in V.candidates():
        ext = (f.suffix or "").lstrip(".").lower()
        if ext not in V.OBJECT_FORMATS:
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        if len(V.payload_bytes(text)) < 80:
            continue
        kind, ok, why = V.check_encoding(f)
        assert kind == V.OBJECT_FORMATS[ext][0], (
            f"{f.name} has extension {ext} but was routed to {kind}")
        assert ok, f"{f.name}: {why}"
        routed += 1
    # Once the object formats are built there will be files here. Until then the
    # assertion above is vacuous, which is exactly the state that hid E30, so
    # it is stated rather than left implicit.
    print(f"    (object-format files with real bytes: {routed})")