# How a file in `hello/` gets its content

This is the short version. There are 7 326 files. 1 576 carry a real Hello World
program. The rest carry something else, and *what* they carry is decided by a
measurement rather than by taste.

## The question, and the answer to it

"Can this language print?" is the wrong first question. The right one is **"does
this language have anywhere to put a greeting?"**, and that has five answers, not
two.

| kind | count | what the file holds |
|---|---:|---|
| `program` | 432 | a real program; this is the backlog |
| `esolang` | 3 280 | an admission that no canonical program is written down |
| `unknown` | 2 099 | an admission that the entry is an index, not a language |
| `document` | 47 | a real document whose content is the greeting |
| `binary` | 9 | the format's magic number and where the greeting would be |

`scripts/classify_placeholders.py` computes that table into
`data/placeholder_classes.json`, and the generator reads it. So the five answers
are five sentences in `build_file()`, chosen per file rather than picked by hand.

The `unknown` bucket is the one worth reading. 1 747 of those files came from a
Wikipedia scrape and are article titles — "Aidan Gomez", "CAP theorem",
"University Courses". They are counted as languages by the language bar and they
cannot have a Hello World, because they are not languages. Saying so is the
correct answer.

## Adding a program

Programs are added in batches through one tool, which exists because editing a
1 500-entry dictionary by hand is how `HELLO["coff"] = ""` happened.

```bash
# .tmp/batch.json:  {"Fortran 77": "      PROGRAM HELLO\n...", ...}
python scripts/add_templates.py --from .tmp/batch.json --dry-run
python scripts/add_templates.py --from .tmp/batch.json
```

It refuses, with a reason, any batch containing:

- a language the manifest does not list — a program for a language this repository
  does not ship is a program nobody can check;
- a blank program — the `coff` defect, by name;
- a program that never says "Hello World", unless the extension is a
  declaration form, where the fields are the answer.

Then it regenerates, rebalances the bytes, runs the template guard and runs the
tests, so a batch that would break an invariant fails on your machine rather than
in CI.

`--replace` overwrites an existing template when the text differs, and reports
"identical" when it does not, so re-running a batch is not an empty commit.

## The bar

Every language whose extension has no bare-name collision is exactly 2 048 bytes,
so every one is 0.144092 % and the shares sum to exactly 100.000000 %. A program
of any length is padded with `rainbow-pad` comments to reach that. This is the
whole mechanism, and it is why the README's figures can be quoted exactly.

## What "real" means here

A program has to be the one that language's own documentation, test suite or
reference implementation contains. Not something that would compile. Not
something that looks plausible.

Three times this has been load-bearing:

- 34 of 156 heuristic template matches were wrong, and inheritance became an
  explicit allowlist (`logs/ERRORS.log`, E25);
- a microcontroller with no display cannot print, so a PIC16 entry that never
  greets was refused rather than faked;
- a hex dump written from memory is a hex dump that is wrong in one byte, so
  every archive in `hello/full/` was re-encoded by the library that defines the
  format.

A wrong program is worse than an honest admission, because it looks like work.
