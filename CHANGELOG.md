# Changelog

All notable changes to RAiNBOW_Hello-World are recorded here.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `scripts/audit_repo.py` — repository health report. Re-derives the equal-size
  invariant from disk rather than trusting the manifest, and checks that every
  asset the README embeds exists and is non-degenerate.
- `scripts/check_readme_links.py` — catches broken image paths and dead TOC
  anchors. External links are counted but not fetched, to keep the gate offline.
- `scripts/check_docs_links.py` — the same, for every markdown file, resolving
  relative links against the document that contains them.
- `scripts/language_report.py` — inventory by Linguist type, plus template and
  runner coverage.
- `scripts/generate_hero_banner.py` and `assets/hero-banner.png` — the README
  banner, with counts read live from the repository.
- `scripts/update_readme_showcase.py` — a 58-language table generated from
  `data/linguist.json` and `hello/manifest.json`.
- `docs/ARCHITECTURE.md`, `docs/WHY-631-NOT-694.md`, `docs/FAQ.md`,
  `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `.editorconfig`,
  issue and pull-request templates.

### Fixed
- Eight dead table-of-contents links. Anchors were hand-written with
  percent-encoded emoji, but only one heading contained an emoji; two were also
  wrong in substance, conflating 7 326 files with 7 325 distinct languages.
- The Linguist audit printed `1.0100 %` where the API reports `1.0116 %`. It was
  reprinting Linguist's rounded two-decimal value at four decimals. An audit that
  disagrees with the thing it audits trains people to ignore it.
- `update_readme_assets.py` shipped with an invalid f-string placeholder and died
  on every invocation. `validate_delivery.py` now *runs* the generators instead
  of grepping them, so that class of bug cannot ship again.

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