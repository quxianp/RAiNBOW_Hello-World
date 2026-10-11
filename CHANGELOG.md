# Changelog

All notable changes to RAiNBOW_Hello-World are recorded here.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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