# Security Policy

## What this repository is

7,326 files that each contain a greeting, a banner comment and padding. One
Bash script that draws them. One Python generator. No network access, no
credentials, no database, no user accounts, no data anyone typed.

There is very little here that can be attacked, and the honest thing is to say
which parts are the only parts worth thinking about.

## What actually runs

| what | where | what it does |
|---|---|---|
| `run.sh` | your shell | reads the files in `hello/` and prints a coloured banner |
| `scripts/generate_all_hello.py` | your Python | writes `hello/` from the tables in the repository |
| `scripts/record_demo.sh` | CI only | shells out to ffmpeg and vhs |
| `scripts/apply_batches.py` | your shell | runs git and `add_templates.py` |

`run.sh` is the only thing a visitor runs, and it reads nothing outside this
repository.

## Where a real vulnerability would be

**`run.sh` under `set -u`.** This is not hypothetical. E31 was a crash in the
demo: `run.sh` read an undefined `$FAST` behind a `[ -t 1 ]` guard, so it
executed correctly on a terminal and crashed in CI. `tests/test_shell_variables.py`
now exists because of it. If you find another undefined variable under `set -u`,
that is a genuine bug and we want it.

**The generator writes 7,326 files.** Anything that changes what it writes can
change every file in the repository at once. `scripts/add_templates.py` refuses
a program that does not contain a greeting, refuses one for a language the
repository does not ship, and `scripts/check_templates.py` runs afterwards --
but the review is the real control.

**CI runs third-party actions.** `actions/checkout`, `actions/setup-python`,
`ffmpeg` and `vhs`. Pinned to major versions, not to commit SHAs. That is a
deliberate trade-off for a repository with no secrets and no write access from
the runner, and it is worth revisiting if that ever changes.

## Out of scope

- **The contents of `hello/`.** Those are other people's Hello World programs,
  vendored. A bug in one of them is a bug in that language, not in this
  repository. If a vendored file turns out to do something unexpected, that is
  still worth reporting -- see below.
- **The generated assets.** `assets/hello-world.gif`, `.mp4` and the bar PNG
  are rebuilt by CI on every push.
- **Denial of service through CI.** Forking and letting Actions churn is not a
  vulnerability in this repository.

## Reporting a vulnerability

There is no security.txt and no dedicated address, because this repository has
one maintainer and adding a private reporting channel for a Hello World
collection would be theatre. Open an issue, or email the address in the
repository's About panel if the issue should not be public.

If you have found something exploitable rather than merely wrong, say so in the
first line. It will be looked at.

## Verifying what you are running

```sh
git log --oneline -1          # what you have
python scripts/run_tests.py   # 99 tests
python scripts/validate_delivery.py
bash run.sh                   # the rainbow
```

`scripts/validate_delivery.py` runs every repository check in the order CI does,
and prints `ALL WORKFLOW/REPO CHECKS PASSED` or the list of what did not. If
that command passes on your checkout, the checkout is the one this repository
published.