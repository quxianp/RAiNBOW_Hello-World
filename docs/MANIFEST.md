# `hello/manifest.json`

One file per tracked Hello World, and the only description of this repository
that anything else reads. The generator writes it, the bar renderer colours
from it, the coverage figure counts it, the acceptance checks compare against
it, and `scripts/classify_placeholders.py` reads its siblings to decide what to
say about the files that have no program.

It is therefore the most load-bearing file in the repository and the one with
the fewest readers, so this is what it contains and which of its fields are
allowed to be empty.

## Shape

```json
{
  "generated": "…ISO 8601…",
  "repo": "https://github.com/quxianp/RAiNBOW_Hello-World",
  "files": [ { …one object per file… } ]
}
```

`files` has one entry for each of the 7,326 files, in the order they were
generated. Order is not significant; the path is the key.

## One entry

```json
{
  "path": "hello/core/python/hello.py",
  "language": "Python",
  "layer": "core",
  "extension": ".py",
  "type": "programming",
  "color": "#3572A5",
  "hue": 210.0,
  "share": 0.1441,
  "modeline": "vim",
  "runner": "python3 \"{file}\" || python \"{file}\"",
  "real_template": true
}
```

| field | meaning | may be null |
|---|---|---|
| `path` | the file, relative to the repository root | no |
| `language` | Linguist's name for it | no |
| `layer` | `core` or `full` | no |
| `extension` | Linguist's extension, which may be compound (`.js.erb`) | no |
| `type` | Linguist's classification: `programming`, `markup`, `prose`, `data` | **yes** |
| `color` | Linguist's colour, `#rrggbb` or `#rgb` | **yes** |
| `hue` | that colour's HSV hue in degrees, computed | **yes** |
| `share` | percent of the layer's bytes this file is given | no |
| `modeline` | Linguist's name for the modeline the language uses | **yes** |
| `runner` | the command that runs the file, with `{file}` | **yes** |
| `real_template` | whether the generator has a program for it | no |

## The three fields that are allowed to be empty

**`type` is null for 6,490 files.** Linguist does not classify them at all —
they are esolangs, esoteric file formats and entries that exist only because
somebody wrote a `.snippet` file once. That is not a missing value, it is the
honest one. A generator that filled it in would be inventing a classification
Linguist does not make.

**`color` and `hue` are null for languages Linguist has no colour for.** About
142 of them. Where a colour exists, the hue is computed from it rather than
chosen, and `scripts/check_manifest.py` recomputes it and fails if the two
disagree — because the bar is drawn from those two fields and nothing else, so a
mismatch is a wrong pixel everywhere at once and visible in no way.

**`modeline` and `runner` are null when there is nothing to record.** A language
with no modeline has no `modeline`. A language with no toolchain installed in CI
has no `runner` — and when it does have a `runner`, that runner must mention
`{file}`. It used to be allowed not to: four entries were the bare string
`echo "Hello World!"`, which runs nothing, and the manifest asserted a runner
for four languages that were never executed. That is E34.

## `share`, and why it has to be exactly 100

The core layer's 694 files are given equal byte shares, and the sum of those
shares is 100. Equal bytes means equal slices on GitHub's language bar, which is
the entire visual premise of the repository — the rainbow is the bar, and a bar
with one fat slice and 693 hairlines is not a rainbow.

`scripts/balance_bytes.py` computes the padding that gets each file to its share
and writes `logs/balance_summary.json`. `scripts/audit_repo.py` re-derives the
equal-size invariant from disk rather than from the manifest, because the
manifest cannot be the thing that checks itself: a broken generator would agree
with itself perfectly.

## Compound extensions

`extension` is Linguist's, not `pathlib.Path.suffix`. For `hello.js.erb`
Linguist's extension is `.js.erb` and `suffix` returns `.erb`, which is the
other half of the same trap as `Path("hello.intel_hex").stem` returning
`"hello"`. `check_manifest.py` therefore requires the recorded extension to be a
suffix of the filename *and* the longest such extension the manifest records for
that file — which rejects both a wrong-short extension and a made-up one.

## Regenerating it

```sh
python scripts/generate_all_hello.py     # writes hello/ and the manifest
python scripts/balance_bytes.py          # re-tunes share, then re-writes it
python scripts/check_manifest.py         # the manifest against the files
```

Never edit the manifest by hand. It is overwritten on the next generation, and
`tests/test_generated_files.py` fails when it is stale.

## Reading it

```sh
python scripts/coverage_figure.py --json     # the counts
python scripts/language_report.py            # by Linguist type
python scripts/extension_collisions.py       # extensions nobody owns alone
python scripts/check_manifest.py --verbose   # every field, every entry
```

The last one is the most useful and the least used.