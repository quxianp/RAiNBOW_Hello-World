# Agent state

Last updated: 2026-10-13

## Current state

| | |
|---|---|
| HEAD | see `git rev-parse --short HEAD` |
| Branch | `main`, in sync with `origin/main` |
| Core layer | 694 languages, each exactly 2048 bytes |
| Full layer | 6 632 files |
| Total | 7 326 files, 7 325 unique languages |
| Byte share | 0.144092 % each, summing to exactly 100.000000 % |
| Segments GitHub renders | 631 (Linguist folds dialects) |
| Curated templates | ~869 of 7 326; 81.8 % of the core layer |
| Tests | 41, run by `scripts/run_tests.py`, all in CI |
| Acceptance | 19/19 |

## Commands that matter

```bash
python scripts/run_tests.py          # 41 tests
python scripts/verify_languages.py   # 19 acceptance checks
python scripts/validate_delivery.py  # repo gate
python scripts/check_templates.py    # template correctness
python scripts/audit_repo.py         # health report
python scripts/measure_motion.py     # is the recording actually moving?
bash run.sh                          # the show
```

## Toolchain

Not on PATH; invoke by absolute path:

- git `D:\Git\cmd\git.exe`
- bash `D:\Git\bin\bash.exe`
- python 3.13 `C:\hclaw\python\python.exe`
- python 3.12 (matches CI) `D:\Microsoft VS Code\data\python\python.exe`

## Environment hazards

- **PowerShell will corrupt UTF-8.** `Set-Content` / `Out-File` round-trip text
  through the console code page and destroy emoji and non-Latin characters.
  This corrupted README.md once already. Write files with Python or the edit
  tool, never with `Set-Content`.
- **PowerShell `>` writes UTF-16 with a BOM.** Use `git cat-file -p` through
  Python's `subprocess` when you need to inspect committed bytes.
- **`git push` needs the proxy at 127.0.0.1:10818.** If the proxy is down,
  every push fails; the work is safe locally and can be pushed later.
- The repo is owned by a different SID; `git config --global safe.directory` was
  required.
- `scripts/__pycache__` is owned by another SID; compile with `compile()` rather
  than `py_compile`.

## Ledgers

- `logs/ERRORS.log` — every defect found, E1–E28
- `logs/DECISIONS.md` — decisions and their reasoning
- `logs/AGENT_STATE.md` — this file
- `logs/COMMANDS.log` — command history

## What is deliberately not done

- The remaining ~150 core placeholders are languages where a plausible-looking
  program would be a fabrication. They keep the honest note.
- GitHub's legend cannot name 631 languages; that is a UI limit, not a
  repository defect.
- Branch protection, the social preview image and Pages need a browser or a
  different scope; `scripts/configure_repo.ps1` lists them as out of reach.