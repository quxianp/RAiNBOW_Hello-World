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
import sys

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


def flatgeobuf() -> bytes:
    out = struct.pack(">I", 0x0A0D0D0A)                 # the magic number
    out += bytes((3, 1))                                 # version, header type
    out += struct.pack(">dddd", -1.0, -1.0, 1.0, 1.0)   # the envelope
    out += struct.pack(">I", 0)                          # geometry: unknown
    return out + b"\x00" * 64


def pe() -> bytes:
    stub = bytearray(64)
    stub[0:2] = b"MZ"
    struct.pack_into("<I", stub, 0x3C, 64)
    coff = struct.pack("<HHIIIHH", 0x014C, 1, 0, 0, 0, 224, 0x0102)
    opt = bytearray(224)
    struct.pack_into("<H", opt, 0, 0x010B)
    return bytes(stub) + b"PE\0\0" + coff + bytes(opt)


def macho() -> bytes:
    return struct.pack("<IiiIIII", 0xFEEDFACE, 0x01000007, 3, 2, 1, 0, 0x85)


def dex() -> bytes:
    out = bytearray(b"dex\n035\0")
    out += struct.pack("<I", 0xDEADBEEF)
    out += bytes(range(20))
    out += struct.pack("<I", 112)      # file_size, patched below
    out += struct.pack("<I", 112)      # header_size
    out += struct.pack("<I", 0x12345678)
    out += b"\x00" * (112 - len(out))
    out += GREETING
    out[32:36] = struct.pack("<I", len(out))
    return bytes(out)


def wasm() -> bytes:
    return b"\x00asm" + struct.pack("<I", 1) + b"\x01\x03\x60\x00\x00"


def dos_exe() -> bytes:
    head = struct.pack("<2s13H", b"MZ", 0, 1, 4, 0, 0x10, 0xFFFF,
                       0, 0x100, 0, 0, 0, 0x1C, 0)
    assert len(head) == 28
    reloc = struct.pack("<4H", 0, 0, 0, 0)          # four empty entries
    text = (GREETING + b"\r\n$").ljust(512, b"\x90")  # one 512-byte page
    return head + reloc + text


def ans() -> bytes:
    return GREETING.ljust(80, b" ") + b"\x0c"


BUILDERS = {
    "coff": coff, "dwarf": dwarf, "fits": fits, "shapefile": shapefile,
    "tiff": tiff, "dbf": dbf, "flatgeobuf": flatgeobuf,
    "pe_format": pe, "macho": macho, "dex": dex, "wasm_binary": wasm,
    "dos_exe": dos_exe, "ans": ans, "shp": shapefile,
}
CHECKS = {
    "coff": V.check_coff, "dwarf": V.check_dwarf, "fits": V.check_fits,
    "shapefile": V.check_shapefile, "tiff": V.check_tiff, "dbf": V.check_dbf,
    "flatgeobuf": V.check_flatgeobuf, "pe_format": V.check_pe,
    "macho": V.check_macho, "dex": V.check_dex, "wasm_binary": V.check_wasm,
    "dos_exe": V.check_dos_exe, "ans": V.check_ans,
    "shp": V.check_shapefile,
}


def test_every_builder_has_a_checker():
    """Every format the module builds must be one the verifier can check.

    Checked against `build_object_formats.BUILDERS`, which is the single
    definition. The first version compared two hand-maintained tables in this
    file, and the two drifted the first time a format was added.
    """
    real = _builders().BUILDERS
    missing = [lang for key, (lang, _) in real.items()
               if key not in V.OBJECT_FORMATS]
    assert not missing, f"built but not checkable: {missing}"
    assert len(real) >= 25, f"only {len(real)} formats built"


def test_a_correct_buffer_is_accepted_and_the_greeting_is_found():
    for name, build in BUILDERS.items():
        ok, why = CHECKS[name](build())
        assert ok, f"{name}: {why}"
        assert why.strip(), f"{name} accepted but said nothing about the file"


