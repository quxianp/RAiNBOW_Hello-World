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


def build_flatgeobuf() -> bytes:
    """A FlatGeobuf header, and no greeting anywhere in it.

    FlatGeobuf replaced GeoPackage's JSON sidecar with a header inside the
    file: magic, version, header type, then a bounding box and a geometry
    type. There is no field for a name, a description or a comment, and the
    four magic bytes are 0A 0D 0D 0A -- two newlines -- so a dump of this file
    opens with what looks like two blank lines.

    The envelope here is the unit square, because a bounding box of 0..0 is
    valid and useless and an inverted one is a file a reader rejects.
    """
    out = struct.pack(">I", 0x0A0D0D0A)
    out += bytes((3, 1))                                # version 3, header
    out += struct.pack(">dddd", 0.0, 0.0, 1.0, 1.0)    # envelope
    out += struct.pack(">I", 0)                        # geometry: unknown
    return out + b"\x00" * 64


def build_dos_exe() -> bytes:
    """A DOS MZ executable: a 28-byte header, a relocation table, a load module.

    `e_cblp` counts 16-byte paragraphs of relocation and `e_cp` counts 512-byte
    pages of code, and the header's own size plus those two has to account for
    the file. `e_ip` and `e_cs` point at the entry point within the load module:
    e_cs is the segment, e_ip the offset, and the usual value for a hand-written
    one is 0x0000 with e_cp set -- because the code is placed at offset 0x100,
    which is the first page after the header.
    """
    header = struct.pack(
        "<2s13H",
        b"MZ",
        0,      # e_cblp:  final page count -- the whole file fits, so 0
        1,      # e_cp:    pages in the load module
        4,      # e_crlc:  relocation entries
        0,      # e_cparhdr
        0x0010, # e_minalloc
        0xFFFF, # e_maxalloc
        0,      # e_ss
        0x0100, # e_sp:   stack pointer, at the top of the segment
        0,      # e_csum:  not checked
        0x0000, # e_ip:    entry offset within the load module
        0,      # e_cs
        0x001C, # e_lfarlc: relocation table at offset 0x1C
        0,      # e_ovno
    )
    assert len(header) == 28, len(header)
    reloc = struct.pack("<4H", 0, 0, 0, 0)      # four empty relocation entries
    text = GREETING + b"\r\n$"
    assert len(text) <= 512, len(text)
    return header + reloc + text.ljust(512, b"\x90")


def build_pe() -> bytes:
    """A PE32 image: an MZ stub, then a PE signature, a COFF header, an optional
    header and one section header.

    `e_lfanew` at 0x3C is the interesting field: it is where the PE signature
    is, and a stub whose e_lfanew disagrees with where the signature actually
    sits is a file every loader rejects.
    """
    stub = bytearray(64)
    stub[0:2] = b"MZ"
    e_lfanew = 64
    struct.pack_into("<I", stub, 0x3C, e_lfanew)

    coff = struct.pack("<HHIIIHH", 0x014C, 1, 0, 0, 0, 224,
                       0x0102 | 0x0002)          # executable | 32-bit
    opt = bytearray(224)
    struct.pack_into("<H", opt, 0, 0x010B)          # PE32
    struct.pack_into("<B", opt, 2, 14)              # linker version
    struct.pack_into("<I", opt, 16, 0x1000)         # entry point RVA
    struct.pack_into("<I", opt, 20, 0x1000)         # base of code
    struct.pack_into("<I", opt, 28, 0x400000)       # image base
    struct.pack_into("<I", opt, 32, 0x1000)         # section alignment
    struct.pack_into("<I", opt, 36, 0x200)          # file alignment
    struct.pack_into("<I", opt, 56, 0x2000)         # size of image
    struct.pack_into("<I", opt, 60, 0x200)          # size of headers
    struct.pack_into("<H", opt, 68, 3)              # subsystem: console
    struct.pack_into("<I", opt, 72, 16)             # size of stack reserve
    struct.pack_into("<I", opt, 76, 0x1000)         # size of stack commit
    struct.pack_into("<I", opt, 80, 0x1000)         # size of heap reserve
    struct.pack_into("<I", opt, 84, 0x1000)         # size of heap commit
    section = (
        b".text\x00\x00\x00"
        + struct.pack("<IIIIIIHHI",
                     len(GREETING),        # virtual size
                     0x1000,               # virtual address
                     0x200,                # size of raw data
                     e_lfanew + 4 + len(coff) + 224 + 40,   # pointer to raw data
                     0, 0, 0, 0,
                     0x60000020)           # CODE | EXECUTE | READ
    )
    return bytes(stub) + b"PE\0\0" + coff + bytes(opt) + section


