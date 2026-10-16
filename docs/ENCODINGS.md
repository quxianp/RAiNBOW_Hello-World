# The files that are not programs

Roughly seventy files in `hello/full/` contain no program at all. They are
encodings — the greeting, transformed — and they exist because an encoding of a
known string is not unknowable, even when a *program* in that language would be.

They are also the most error-prone files in the repository, because a hex dump
that is wrong in one byte is indistinguishable from one that is right. Every byte
sequence in these files was therefore produced by the library that defines the
format, and `scripts/verify_encodings.py` decodes them all back to check it.

```bash
python scripts/verify_encodings.py --verbose
```

## What is there

| kind | file | what it holds |
|---|---|---|
| positional encoding | `base16`, `base62`, `base85`, `ascii85`, `base95` | the greeting in that alphabet, with the alphabet written out |
| checksummed | `base58`, `intel-hex`, `motorola-s-record`, `srec` | the same, plus the checksum and the arithmetic that produced it |
| compressed | `deflate`, `gzip-binary`, `bzip2-binary`, `xz-binary`, `snappy-binary` | a real stream that really decompresses |
| container | `zip-binary`, `tar-binary` | a real archive containing `hello.txt` |
| image | `bmp`, `gif-binary`, `png-binary`, `jpeg`, `pgm`, `ppm`, `pbm`, `pnm`, `webp`, `jxl`, `avif`, `heif`, `ico`, `tiff` | the format's real magic, and the greeting in the field that is free-form |
| serialisation | `messagepack`, `cbor`, `bson` | a document holding the greeting, encoded by hand |
| office | `doc`, `xls`, `ppt`, `msi`, `chm` | the OLE compound-file signature, and where the greeting would live |
| object | `coff`, `omf`, `llvm-bitcode`, `dwarf`, `srec`, `intel-hex` | the header a linker or reader parses |
| textual encodings | `nato-phonetic-alphabet`, `morse-code-binary`, `hollerith-code`, `ebcdic`, `iso-8859-1`, `windows-1252`, `utf-16`, `utf-32`, `utf-7`, `unicode-code-point` | the greeting spelled in that scheme |

## The four that are worth knowing about

**Intel HEX and S-records carry checksums**, and a checksum written from memory
is a checksum that is wrong — and a wrong checksum reads as correct because
nothing about the rest of the record changes.

```
:0C00000048656C6C6F20576F726C6421B7
 count 0x0C, offset 0x0000, type 00, twelve data bytes, checksum B7
 the bytes sum to 1097 = 0x449, so CC = 0x100 - 0x49 = 0xB7

S10F000048656C6C6F20576F726C6421B3
 count 0x0F covers a 2-byte address, 12 data bytes and the checksum
 the sum is 1100 = 0x44C and S-records use the ones complement: ~0x4C = 0xB3
```

**Hollerith is not ASCII.** Digits are 0–9, then A–I restart at 1, J–R restart at
0 again, and S–Z restart at 1. So `Hello` is `85 22 5 5 5`, and a reader who
assumed ASCII would be wrong in five of the twelve columns.

**UTF-7 only encodes the run of letters.** `Hello World!` is
`+ZeVnLIqe- World!`, with a literal space and a literal exclamation mark, because
only the eight consecutive ASCII letters need the base64 shift syntax.

**The netpbm files are real files.** P5, P6 and P4 headers permit `#` comments
anywhere in the header, so `Hello World!` is a legal comment in a genuine PGM
with a genuine one-pixel payload. A reader can feed the bytes to netpbm.

## The encodings of the encoding files

`bitwise`, `manchester-code`, `miller-code`, `nrz`, `aiken-code`, `huffman-coding`,
`arithmetic-coding`, `lzw`, `lz77`, `lz78`, `burrows-wheeler`, `rzi`,
`braille-encoding`, `packed-pixel`, `bcd-code`, `raw-bytes`.

These are computed rather than described, and two of the results are worth
repeating because they look wrong and are not:

- The **OR** of every byte of the greeting is `7F`. ASCII tops out at `0x7F`, so
  the OR of any run of ASCII reaches that ceiling, and this run does.
- **Huffman** codes these twelve symbols in 37 bits against 96 raw. A code built
  for one string is optimal for that string, and this one has three `l`s and two
  `o`s to exploit. It is also why no real format uses a single table.

## Why not just print?

Because a ZIP file does not print, a Base58 string is not a program, and a
`.doc` is an OLE compound file. Writing `print("Hello World!")` into any of these
would produce a file that looks like work and is not — which is the failure this
repository already has an entry for, in `logs/ERRORS.log`, about 34 templates
that were confidently wrong.
