# Agent state

Last updated: 2026-10-17

## Current state

| | |
|---|---|
| HEAD | see `git rev-parse --short HEAD` |
| Branch | `main`, in sync with `origin/main` |
| Core layer | 694 languages, each exactly 2048 bytes |
| Full layer | 6 632 files |
| Total | 7 326 files, 7 326 unique languages |
| Byte share | 0.144092 % each, summing to exactly 100.000000 % |
| Segments GitHub renders | 631 (Linguist folds dialects) |
| Programs | 1 663, of which 1 568 are curated templates and 95 inherit |
| Core coverage | 692/694 (99.7 %) |
| Full coverage | 891/6 632 (13.4 %) |
| Remaining backlog | **336** files, all `kind=program` |
| Tests | 72, run by `scripts/run_tests.py`, all in CI |
| Acceptance | 19/19 |
| Demo | 4.9 MB GIF, 29.5 s, 8.10 % mean motion, 28.9 % frozen |

Run `python scripts/coverage_figure.py` for those numbers. Do not type them: the
last forty times they were typed they were wrong, because they were written before
the batch had been applied (logs/ERRORS.log, E32).

The backlog is 336, not 6 200. The other 5 409 program-less files are 3 279
esoteric languages with no canonical program, 2 098 Wikipedia article titles that
are not languages at all, 47 documents and 9 binary formats. See
`docs/HOW-FILES-GET-THEIR-CONTENT.md`.

## Commands that matter

```bash
python scripts/coverage_figure.py       # every number above, measured
python scripts/run_tests.py             # 72 tests
python scripts/verify_languages.py      # 19 acceptance checks
python scripts/validate_delivery.py     # workflow, layout, generators, exec bits
python scripts/check_templates.py       # template correctness
python scripts/classify_placeholders.py # the five kinds, and --check
python scripts/language_table.py        # data/LANGUAGES.md, and --check
python scripts/check_demo_motion.py     # is the recording moving?
python scripts/inspect_frames.py        # what is on screen? (contact sheet)
python scripts/verify_encodings.py      # do the hex dumps decode back?
python scripts/hue_uniformity.py        # is the bar actually a rainbow?
python scripts/audit_repo.py            # health report
bash run.sh                             # the show
bash scripts/record_demo.sh             # record + tune + transcode
```

## Adding programs

Batches go through one tool, because editing a 1 500-entry dictionary by hand is
how `HELLO["coff"] = ""` came to count as a template:

```bash
python scripts/add_templates.py --from .tmp/batch.json --dry-run
python scripts/add_templates.py --from .tmp/batch.json
python scripts/add_templates.py --from .tmp/batch.json --replace   # corrections
```

The tool regenerates, rebalances, runs the template guard and runs the tests. It
also refuses languages that are not in the manifest, blank programs, and programs
that never say "Hello World" — and it is right to refuse. Roughly one entry in
five is rejected, usually because the file is a good answer to a slightly
different question.

## Toolchain

Not on PATH; invoke by absolute path:

- git `D:\Git\cmd\git.exe`
- bash `D:\Git\bin\bash.exe`
- python 3.13 `C:\hclaw\python\python.exe`
- python 3.12 (matches CI) `D:\DevEnv\python\python.exe`
- ffmpeg (local experiments only) `D:\JianyingPro\11.2.0.14339\ffmpeg.exe`

## Environment hazards

- **PowerShell will corrupt UTF-8.** `Set-Content` / `Out-File` round-trip text
  through the console code page and destroy emoji and non-Latin characters.
  Write files with Python or the edit tool. `Add-Content` also appends CRLF,
  which `tests/test_clean_checkout.py` rejects for tracked text files.
- **PowerShell pipelines append `\r` to the last line.** `"a`nb" | git ...`
  sends `b\r`, so `git check-ignore --stdin` appears to ignore nothing when the
  interesting path is last. Put a sentinel line after it.
- **A pipeline hides an exit code.** `cmd | Select-Object -First 1` makes
  `$LASTEXITCODE` the pipeline's, not the command's.
- **`git push` needs the proxy at 127.0.0.1:10818.** When the VPN is down every
  push fails. `.tmp/push_retry.py` retries in the background and rebases first,
  because the CI jobs commit regenerated assets to `main`.
- **The network here drops for minutes at a time.** Work locally and let the
  pusher catch up; do not stall on a push.
- The repo is owned by a different SID; `git config --global safe.directory` was
  required.
- `scripts/__pycache__` is owned by another SID; compile with `compile()` rather
  than `py_compile`.

## The three most expensive defects, and what they have in common

1. **A crash behind a TTY guard** (E31). Every local invocation pipes stdout, so
   every local run took the other branch. Only the recorder ran the line.
2. **Four language files in no clone** (E30). `.gitignore` matched `*.bundle` and
   `*.obj`. Five checks agreed the files were present and all five read the
   working tree.
3. **One stray byte breaking 23 of 24 shards** (E30). A BOM plus one CRLF in a
   file `.gitattributes` marks as LF text, so every checkout rewrote it.

And the lesson is not a list of causes. It is that **a check which reads the
working tree cannot tell you what is committed, and a test that pipes its output
cannot tell you what a TTY-only branch does.** A fresh clone, a real terminal and
an actual frame of the output are all things worth going and looking at.

There is now a guard for each: `tests/test_gitignore_safety.py`,
`tests/test_clean_checkout.py`, `tests/test_shell_variables.py`,
`scripts/check_demo_motion.py`.

## Ledgers

- `logs/ERRORS.log` — every defect found, E1–E32
- `logs/DECISIONS.md` — decisions and their reasoning
- `logs/AGENT_STATE.md` — this file
