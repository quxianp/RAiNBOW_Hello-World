# Changelog

All notable changes to RAiNBOW_Hello-World are recorded here.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0] - 2026-10-17

The day the repository started checking its own claims. Everything below was
found by a tool that was added to find it, and four of the findings were real
defects in files that every other check passed.

The largest of those is `hello/manifest.json`. It is the most load-bearing file
here -- the generator writes it, the bar renderer colours from it, the coverage
figure counts it -- and nothing checked it. Four of the 7,326 entries carried a
`runner` field whose entire command was `echo "Hello World!"`: a field asserting
that a language could be run, in a manifest, for four languages that were never
executed. See `logs/ERRORS.log` E34.

### Added
- **`scripts/check_manifest.py`** -- asserts the manifest describes the
  repository that is on disk: every path exists, its layer matches its directory,
  its extension is the one on disk, its modeline is a name `languages.yml`
  defines, its runner mentions the file it runs, and **its hue is the hue of the
  colour beside it, recomputed**. That last one matters because the bar is drawn
  from those two fields and nothing else, so a mismatch is a wrong pixel
  everywhere at once and visible in no way.
- **`scripts/build_object_formats.py`** -- builds COFF, DWARF, WCS, SHP, TIFF,
  SHPFFIL and FlatGeobuf from their specifications' own field widths. A header
  is a dozen fields in a specified order and transcribing one produces a file
  that is wrong in exactly one byte and looks identical to a correct one. Two of
  the seven have somewhere to put the greeting -- TIFF's ImageDescription and a
  FITS COMMENT card -- and five do not, and say so.
- **Six structure checkers in `scripts/verify_encodings.py`**, one per object
  format, reading the fields by name. The FITS one requires `=` in column 9 of
  every card; moving it one column left changes no byte count and no hex token
  and is caught by nothing else in the suite.
- **`scripts/extension_collisions.py`** -- 117 extensions are claimed by more than one
  language. Linguist gives both R and Rez the extension `.r`, so the manifest
  has two files claiming it and GitHub counts both as R. The tool measures how
  much is at stake and refuses to say which language wins, because that is
  Linguist's answer and not this repository's.
- **`scripts/check_doc_figures.py`** -- resolves every figure quoted in the
  prose against the tool that measures it. It found four checkable figures in
  the documentation, all four correct; the stale ones live in commit messages,
  which is exactly why it can only be a regression guard.
- **`Makefile`**, and `scripts/make_help.py`, because there were 45 scripts and no index.
- **`docs/MANIFEST.md`**, and 17 family guides under `docs/languages/`,
  each covering a family where the obvious template is wrong in a way that passes
  every automated check.
- **`SECURITY.md`**, **`CODE_OF_CONDUCT.md`**, **`.github/dependabot.yml`**.

### Fixed
- **The demo ends on the greeting.** `--force-hold` was checked *after* the
  sweep rather than before it, so the hold could fire past the deadline and the
  recording finished on an empty screen.
- **A comment that names a magic number is not the magic number.** The
  FlatGeobuf file's preamble says "the magic is 0A 0D 0D 0A", and the verifier
  read the explanation as the magic: it reported version 10, which is 0x0A. A
  dump line is now identified by its ASCII gutter.
- **Re-applying an unchanged batch is a no-op, not a failure.** `add_templates.py`
  exited 1 on a batch whose content was already present, which reads as "the fix
  did not work" to anything reading the exit code.
- **A round floor for six formats with four different minimum lengths** skipped
  every small object file it had been written for.

### Changed
- **1,814 programs** across 7,326 files (694 of 694 core, 99.7 %),
  from 1,070 when this began. Every one added by a batch that had to pass the
  template guard, which is what rejected a Rez template that could not be
  honest.
- **The suite is 103 tests** in 19 files, standard library only.

### Defects recorded
- `logs/ERRORS.log` now runs to E34. The four newest share a shape worth naming:
  **a claim that costs nothing to check and that nobody checked** -- a file in
  no clone (E30), a variable read under `set -u` behind a guard no local run
  reached (E31), a figure typed instead of measured (E32, E33), and a runner that
  never ran anything (E34).

[330 commits]

## [2.1.0] - 2026-10-17

The day the demo stopped lying. The GIF had been frozen for 22 of its 33 seconds
for several commits, and every signal the build had said it was fine: the
recording succeeded, the encoder succeeded, the file was a plausible four
megabytes, the run log ended with `run.sh done`.

It was frozen because `run.sh` was crashing at line 279. `measure_motion.py`
reported "367 of 418 transitions frozen" and could not say why -- coverage tells
you that nothing changed, and only a picture tells you that something changed
into an error message. Three commits were spent shortening a sleep before anyone
extracted a frame and read it.

### Added
- **A gate that refuses to publish a demo which does not move.**
  `scripts/check_demo_motion.py` runs after the recording and before the assets
  are committed, so a static take never reaches `main`. Two independent checks:
  frozen transitions at or below 50 % (the same boundary `measure_motion.py`
  already calls "monotonous") and mean coverage at or above 3 % to catch drift.
  A missing GIF exits 0, so a VHS CDN outage still cannot block the pipeline.
- **`scripts/inspect_frames.py`** -- a contact sheet of frames across the
  runtime. This is the tool that found the crash: nine tiles in one image showed
  the error text mid-frame, a blank screen at 14.9 s, and a blank final screen,
  none of which any statistic had objected to.
- **`scripts/classify_placeholders.py`** and `data/placeholder_classes.json`,
  which sort every program-less file into one of five kinds that need five
  different answers, and every file now says which one it is.
