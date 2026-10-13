# Agent state

Last updated: 2026-10-13

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
| Curated templates | 1 084; 692 of 694 core files (99.7 %) |
| Tests | 56, run by `scripts/run_tests.py`, all in CI |
| Acceptance | 19/19 |
| Demo | 4.9 MB GIF, 29.5 s, 8.10 % mean motion, 28.9 % frozen |

The last figure is the one worth watching. It was 1.79 % with 84 % of
transitions frozen while every step of the build reported success — see
`logs/ERRORS.log`, E31. `scripts/check_demo_motion.py` now fails the build
before such a file can be committed.

## Commands that matter

```bash
python scripts/run_tests.py            # 56 tests
python scripts/verify_languages.py     # 19 acceptance checks
python scripts/validate_delivery.py    # repo gate
python scripts/check_templates.py      # template correctness
python scripts/check_demo_motion.py    # is the recording actually moving?
python scripts/audit_repo.py           # health report
bash run.sh                            # the show
bash scripts/record_demo.sh            # record + tune + transcode
```

## Toolchain

Not on PATH; invoke by absolute path:

- git `D:\Git\cmd\git.exe`
- bash `D:\Git\bin\bash.exe`
- python 3.13 `C:\hclaw\python\python.exe`
- python 3.12 (matches CI) `D:\DevEnv\python\python.exe`
- ffmpeg (local experiments only; CI installs its own) `D:\JianyingPro\11.2.0.14339\ffmpeg.exe`

## Environment hazards

- **PowerShell will corrupt UTF-8.** `Set-Content` / `Out-File` round-trip text
  through the console code page and destroy emoji and non-Latin characters.
  This corrupted README.md once already. Write files with Python or the edit
  tool, never with `Set-Content`. It also appends a BOM and CRLF endings, which
  `tests/test_clean_checkout.py` will now reject for any tracked text file.
- **PowerShell pipelines append `\r` to the last line.** `"a`nb" | git ...`
  sends `b\r`, so `git check-ignore --stdin` appears to ignore nothing when the
  interesting path is last. Put a sentinel line after it.
- **PowerShell `>` writes UTF-16 with a BOM.** Use `git cat-file -p` through
  Python's `subprocess` when you need to inspect committed bytes.
- **A pipeline hides an exit code.** `cmd | Select-Object -First 1` makes
  `$LASTEXITCODE` the pipeline's, not the command's. Write to a file, or check
  inside a single command.
- **`git push` needs the proxy at 127.0.0.1:10818.** If the proxy is down,
  every push fails; the work is safe locally and can be pushed later. Retry —
  the VPN drops for a few seconds at a time and often recovers on attempt two.
- **CI commits to `main`.** The assets and batch jobs push regenerated files, so
  `git pull --rebase` before every push or the push is rejected as non-fast-
  forward.
- The repo is owned by a different SID; `git config --global safe.directory` was
  required.
- `scripts/__pycache__` is owned by another SID; compile with `compile()` rather
  than `py_compile`.

## Things that have gone wrong here, in order of cost

1. **A crash that four statistics could not see.** `run.sh` read an undefined
   `$FAST` behind a `[ -t 1 ]` guard, so only the recorder ever ran it, and the
   published GIF was a crash report with a still frame behind it. Reading the
   pixels found it in one step; measuring them had already cost three commits.
   Guarded now by `tests/test_shell_variables.py`.
2. **A file that existed in no clone.** `.gitignore` matched `*.bundle` and
   `*.obj`, which are also language extensions. Five checks agreed the file was
   present and all five read the working tree. Guarded by
   `tests/test_gitignore_safety.py`.
3. **One stray byte breaking 23 of 24 shards.** A BOM plus one CRLF in a `.ps1`
   file that `.gitattributes` marks as LF text, so every checkout rewrote it and
   `git pull --rebase` refused. Guarded by `tests/test_clean_checkout.py`, which
   makes a real clone.

All three shared a shape: every local check was green, and the failure only
existed in a place local checks do not look. A fresh clone, a real terminal, and
an actual frame of the output are all things worth going and looking at.

## Ledgers

- `logs/ERRORS.log` — every defect found, E1–E31
- `logs/DECISIONS.md` — decisions and their reasoning
- `logs/AGENT_STATE.md` — this file