def test_the_three_that_have_a_text_field_name_it():
    """Four have a text field; the rest do not.

    Asserted separately because it is the interesting half. A checker that
    reports "structure ok" is right, but a *file* that quietly puts the
    greeting somewhere the format does not read would be a lie.
    """
    for name, needle in (("coff", "is the greeting"),
                         ("fits", "carries the greeting"),
                         ("tiff", "is the greeting")):
        ok, why = CHECKS[name](BUILDERS[name]())
        assert ok and needle in why, f"{name}: {why}"
    for name in ("dwarf", "shapefile", "dbf", "pe_format", "macho", "dex",
                 "wasm_binary", "dos_exe"):
        ok, why = CHECKS[name](BUILDERS[name]())
        assert ok, f"{name}: {why}"
    # DWARF and dBASE do have a free-text field, just not where it looked.
    assert "producer" in CHECKS["dwarf"](dwarf())[1]
    assert "HelloWorld" in CHECKS["dbf"](dbf())[1]
    # ANS is the one binary format whose entire payload is text.
    ok, why = CHECKS["ans"](ans())
    assert ok and "80 characters" in why, f"ans: {why}"


def test_a_wrong_magic_number_is_rejected():
    cases = {
        "coff": lambda b: b[:2] + struct.pack("<H", 0x8664) + b[4:],  # x86-64
        "shapefile": lambda b: struct.pack(">i", 9995) + b[4:],
        "tiff": lambda b: b[:2] + struct.pack("<H", 43) + b[4:],
        "dbf": lambda b: b"\x07" + b[1:],
        "flatgeobuf": lambda b: struct.pack(">I", 0x0A0D0D0B) + b[4:],
        "pe_format": lambda b: b"ZZ" + b[2:],
        "macho": lambda b: struct.pack("<I", 0xFEEDFACD) + b[4:],
        "dex": lambda b: b"dex" + b"x" + b[4:],
        "wasm_binary": lambda b: b"\x00asx" + b[4:],
        "dos_exe": lambda b: b"ZZ" + b[2:],
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
        "dex": lambda b: b[:32] + struct.pack("<I", 9999) + b[36:],
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
    for ext in ("coff", "dwarf", "wcs", "shp", "tiff", "shpffil", "flatgeobuf",
                "pe_format", "macho", "dex", "wasm_binary", "dos_exe", "ans"):
        assert ext in V.OBJECT_FORMATS, f"{ext} has no checker registered"


def test_the_macho_endianness_is_derived_not_guessed():
    """Reading the magic the wrong way round succeeds and reports nonsense.

    A Mach-O file writes the constant 0xFEEDFACE in the file's byte order, so
    the magic a little-endian read returns decides the endianness of everything
    after it. The first version had the mapping inverted and reported
    `cpu 117440513, file type 33554432` for a perfectly correct header -- every
    field a byte-swapped number, and no failure anywhere, because a byte-swapped
    uint32 is still a uint32.

    So the check is that the values come out as the ones written.
    """
    buf = macho()
    ok, why = V.check_macho(buf)
    assert ok, why
    cpu, sub, ftype = struct.unpack_from("<iiI", buf, 4)
    assert f"cpu {cpu}/{sub}" in why, why
    assert f"file type {ftype}" in why, why
    assert ftype == 2, "MH_EXECUTE is file type 2; the builder says otherwise"


def test_a_preamble_that_names_the_magic_number_does_not_become_payload():
    """The FlatGeobuf bug, kept.

    Its file says "the magic is 0A 0D 0D 0A" in the preamble, and those four
    hex pairs were read as the first bytes of the file. The reported version
    was 10 -- 0x0A, leaked out of the sentence that explains 0x0A -- and the
    checker rejected a file it had built itself.

    A dump line is identified by its ASCII gutter, so a comment that happens
    to contain hex is excluded no matter what it says.
    """
    preamble = ("// FlatGeobuf: magic 0A 0D 0D 0A, version 3.\n"
                "// The envelope follows in four big-endian doubles.\n")
    buf = flatgeobuf()
    body = "\n".join(
        "// " + " ".join(f"{b:02X}" for b in buf[i:i + 16]).ljust(47)
        + "  |" + "".join(chr(c) if 32 <= c < 127 else "."
                          for c in buf[i:i + 16]) + "|   <- %04X" % i
        for i in range(0, len(buf), 16))
    got = V.payload_bytes(preamble + body + "\n")
    assert got == buf, (
        f"preamble leaked into the payload: got {len(got)} bytes, "
        f"expected {len(buf)}; first four are {got[:4].hex(' ')}")


def test_a_flatgeobuf_envelope_that_is_the_wrong_way_round_is_rejected():
    """A bounding box with min > max passes every magic-number check.

    FlatGeobuf's envelope is four big-endian doubles and nothing else, so a
    transposed pair is perfectly well-formed bytes in a perfectly well-formed
    file. Only a checker that reads the numbers as a box rather than as a
    sequence of eight bytes notices.
    """
    buf = bytearray(flatgeobuf())
    struct.pack_into(">d", buf, 6, 1.0)          # Xmin past Xmax
    struct.pack_into(">d", buf, 22, -1.0)
    ok, why = V.check_flatgeobuf(bytes(buf))
    assert not ok, f"an inverted envelope was accepted: {why}"


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
        minimum = V.OBJECT_FORMATS[ext][2]
        if len(V.payload_bytes(text)) < minimum:
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


def _builders():
    """The real builders, loaded once.

    The test file used to carry its own copy of every format's constructor, and
    the moment a format was added to the real module the copy went stale and the
    suite reported "png has a route floor and a checker but nothing builds it"
    -- which is the right complaint about the wrong object. The module is the
    only definition; the tests build with it.
    """
    key = "build_object_formats_under_test"
    if key in sys.modules:
        return sys.modules[key]
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        key, ROOT / "scripts" / "build_object_formats.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    spec.loader.exec_module(mod)
    return mod


def _build(key: str) -> bytes:
    fn = _builders().BUILDERS[key][1]
    # `build_rar` returns bytes directly; the tuple case is a builder that has
    # nothing else to hand back.
    return fn[0] if isinstance(fn, tuple) else fn()


def test_the_route_floor_is_each_format_s_own_minimum():
    """A shared floor was wrong in both directions, so the floor is data now.

    At 80 bytes it skipped every small file it had been written for; at a
    smaller number it would hand an empty buffer to `struct.unpack_from` and
    raise. Each entry therefore carries the length below which a buffer cannot
    be a real file of that format, which is also the length its own checker
    bounds-checks against.

    The buffer handed to the checker is a *truncation* of a real one, not a
    buffer of zeros. Zeros fail on the magic number -- correctly, but for the
    wrong reason -- which is how a test can assert "it rejected it" forever
    without ever testing the length check it is about.
    """
    real = _builders().BUILDERS
    for tag, (kind, check, minimum) in V.OBJECT_FORMATS.items():
        assert isinstance(minimum, int) and minimum > 0, tag
        if tag not in real:
            # An alias -- `obj` is `coff`, `tif` is `tiff`. It shares the
            # checker's floor, so the canonical tag already tested it.
            assert any(a in real and V.OBJECT_FORMATS[a][1] is check
                       for a in V.OBJECT_FORMATS), (
                f"{tag} has a route floor and a checker but nothing builds it")
            continue
        ok, why = check(_build(tag)[:minimum - 1])
        assert not ok, f"{tag} accepted a {minimum - 1}-byte file: {why}"
        assert str(minimum - 1) in why or "short" in why or "need" in why \
            or "empty" in why, (
                f"{tag} rejected a short buffer without saying how short: {why}")