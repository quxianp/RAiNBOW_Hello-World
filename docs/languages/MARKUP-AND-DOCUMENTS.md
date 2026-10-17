# Adding a template: markup, prose and document formats

Two hundred-odd entries are markup, data or configuration, and none of them is a
programming language. This is the family where "no program" is not a shortfall.

## The trap

Assuming a document format needs a Hello World *program*. It does not. A feed is
a feed whether or not anything is executing, and the honest content is a
document whose text is the greeting.

## Four shapes, and the differences matter

**Markup with a body.** Markdown, AsciiDoc, Org, reStructuredText, MediaWiki,
Pod, RDoc, Text, Textile, Creole. All of them get a heading and the greeting.

**Markup that is a document about something.** RSS, Atom, OPML, XSL-FO, XPages,
GEXF, MusicXML, TEI, SVG, the OGC service documents. These have a `title` or
`<title>` element, and that is where the greeting belongs. A `<description>` is
also a legitimate home.

**Markup with a grammar.** RELAX NG, Schematron. These describe a language, not a
document, so the greeting is a rule that asserts it.

**Formats with no text form at all.** PNG, GIF, JPEG, ICO, WebP, JXL, AVIF, HEIF,
PBM/PGM/PPM/PNM, TIFF, BMP, MessagePack, CBOR, BSON.

## What the last group actually got

Each of those carries its format's **real magic number** and, where there is
room, the greeting in a field that is free-form. Examples already in the
repository:

```text
PNG    89 50 4E 47 0D 0A 1A 0A        the signature
GIF    47 49 46 38 39 61                GIF89a
TIFF   49 49 2A 00  08 00 00 00        II, magic 42, IFD offset
PGM    50 35 0A 23 20 48 65 ...        P5, then a # comment, which the format
                                        permits anywhere in the header
```

The netpbm ones are the nicest, because a `#` comment in a PGM header is legal
and the file is genuinely valid: `python scripts/verify_encodings.py` decodes
them.

## The trap inside the trap

A binary format does not become a Hello World by being described. What was added
is a **real header with the greeting in the one field that accepts arbitrary
bytes** — the PNG's `tEXt` chunk, the GIF's comment extension, the PDF's content
stream, the TIFF's Software tag, the PGM's comment. Those are files the format
itself accepts.

A `.doc` gets the OLE compound-file signature and says where the greeting would
live inside the stream directory. That is the honest answer, and it is better
than a hex dump that is wrong in one byte.

## Before you write one

- Is there a title, description or comment field? Use it.
- Is the format binary? Then give the real signature, and never fabricate
  bytes you have not computed.
- Does the format permit a comment? Netpbm does, and that makes the answer
  verifiable.
- If it has a checksum, compute it — see `docs/ENCODINGS.md`.