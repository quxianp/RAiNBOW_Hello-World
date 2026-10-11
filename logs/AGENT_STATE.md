# AGENT_STATE — Goal G-RAINBOW-HELLO — COMPLETE

Repo: https://github.com/quxianp/RAiNBOW_Hello-World.git (branch `main`)
Local path: `E:\rainbow_hello_world`

## Goal

Ship RAiNBOW_Hello-World: 3000+ Hello-World files, a 600–800 segment Linguist
rainbow bar, a `run.sh` show that prints a rainbow `Hello World!`, and GitHub
Actions that produce the demo assets and commit them back.

## Status: all acceptance criteria met

| # | Criterion | Result |
|---|---|---|
| 1 | Repository non-empty | 7 398 tracked files |
| 2 | Required files/dirs present | all 12 verified by `scripts/validate_delivery.py` |
| 3 | `hello/core` 600–800 | **694** |
| 4 | Equal share, sums to 100 % | 0.144092 % each, **100.000000 %**, stdev 0.000000 pp |
| 5 | `hello/full` ≥ 2400 | **6 632** |
| 6 | Total language files ≥ 3000 | **7 326** |
| 7 | Bar is hundreds of fine segments | **631** languages live on GitHub, ~1.90 px each |
| 8 | `run.sh` prints a rainbow Hello World! | exit 0, 0 malformed escapes, 12-colour greeting |
| 9 | Actions generate gif/mp4/bar png | all four present, committed by CI |
| 10 | README embeds the assets | asset block between the markers |
| 11 | `main` pushed | in sync, 0 behind / 0 ahead |
| 12 | Pipeline runs unattended | 2 daily `schedule` runs fired and self-published |

## Environment (verified 2026-10-09)

| Tool | Location / version | Note |
|---|---|---|
| git | `D:\Git\cmd\git.exe` 2.55.0.windows.4 | not on PATH; added per command |
| bash | `D:\Git\bin\bash.exe` 5.3.15 | used for `run.sh` |
| python | `C:\hclaw\python\python.exe` 3.13.12 | yaml, requests, bs4, PIL, matplotlib |
| python (CI parity) | `D:\Microsoft VS Code\data\python\python.exe` 3.12.7 | matches `actions/setup-python` |
| figlet/toilet/lolcat/ffmpeg | absent locally | `scripts/rainbow.py` fallback is the live path |

Network: `api.github.com` reachable; the release CDN (`objects.githubusercontent.com`)
is not, from this machine. Python's `urllib` cannot reach GitHub (no system proxy) --
PowerShell's `Invoke-RestMethod` can.

## CI run history

| Run | SHA | Result | Note |
|---|---|---|---|
| 37818363260 | 36f92f23 | cancelled | `install VHS`: nested tarball (E10) |
| 37819076073 | 332cf6c7 | failure | `read_text(newline=)` fatal on 3.12 (E12) |
| 37820167736 | b3a2c026 | success | green but produced no GIF/MP4 (E10 masked) |
| 37820749718 | 6c8c987b | success | GIF + MP4 + real bar PNG produced |
| 37821672417 | 039a9522 | success | cache-busting blanked the page (E14) |
| 37822464159 | 9ce8bb45 | success | all assets correct, clutter removed |
| 37919176384 | 6598bc2b | success | **schedule**, 2026-10-09 |
| 38043242505 | 84ae1ee7 | success | **schedule**, 2026-10-10 |
| 38074239612 | 3a9054fe | success | exec bit fixed: GIF 45 KB -> 603 KB, demo runs |
| 38075001749 | 020847d2 | success | bold two-line finale art |
| 38076066230 … 38077288158 | various | failure | linguist gem install/require/API fixes |
| latest | a29f9fb5 | success | full 631-language bar image published (917 KB) |

## The rendered bar image

`assets/rainbow-bar-github.png` is drawn by `scripts/render_github_bar.py` from
`GET /repos/.../languages`:

- the 631-segment strip in GitHub's own descending-byte order
- **every one of the 631 languages listed by name**, with its Linguist colour
  swatch and its real share, in the same order, so legend position *i*
  corresponds to bar segment *i*
- 10 columns x 64 rows, 2557x1358; the figure width auto-grows until the
  longest actual name fits its column, so long names such as
  "Mathematical Programming System" never collide with the share beside them
- one language (`Checksums`) has no Linguist colour and renders grey; the script
  logs that rather than hiding it

## What the screenshots in the report showed, and what was actually true

| What the screenshots in the report showed, and what was actually true

| Symptom | Reality |
|---|---|
| GIF shows `bash: ./run.sh: Permission denied` | **Real bug.** The file was committed 100644. Fixed; the demo now records a 534 KB GIF of the actual show. |
| Bar shows `HTML 27.6 %`, C/C++ not visible | **Stale cached page.** `github-linguist` 9.7.0 and `GET /repos/.../languages` both report 631 languages / 1 417 216 B / HTML 1.0116 %. |
| C, C++, Java, Go, Rust not named | **UI limitation.** GitHub names only the largest few of 631 languages and folds the rest into "Other". `assets/rainbow-bar-github.png` lists **all 631 by name**, with colour and share. |
| The image only showed ~31 languages | **Fair criticism.** The renderer used a hand-picked "featured" list. Replaced with a full legend of every language in the breakdown. |

## Known residual risk

- The HTML family collapses: `HTML`, `HTML+ECR/EEX/ERB/PHP/Razor` and `Ecmarkup`
  are seven files reported as one `HTML` segment, so those six dialects do not get
  their own stripe. Recovering them needs per-file modeline support that the
  Linguist CLI cannot currently report on (E17b).
- `scripts/screenshot_github.py` still captures the cached panel; it now writes
  `assets/rainbow-bar-live.png`, which is not referenced from the README, and the
  6 KB floor deletes degenerate captures.
- The 24 shard jobs run `max-parallel: 1`, so a full run is ~20–30 min.

## Next step

None. Shipped.
