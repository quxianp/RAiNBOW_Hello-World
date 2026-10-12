# Architecture

How the pieces fit together, and which decisions are load-bearing.

## The one idea

GitHub colours a repository's language bar by **byte share**. Every language that
appears is a slice of a 100 % pie. So to control the bar, you control byte
counts:

- one core language present ⇒ one coloured segment, sized by its bytes;
- all core files **exactly the same size** ⇒ all segments exactly equal;
- core files **ordered by hue** ⇒ the bar reads as a spectrum rather than
  confetti.

Everything else in this repository exists to make those three sentences true.

## Layers

```
hello/core/<slug>/     694 files, exactly 2048 bytes each  -> the bar
hello/full/<slug>/     6 632 files, vendored              -> breadth, not the bar
config/                                               -> inputs to the generators
data/                                                  -> harvested language inventories
scripts/                                               -> generators + gates
logs/                                                  -> evidence and ledgers
assets/                                                -> rendered media
```

### Why two layers

A file only enters `hello/core/` if **all three** hold:

1. Linguist assigns it a **colour** — 142 languages have none (COBOL among them)
   and a colourless language cannot appear on a colour bar at all;
2. Linguist can **detect** it from the file alone;
3. `include_in_language_stats` can be forced on, because Linguist's default
   `types` only counts `programming` and `markup`, while 124 of our core
   languages are `data` or `prose`.

`hello/full/` holds everything else. It is vendored, so it is not regenerated,
and it is **excluded from the bar** via `.gitattributes`.

### Why 2048 bytes

Fixed size ⇒ exactly equal shares ⇒ `1/694 = 0.144092 %` each, summing to exactly
100 %. The number 2048 is arbitrary; exactness is not. It also comfortably fits
the largest modeline and banner in the inventory.

## The 694 → 631 gap

The repository contains 694 coloured, detectable languages. **GitHub's bar shows
631.**

Linguist merges dialect names into their parent language — among others, the 7
HTML-family files (`html`, `handlebars`, `haml`, …) collapse into a single `HTML`
segment of exactly 7 × 2048 = 14 336 bytes. That is why `HTML` reads **1.0116 %**:
1.0116 ≈ 7 × 0.144092.

This was **measured, not assumed**. `scripts/modeline_ab_test.rb` runs Linguist
over the repository twice — once with the per-file modelines, once with them
stripped — and both runs report 631 languages. 63 names are folded regardless of
how the files are annotated. The modelines are kept anyway: they are neutral, and
they make each file self-describing.

`logs/linguist_audit.json` is the authoritative record, produced by CI from the
`github-linguist` gem itself.

## Pipeline

```
fetch_languages.py      -> data/*.json          (harvest)
merge_language_sources.py -> data/merged_langs.json
select_rainbow_langs.py   -> config/rainbow_langs.json, core-langs.txt
generate_all_hello.py      -> hello/core/**       (write files)
balance_bytes.py           -> hello/core/**       (pad to 2048)
verify_languages.py        -> 19 acceptance checks
render_* / record_demo.sh  -> assets/            (media)
validate_delivery.py       -> repo gate
```

Generators write; nothing hand-edits `hello/core/`. `CONTRIBUTING.md` says so and
explains why (CI reverts it).

## Gates

| Gate | Catches |
|---|---|
| `verify_languages.py` | counts, equal shares, sum = 100 %, detection |
| `validate_delivery.py` | workflow shape, layout, exec bits, animation wiring, generators |
| `audit_repo.py` | equal-size invariant re-derived from disk, asset sanity |
| `check_readme_links.py` | broken image paths, dead TOC anchors |

All are offline and deterministic. The only network-dependent step is the bar
render, which reads `GET /repos/.../languages`.

## Known limits

- **The legend cannot name 631 languages.** GitHub collapses the tail into one
  grey *Other* row. Unfixable from the repository side, which is why
  `assets/rainbow-bar-github.png` is rendered from the API with every language
  named.
- **GitHub's language panel is edge-cached.** It can show a stale breakdown. The
  API is authoritative; see `logs/ERRORS.log`.
- **Only 7.1 % of core files can actually run.** A curated program is not the
  same as a runnable one: most are correct for their language but need an
  interpreter this repository does not install.
- **Templates are keyed on language name, never inferred.** Inheritance is an
  explicit allowlist (`INHERIT`) because the first matcher, which fell back to
  first-word and extension matching, gave JASS a shell `echo` and `Go Module` an
  entire Go program. See `logs/ERRORS.log` E25.
- **One core language has no template and is meant not to.** Rez shares its `.r`
  extension with R, and the right program depends on which language is meant, so
  it carries the honest placeholder. See E29.