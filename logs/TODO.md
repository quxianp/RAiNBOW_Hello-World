# TODO — G-RAINBOW-HELLO

- [x] G1 toolchain: git 2.55.0, bash 5.3.15, python 3.13.12 + 3.12.7 for CI parity
- [x] G2 `README.md` (intro, two-layer design, byte maths, hue buckets, sources, CI)
- [x] G3 `demo.tape` (VHS: 1200x800, font 20, ~29 s)
- [x] G4 `scripts/record_demo.sh` (VHS -> gif, ffmpeg -> mp4, non-fatal fallbacks)
- [x] G5 `scripts/screenshot_github.py` (selector cascade -> heading clip -> full page)
- [x] G6 workflow: daily `schedule` + `assets` job (16 steps) + PAT fallback + artifacts
- [x] G7 `verify_languages.py` 19/19 on Python 3.12.7 and 3.13.12
- [x] G8 `balance_bytes.py` idempotent (0 drift across `hello/core`)
- [x] G9 `bash run.sh` exit 0, 0 malformed escapes, 12-colour greeting, 1590 SGR sequences
- [x] G10 push `main` — in sync with origin (0 behind / 0 ahead)
- [ ] G11 confirm CI run 37820167736 publishes gif + mp4 + bar PNG

## Bugs found and fixed this session

- [x] `rgb()` emitted `ESC 38;2;R;G;Bm` with no `[` — greeting was never coloured
- [x] `rainbow.py` stripped colour whenever stdout was not a TTY
- [x] `roll_call()` printed `+0 more` after showing 50 of 694 languages
- [x] VHS tarball is nested, so `tar -xzf ... vhs` failed (E10)
- [x] CRLF/LF mismatch churned `manifest.json` by 81290 lines (E11)
- [x] `newline=` leaked onto `read_text()`, fatal on Python 3.12 (E12)
- [x] PowerShell splits multi-line `git commit -m` (E13)

## Remaining risk

- The assets job depends on the GitHub release CDN and on Chrome for VHS. Both
  are now non-fatal, so a failure degrades to "GIF missing" and is reported in
  the job summary rather than breaking the build.
- 24 shard jobs run with `max-parallel: 1`, so a full run takes roughly 20-30
  minutes wall clock.
