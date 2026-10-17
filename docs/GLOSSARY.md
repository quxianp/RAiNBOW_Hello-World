# Glossary

This repository uses four different senses of "kind" and two of "layer", and
they are easy to confuse because they all sound like classifications of
languages. They are not. None of them is a classification of languages.

## The layers

| layer | where | counted by GitHub? |
|---|---|---|
| **core** | `hello/core/<slug>/hello.<ext>` | **yes** — this is the bar |
| **full** | `hello/full/<slug>/hello.<ext>` | no — vendored, present but not counted |

The core layer is 694 files with equal byte shares, and that is the whole
visual premise: equal bytes means equal slices, and 694 equal slices is a
rainbow. The full layer is everything else Linguist knows about — 6,632 files —
and it exists so that the repository is a complete answer to "what does
Linguist recognise" without 6,632 unequal slices ruining the bar.

So a file in `full/` is not less real. It is simply not in the picture.

## Linguist's types

Linguist classifies every language it knows into exactly four types, and they
appear as the manifest's `type` field:

| type | what it is | share of the core layer |
|---|---|---|
| `programming` | languages with a compiler or interpreter | the majority |
| `markup` | HTML, XML, Markdown, SVG | smaller |
| `data` | JSON, YAML, TOML, CSV | smaller |
| `prose` | plain text and prose formats | smallest |

`type` is **null for 6,490 files.** Linguist does not classify them — they are
esolangs, esoteric file formats, and entries that exist because somebody once
wrote a `.snippet` file. That is not a gap in the data; it is Linguist's actual
answer, and filling it in would mean inventing a classification Linguist does not
make.

## Our placeholder kinds

`scripts/classify_placeholders.py` sorts every file that has **no program** into
one of five kinds. This is not Linguist's vocabulary and it does not overlap with
Linguist's types:

| kind | what it is | what the file's answer is |
|---|---|---|
| `esolang` | a language Linguist will not classify | the canonical program, or an honest note |
| `unknown` | a language Linguist will classify but has no documented Hello World for | an admission naming the gap |
| `document` | a markup or data format | the document itself, with the greeting in its one free-text field |
| `program` | a language that *could* have a program and has not been written yet | an admission naming what is missing |
| `binary` | a format with no text form | the real magic number, and a computed payload |

Every file with no program carries an **admission line** saying which kind it is,
which group it was placed in, and where the classification came from. That line
is the point: 6,000-odd files that all said the same sentence would be a
repository that hides its own gaps.

## Segments

A **segment** is one coloured slice on GitHub's language bar. The core layer has
694 files and the bar shows **631 segments**, and both numbers are right.

Linguist folds dialects together before it counts. Seven HTML files in this
repository — `HTML`, `HTML+ERB`, `HTML+EEX`, `HTML+PHP`, `HTML+Razor`,
`HTML+Elixir`, `Ecmarkup` — are **one** segment, because Linguist merges HTML and
its dialects into a single language for the bar. 63 names are folded that way.

`docs/WHY-631-NOT-694.md` is the long answer. The short one is that a segment is
not a file: equal bytes per file makes 694 files of equal weight, and the bar
then merges some of them, and the merged slice is correspondingly wider. The bar
is still a rainbow; it is just 631 slices of it.

## Other words

**Admission** — the one-line statement in a file that says why it does not print
a greeting, naming the kind and the source. An admission is not a placeholder in
the apologetic sense. It is the answer for a file whose language has no answer.

**Template** — a program in `HELLO` inside
`scripts/generate_all_hello.py`. About 1,730 of them, plus 95 entries in
`INHERIT`, which is an explicit allowlist of dialects that share a parent's
syntax. `INHERIT` is a list and never a heuristic, because a heuristic that
guesses "these two are close enough" eventually produces a file in the wrong
language that passes every check.

**Declaration form** — a format with no program body, where the fields *are* the
answer: `.properties`, `pom.xml`, `go.mod`, `Makefile`. Listed by extension in
`add_templates.py`'s `DECLARATION_FORMS`, and guarded in both directions by
`tests/test_declaration_forms.py`: no greeting is required, and no `main` is
allowed.

**Real template** — whether the generator has a program for a language, as
opposed to emitting an admission. Recorded per file in the manifest as
`real_template`, and asserted to agree with `program_for()` by
`scripts/check_templates.py` for all 7,326 files.

**Byte share** — the percentage of the layer's bytes a file is given. Equal
across the core layer by construction, and padded to by
`scripts/balance_bytes.py`. It is a *share*, not a size: two files with equal
share in the same layer end up the same length, which is why the padding is
measured on disk rather than summed from the manifest.

**Runner** — the command that executes a file, containing `{file}`. Null for
6,180-odd languages, because CI does not have their toolchains. A runner that
exists must mention the file it runs; four that did not are E34.

## The four senses at a glance

| sense | owned by | lives in |
|---|---|---|
| layer | this repository | `path`, `layer` |
| type | Linguist | `type` |
| kind | this repository | `placeholder_classes.json` |
| segment | GitHub's renderer | nowhere here — measured with Linguist |

Only the first three are in the manifest. The fourth is GitHub's, which is why
`scripts/extension_collisions.py` counts how much is at stake in a manifest
whose extensions 117 of them do not uniquely identify, and refuses to guess
which language wins.