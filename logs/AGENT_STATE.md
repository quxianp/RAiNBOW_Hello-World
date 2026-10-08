# AGENT_STATE — Goal G-RAINBOW-HELLO

Repo: https://github.com/quxianp/RAiNBOW_Hello-World.git (branch `main`)
Local path: `E:\rainbow_hello_world`

## Goal

Ship RAiNBOW_Hello-World: 3000+ Hello-World files, a 600–800 segment Linguist
rainbow bar, a `run.sh` show that prints a rainbow `Hello World!`, and GitHub
Actions that produce `assets/hello-world.gif`, `assets/hello-world.mp4` and the
rainbow bar images.

## Environment (verified 2026-10-09)

| Tool | Location / version | Note |
|---|---|---|
| git | `D:\Git\cmd\git.exe` 2.55.0.windows.4 | NOT on PATH — added per command |
| bash | `D:\Git\bin\bash.exe` 5.3.15 | GNU bash, used for `run.sh` |
| python | `C:\hclaw\python\python.exe` 3.13.12 | primary; yaml, requests, bs4, PIL, matplotlib OK |
| python (CI parity) | `D:\Microsoft VS Code\data\python\python.exe` 3.12.7 | matches `actions/setup-python` |
| `python3` | WindowsApps stub | prints nothing — `run.sh` probes this and rejects it |
| figlet/toilet/lolcat/ffmpeg | **MISSING** locally | `scripts/rainbow.py` fallback is the live path |
| node/npx/gh/docker | MISSING | not required |

Network: `api.github.com` returns 200 directly. `objects.githubusercontent.com`
(the release CDN) times out from here — diagnostics were done via the Actions
API instead.

## Repository contents

- 694 core files, 6632 full files, 7326 total language files.
- Byte balance: every core file exactly 2048 B => 0.144092 % each, sum
  100.000000 %, stdev 0.000000 pp, 1421312 counted bytes.
- Merged inventory 7325 languages; hue span 0.0°–359.6°; 0 unrecognisable files.

## Subgoals (honest status)

| ID | Subgoal | Status | Evidence |
|---|---|---|---|
| G1 | Toolchain (git/bash/python) usable | DONE | `.tmp/probe_env.sh` |
| G2 | `README.md` with asset markers | DONE | README.md, markers verified |
| G3 | `demo.tape` VHS config | DONE | demo.tape |
| G4 | `scripts/record_demo.sh` | DONE | bash -n clean |
| G5 | `scripts/screenshot_github.py` | DONE | non-fatal, selector cascade |
| G6 | Workflow: `schedule` + `assets` job | DONE | YAML parses, 16 steps |
| G7 | `verify_languages.py` green | DONE | 19/19 on 3.12 **and** 3.13 |
| G8 | `balance_bytes.py` idempotent | DONE | 0 drift on re-run |
| G9 | `run.sh` prints rainbow Hello World | DONE | 0 malformed escapes, 12-colour greeting, exit 0 |
| G10 | Commit + push `main` | DONE | `332cf6c7..b3a2c026`, in sync (0/0) |
| G11 | Actions produces assets | **IN PROGRESS** | run 37820167736 |

## CI run history

| Run | SHA | Result | What happened |
|---|---|---|---|
| 37818363260 | 36f92f23 | cancelled | assets failed at `install VHS` (E10); verify passed |
| 37819076073 | 332cf6c7 | failure | acceptance died on `read_text(newline=)` (E12) |
| 37820167736 | b3a2c026 | **running** | all three defects fixed |

## Next step

Confirm run 37820167736: assets job green, `assets/hello-world.gif`,
`assets/hello-world.mp4` and a bar PNG committed back to `main`.
