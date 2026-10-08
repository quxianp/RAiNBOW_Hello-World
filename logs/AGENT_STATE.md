# AGENT_STATE — Goal G-RAINBOW-HELLO

Repo: https://github.com/quxianp/RAiNBOW_Hello-World.git (branch `main`)
Local path: `E:\rainbow_hello_world`

## Goal

Ship RAiNBOW_Hello-World: 3000+ Hello-World files, a 600–800 segment Linguist rainbow
bar, a `run.sh` show that prints a rainbow `Hello World!`, and GitHub Actions that
produce `assets/hello-world.gif`, `assets/hello-world.mp4` and the rainbow bar images.

## Environment (verified 2026-10-09)

| Tool | Location / version | Note |
|---|---|---|
| git | `D:\Git\cmd\git.exe` 2.55.0.windows.4 | NOT on PATH — must be added per command |
| bash | `D:\Git\bin\bash.exe` 5.3.15 | GNU bash, used for `run.sh` |
| python | `C:\hclaw\python\python.exe` 3.13.12 | yaml, requests, bs4, PIL, matplotlib OK |
| `python3` | WindowsApps stub | prints nothing — `run.sh` probes this and rejects it |
| figlet/toilet/lolcat/ffmpeg | **MISSING** | `run.sh` fallbacks (scripts/rainbow.py) are the live path |
| node/npx/gh/docker | MISSING | not required; CI does the heavy lifting |

Network: direct `https://api.github.com` returns 200. Proxy `127.0.0.1:10818` alive.

## Inherited state (from prior agent, not yet re-verified by me)

- 694 core files, 6632 full files, 7326 total language files (counted this session).
- `logs/verify_languages.json` claims 19/19 checks ok.
- `logs/balance_summary.json` claims 694 x 2048 B, sum 100 %.
- Local `main` is 8 commits AHEAD of `origin/main`, 7374 tracked files.
- `.github/` is UNTRACKED — the workflow has never been pushed.
- `README.md` and `demo.tape` DO NOT EXIST.
- Missing scripts: `record_demo.sh`, `screenshot_github.py`.
- Workflow has no `schedule` trigger and no asset-generation job.

## Subgoals (honest status)

| ID | Subgoal | Status | Evidence |
|---|---|---|---|
| G1 | Toolchain (git/bash/python) usable | DONE | `.tmp/probe_env.sh` |
| G2 | `README.md` with asset markers | TODO | — |
| G3 | `demo.tape` VHS config | TODO | — |
| G4 | `scripts/record_demo.sh` | TODO | — |
| G5 | `scripts/screenshot_github.py` | TODO | — |
| G6 | Workflow: `schedule` + assets job | TODO | — |
| G7 | Re-run `verify_languages.py` green | TODO | — |
| G8 | Re-run `balance_bytes.py` idempotent | TODO | — |
| G9 | `run.sh` prints rainbow Hello World | TODO | — |
| G10 | Commit + push `main` | TODO | — |
| G11 | Actions produces assets | TODO | — |

## Failures / fallbacks (see logs/ERRORS.log)

1. `git`/`bash` absent from PATH -> discovered at `D:\Git`, added explicitly.
2. git "dubious ownership" -> `git config --global --add safe.directory E:/rainbow_hello_world`.
3. `python3` resolves to a WindowsApps stub -> `run.sh` probes `print(1)`.
4. figlet/toilet/lolcat missing -> pure-python `scripts/rainbow.py` renders art + colour.
5. `matplotlib` missing -> installed via pip (3.11.2).

## Next step

G7/G8 first (cheap, re-establishes ground truth), then G9, then write G2–G6, then G10, G11.