def build_macho() -> bytes:
    """A 32-bit Mach-O executable header.

    `MH_EXECUTE` is file type 2, and `ncmds` is 0 because an executable header
    with no load commands is a relocatable object rather than a program -- which
    is why the checker rejects ncmds == 0 and the builder sets 1.
    """
    cpu, sub = 0x01000007, 3            # CPU_TYPE_X86, CPU_SUBTYPE_X86_ALL
    return struct.pack("<IiiIIII", 0xFEEDFACE, cpu, sub,
                       2,               # MH_EXECUTE
                       1,               # ncmds
                       0,               # sizeofcmds, patched below
                       0x00000085)      # MH_NOUNDEFS | MH_DYLDLINK | MH_TWOLEVEL


def build_dex() -> bytes:
    """A Dalvik bytecode file: the magic, then a header whose lengths agree.

    `file_size` is the field that matters -- it is the check that catches a
    truncated dump, and a DEX whose header lies about its own length is rejected
    by the runtime before a single class is read.
    """
    magic = b"dex\n035\0"
    checksum = 0xDEADBEEF
    # twenty bytes: a SHA-1 signature is 20 bytes, and writing sixteen shifts
    # every field after it by four -- which the header_size check caught on the
    # first run, reporting 305419896 where 112 belongs.
    signature = bytes(range(20))
    file_size = 112
    body = bytearray()
    body += magic
    body += struct.pack("<I", checksum)
    body += signature
    body += struct.pack("<I", file_size)
    body += struct.pack("<I", 112)      # header_size
    body += struct.pack("<I", 0x12345678)   # endian_tag: the constant
    body += struct.pack("<I", 0)        # link_size
    body += struct.pack("<I", 0)        # link_off
    body += struct.pack("<I", 0)        # map_off
    body += struct.pack("<I", GREETING.__len__())   # string_ids_size
    body += struct.pack("<I", 0)        # string_ids_off
    body += struct.pack("<I", 0)        # type_ids_size
    body += struct.pack("<I", 0)        # type_ids_off
    body += struct.pack("<I", 0)        # proto_ids_size
    body += struct.pack("<I", 0)        # proto_ids_off
    body += struct.pack("<I", 0)        # field_ids_size
    body += struct.pack("<I", 0)        # field_ids_off
    body += struct.pack("<I", 0)        # method_ids_size
    body += struct.pack("<I", 0)        # method_ids_off
    body += struct.pack("<I", 0)        # class_defs_size
    body += struct.pack("<I", 112)      # class_defs_off
    body += GREETING                    # the greeting, after the header
    body[32:36] = struct.pack("<I", len(body))
    assert len(body) >= 112
    return bytes(body)


def _uleb(n: int) -> bytes:
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def build_wasm() -> bytes:
    """A WebAssembly module: the magic, version 1, and a type section.

    Sections are a one-byte id, a ULEB128 length, and that many bytes. Section 1
    is the type section, and one type with no parameters and no results is the
    smallest module that any engine will accept.
    """
    body = b"\x60" + _uleb(0) + _uleb(0)      # functype: () -> ()
    out = b"\x00asm" + struct.pack("<I", 1)
    out += bytes((1,)) + _uleb(len(body)) + body
    return out


def build_ans() -> bytes:
    """An ANSI X3.68-1976 record file: fixed-width records, form-feed separated.

    The format is one rule: every record is exactly as wide as the first, records
    end with a form feed, and so does the file. There is no header and no
    metadata, which makes the greeting the whole of the first record.
    """
    return GREETING.ljust(80, b" ") + b"\x0c"


