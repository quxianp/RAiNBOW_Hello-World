# Changelog

All notable changes to RAiNBOW_Hello-World are recorded here.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **A test suite**: `scripts/run_tests.py` plus 41 tests, run in CI on every
  push. Standard library only -- adding a test framework to the acceptance job's
  dependency set would give one more thing that can turn the gate red for reasons
  unrelated to the repository.
  - `test_bar_invariants.py` -- the equal-size property, checked against the
    filesystem rather than the manifest, because a broken generator and a
    manifest that agrees with it would pass any manifest-only check
  - `test_encoding.py` -- no CRLF in generated files, no mojibake in any
    markdown file, and the contents strip matching its headings
  - `test_linguist_detectability.py` -- every core language coloured, no two
    sharing a Linguist name, every file carrying a modeline, and the language
    files excluded from line-ending normalisation via `git check-attr`
  - `test_demo_acts.py` -- every demo phase actually produces output
  - `test_readme_claims.py` -- the README's numbers match the repository
  - `test_script_hygiene.py` -- scripts compile, are documented, and their usage
    examples name flags that exist
- `scripts/audit_repo.py`, `check_readme_links.py`, `check_docs_links.py`,
  `check_templates.py`, `language_report.py`, `render_ascii_bar.py`,
  `spectral_sweep.py`, `measure_motion.py`, `update_readme_coverage.py`,
  `spotcheck_templates.py`.
- **~870 curated Hello World programs**, taking core-layer coverage from
  26.1 % to **99.7 %** -- 692 of 694 files now carry real code rather than a
  placeholder. The two that do not are ambiguous by extension (Rez shares
  `.r` with R) and are left honest on purpose.
- A spectral sweep in `run.sh` in which every column is coloured with the real
  Linguist colour of one of the 694 core languages, read from the same config
  that orders the bar -- so a missing language would show as a gap in it.
- `assets/ascii-bar.txt`: the bar as terminal art, for readers in a clone rather
  than a browser.
- Repository About panel, 20 topics, discussions, labels, CODEOWNERS,
  `scripts/configure_repo.ps1`, milestone and release v2.0.0.
- `docs/ARCHITECTURE.md`, `docs/WHY-631-NOT-694.md`, `docs/FAQ.md`,
  `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `.editorconfig`,
  issue and pull-request templates.

### Fixed
- **The animated hold drew nothing at all.** `rainbow.py --sweep-only` returned
  before rendering, and the `--sweep` branch required flags `run.sh` never
  passes. The command exited 0 having written zero bytes, so the last 8.7 s of a
  37.4 s recording was a frozen still and nothing failed. Found by measuring
  frame-to-frame motion rather than by watching.
- **The generator invented languages.** Matching templates on the first word of
  a name or its extension gave JASS and Objective-J a shell `echo`, and
  `Go Module` an entire Go program. 34 of 156 matches were wrong; inheritance is
  now an explicit 96-entry allowlist, and `check_templates.py` enforces it.
- **CRLF in seven generated JSON files**, including a `hello/manifest.json` with
  all 81 290 lines CRLF, because `write_text` was called without `newline="\n"`
  and `* -text` means nothing normalises them on the way in.
- **A README destroyed by a code-page round trip.** Editing one number with
  PowerShell's `Set-Content` corrupted every emoji and silently broke three
  table-of-contents anchors. `update_readme_coverage.py` now owns that figure so
  the edit never goes through a console.
- **Placeholders did not admit they were placeholders.** `build_file()` takes its
  note through a parameter core files were already using for the modeline
  caption, so all 6 262 placeholder files opened with "Pinned with a Linguist
  modeline" and never said they had no program.
- **`HELLO["coff"] = ""` counted as a template.** COFF was marked as having a
  curated program and generated as a banner followed by nothing -- while the
  manifest agreed with the generator, the file was the right size, and all 19
  acceptance checks passed. `program_for()` now requires a non-blank value.
- Eight dead TOC links; the Linguist audit printing `1.0100 %` where the API
  reports `1.0116 %`; a template guard that matched its own explanatory comment.

## [2.0.0] - 2026-10-11

### Added
- **The bar is a rainbow.** 694 core languages, one per Linguist-coloured and
  detectable language, ordered by hue, each padded to exactly 2048 bytes so the
  share is an identical 0.144092 % and the sum is exactly 100.000000 %.
- `scripts/render_github_bar.py` draws the bar from `GET /repos/.../languages`
  and lists **all 631** languages by name with their real share.
- `scripts/generate_hero_banner.py` renders the README banner with counts read
  live from the repository, so it cannot drift.
- `scripts/update_readme_showcase.py` writes a 58-language "hall of fame" table
  from `data/linguist.json` and `hello/manifest.json`.
- `scripts/screenshot_github.py` captures GitHub's Languages panel with
  Playwright, rejecting any capture under 6 KB as degenerate.
- `scripts/linguist_audit.rb` runs GitHub's own `github-linguist` gem and
  records the authoritative breakdown.
- `scripts/modeline_ab_test.rb` measures whether the per-file modelines gain or
  lose language segments.
- `scripts/validate_delivery.py` checks the workflow, the layout, the exec bits,
  the animation wiring, and runs the README generators.
- Daily `schedule` trigger, so the pipeline refreshes itself unattended.

### Fixed
- `run.sh`, `install_deps.sh` and `scripts/record_demo.sh` are committed
  `100755`. They were `100644`, so every recorded demo ended on
  `bash: ./run.sh: Permission denied`.
- `rgb()` emitted `ESC 38;2;R;G;Bm` with no `[`, so the "rainbow" greeting was
  never actually coloured.
- The intro computed a hue per character and then discarded it, painting the
  banner pure white.
- `run.sh` passed `--bar`/`--hello`, which disabled every animated code path in
  `scripts/rainbow.py`, so the recording could not move at all.
- The animated hold sat after `exit 0` and never ran, leaving the back half of
  every recording frozen.
- The VHS release tarball is nested, so `tar -xzf ... vhs` failed.
- The GIF optimiser wrote to `*.gif.opt`, and ffmpeg cannot infer a muxer from
  that, so the step failed silently for several runs.
- Generated artefacts were written with platform line endings while
  `* -text` disabled normalisation, churning `hello/manifest.json` by 81 290
  lines per cross-platform run.
- `Path.read_text(newline=...)` is Python 3.13+; the workflow pins 3.12, which
  killed the acceptance job.

### Measured
- 19/19 acceptance checks, on Python 3.13.12 and 3.12.7.
- 7 326 language files: 694 core, 6 632 full.
- 631 languages live on GitHub's bar, which is the ceiling: the modeline A/B
  shows the remaining 63 names are folded by Linguist regardless of annotation.

## [1.0.0] - 2026-10-01

### Added
- Initial two-layer structure: `hello/core/` for the bar and `hello/full/` for
  the vendored long tail.
- Multi-source language harvesting and merging into `data/merged_langs.json`.
- Byte balancing and the 19 acceptance checks.

[Unreleased]: https://github.com/quxianp/RAiNBOW_Hello-World/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/quxianp/RAiNBOW_Hello-World/releases/tag/v2.0.0
[1.0.0]: https://github.com/quxianp/RAiNBOW_Hello-World/releases/tag/v1.0.0