- **`scripts/add_templates.py`**, which adds a batch of programs safely and
  refuses a blank one, a duplicate, a language this repository does not ship, and
  anything that never says "Hello World" -- unless its extension is a declaration
  form, where the fields are the answer.
- **`scripts/verify_encodings.py`**, which decodes about seventy encoding files
  back to the greeting rather than trusting them.
- **`scripts/coverage_figure.py`**, because the coverage number was typed forty
  times and was wrong forty times.
- **`scripts/language_table.py`** and `data/LANGUAGES.md`: all 7 326 files,
  grouped by what they contain rather than by directory.
- **`scripts/hue_uniformity.py`**: the rainbow claim, measured. 655 chromatic
  core languages, ideal hue gap 0.55 deg, mean 0.55 deg, largest 9.93 deg.
- **`docs/DEMO.md`**, `docs/ENCODINGS.md`, `docs/HOW-FILES-GET-THEIR-CONTENT.md`.
- 19 tests, 72 in the suite, all standard library.

### Fixed
- **The show was crashing on every recorded run**, for the reason above.
  `$FAST` was read and never assigned, behind a `[ -t 1 ]` guard that no local
  invocation ever reached. Guarded now by `tests/test_shell_variables.py`, which
  answers the whole class statically.
- **Four language files existed in no clone.** `.gitignore` matched `*.bundle`
  and `*.obj`, which are also language extensions. Five checks agreed the files
  were present and all five read the working tree.
- **One stray byte broke 23 of 24 CI shards.** A BOM plus one CRLF in a `.ps1`
  file that `.gitattributes` marks as LF text, so every checkout rewrote it and
  `git pull --rebase` refused to run.
- **The closing hold spun for ten seconds drawing one frame**, guarded twice: on
  `[ -t 1 ]` in the shell and on `sys.stdout.isatty()` in Python.
- **6 035 placeholders said nothing specific.** Each now names its kind, its
  Linguist groups and where the entry came from.
- **The recording ended on a blank screen**, because the hold's deadline was
  tested after the work rather than before it.
- The GIF encoder is chosen by measurement: seven settings re-encoded from one
  source, and the winner is both 62 % smaller and more animated than the
  alternative.

## [Unreleased]

### Added
- **A test suite**: `scripts/run_tests.py` plus 59 tests, run in CI on every
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
  - `test_gitignore_safety.py` -- no manifest path is excluded by `.gitignore`,
    asked with `check-ignore --no-index` because the plain form skips tracked
    files and therefore reports a clean bill of health on a broken repository
  - `test_clean_checkout.py` -- makes a real clone and asserts the tree is
    clean, plus a cheap scan for a BOM or CRLF in any tracked text file
  - `test_shell_variables.py` -- every variable `run.sh` reads is assigned
    somewhere in the same file, comment-stripped and quote-aware
  - `test_demo_assets.py` -- the committed GIF is animated, and the gate's own
    thresholds have not been quietly widened
- `scripts/audit_repo.py`, `check_readme_links.py`, `check_docs_links.py`,
  `check_templates.py`, `language_report.py`, `render_ascii_bar.py`,
  `spectral_sweep.py`, `measure_motion.py`, `update_readme_coverage.py`,
  `spotcheck_templates.py`, `update_docs_index.py`, `check_demo_motion.py`.
- **A gate that refuses to publish a demo which does not move.**
  `scripts/check_demo_motion.py` runs after the recording and before the
  assets are committed, so a static take never reaches `main`. The published
  GIF once spent 22 of its 33 seconds frozen while every step of the build
  reported success -- it recorded, it optimised, it produced a plausible
  multi-megabyte GIF, and the run log ended with `run.sh done`.
- An animated cold open in `demo.tape`, so the recording begins with the hue
  sweep rather than a blank screen and a blinking cursor.
- **1 084 curated Hello World programs**, taking core-layer coverage from
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
- **The show was crashing on every recorded run.** `run.sh` read `$FAST`,
  which nothing assigned, and runs under `set -u`. The line sits behind
  `[ -t 1 ]`, so every local invocation -- all of which pipe stdout -- took
  the other branch and passed. Only the recorder, which gives `run.sh` a real
  pty, ever ran it. The published GIF contained
  `run.sh: line 279: FAST: unbound variable` in plain sight, above a still
  image occupying two thirds of the recording. Found by reading a frame
  rather than a statistic about it; `measure_motion.py` could report that
  22 seconds were frozen but not that the frozen thing was a crash report.
- **Four language files existed in no clone.** `.gitignore` matched `*.bundle`
  and `*.obj`, which are also language extensions, so
  `hello/full/bundle/hello.bundle` and two `.obj` files were present on the
  generating machine and absent from every checkout. Five checks agreed they
  were there and all five read the working tree.
- **One stray byte broke 23 of 24 CI shards.** `scripts/publish_release.ps1`
  carried a UTF-8 BOM and a single CRLF while `.gitattributes` marks `*.ps1`
  as LF text, so every checkout rewrote it and the batch job's
  `git pull --rebase` refused to run on a dirty tree.
- **The closing hold spun for ten seconds drawing one frame.** It is guarded
  on `[ -t 1 ]`, false whenever stdout is a pipe, and `rainbow.py` separately
  decided whether to animate from `sys.stdout.isatty()`. Either one alone
  reduced the finale to a still image; `--force-hold` and `--force-animation`
  make both explicit.
- **The GIF encoder was blamed for a crash.** Two commits changed palette and
  resolution looking for a flat gradient, while the thing being flattened was
  an error message. The encoder is now chosen by measurement: seven settings
  re-encoded from one source, best motion per megabyte wins.
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