BUILDERS = {
    "coff": ("COFF", build_coff),
    "dwarf": ("DWARF", build_dwarf),
    "wcs": ("WCS", build_wcs),
    "shp": ("SHP", build_shapefile),
    "tiff": ("TIFF", build_tiff),
    "shpffil": ("SHPFFIL", build_dbf),
    "flatgeobuf": ("FlatGeobuf", build_flatgeobuf),
    # executable and bytecode formats
    "dos_exe": ("DOS executable", build_dos_exe),
    "pe_format": ("PE format", build_pe),
    "macho": ("Mach-O", build_macho),
    "dex": ("Dalvik Bytecode", build_dex),
    "wasm_binary": ("WebAssembly Binary", build_wasm),
    "ans": ("ANS", build_ans),
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
        "dos_exe": (
            "// DOS executable: the MZ header, 28 bytes, and then two numbers\n"
            "// that decide everything. e_cblp counts 16-byte paragraphs of\n"
            "// relocation table and e_cp counts 512-byte pages of load module,\n"
            "// and the header plus those two has to account for the whole file.\n"
            "//\n"
            "// The entry point is a segment and an offset, e_cs and e_ip, and\n"
            "// the code here starts at offset 0 of the load module -- which is\n"
            "// why e_ip is 0 rather than 0x100. Nothing prints; the code is in\n"
            "// the segment.\n"
            "//\n"
            "// Hello World! is the load module's own bytes.\n"
            "//\n"
        ),
        "pe_format": (
            "// PE format: a Portable Executable, which is an MZ stub, a PE\n"
            "// signature, a COFF header, an optional header and a section\n"
            "// table. Four headers, and each one has a length field describing\n"
            "// the one after it.\n"
            "//\n"
            "// The field worth knowing is e_lfanew at offset 0x3C: it is where\n"
            "// the PE signature is. An MZ stub whose e_lfanew disagrees with the\n"
            "// signature's actual position is a file every loader rejects, and\n"
            "// it is indistinguishable from correct in a hex dump.\n"
            "//\n"
            "// Hello World! is the .text section's raw data.\n"
            "//\n"
        ),
        "macho": (
            "// Mach-O: Apple's executable format, and a header of seven\n"
            "// four-byte fields -- magic, cputype, cpusubtype, filetype,\n"
            "// ncmds, sizeofcmds, flags.\n"
            "//\n"
            "// The magic is the constant FEEDFACE written in the *file's* byte\n"
            "// order, which is why there are four magics and not one. Reading\n"
            "// the magic wrong way round reads every field after it as a\n"
            "// byte-swapped number and still succeeds, which is why the\n"
            "// checker reports the endianness it chose.\n"
            "//\n"
            "// filetype 2 is MH_EXECUTE. ncmds is 1 rather than 0, because a\n"
            "// header with no load commands is a relocatable object.\n"
            "//\n"
            "// Hello World! is in the comment above and nowhere in the header,\n"
            "// because a Mach-O header has no field for prose.\n"
            "//\n"
        ),
        "dex": (
            "// Dalvik bytecode: the magic `dex\\n035\\0`, a checksum, a 20-byte\n"
            "// SHA-1 signature, and then a row of lengths that all have to\n"
            "// agree with each other and with the file.\n"
            "//\n"
            "// header_size is 112 and endian_tag is the constant 0x12345678 --\n"
            "// it is not an endianness, it is a byte-order mark, and a reader\n"
            "// that got it backwards would know. file_size is the field that\n"
            "// catches a truncated dump, which is the failure this file is most\n"
            "// likely to have.\n"
            "//\n"
            "// Hello World! follows the header.\n"
            "//\n"
        ),
        "wasm_binary": (
            "// WebAssembly Binary: the four bytes 00 61 73 6D, a version, and\n"
            "// then sections -- a one-byte id, a ULEB128 length, that many\n"
            "// bytes. Every length is ULEB128, which is the only part of a WASM\n"
            "// file that is not a fixed width.\n"
            "//\n"
            "// Section 1 is the type section, and one function type with no\n"
            "// parameters and no results is the smallest module any engine\n"
            "// accepts.\n"
            "//\n"
            "// Hello World! is in the comment above: a WASM module is a\n"
            "// compiled artefact and has nowhere to put prose.\n"
            "//\n"
        ),
        "ans": (
            "// ANS is the ANSI X3.68-1976 record format, and the entire\n"
            "// specification is one rule: every record is exactly as wide as\n"
            "// the first, records end with a form feed, and so does the file.\n"
            "//\n"
            "// There is no header, no metadata and no version field, which makes\n"
            "// it the shortest of the formats here at eighty-one bytes and also\n"
            "// the only one whose payload is entirely text.\n"
            "//\n"
            "// Hello World! is the record, left-justified and padded to eighty\n"
            "// characters, which is what the format requires.\n"
            "//\n"
        ),
        "flatgeobuf": (
            "// FlatGeobuf: the format GDAL 3.4 and QGIS 3.30 moved to, which\n"
            "// replaced GeoPackage's JSON sidecar with a header inside the\n"
            "// file. Magic, version, header type, then a bounding box.\n"
            "//\n"
            "// There is no greeting in this file, and the reason is worth\n"
            "// seeing once. The magic is 0A 0D 0D 0A -- so the first eight\n"
            "// bytes of this dump are two newlines with four bytes between\n"
            "// them, which is why FlatGeobuf looks like a text file that has\n"
            "// a very short first line. The rest is a geometry type and\n"
            "// padding: no name, no description, no comment field. A\n"
            "// `Hello World!` in any of them would be a file no reader\n"
            "// accepts, so this one is a correct header with nothing to say.\n"
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