# TODO — G-RAINBOW-HELLO — COMPLETE

- [x] G1 toolchain: git 2.55.0, bash 5.3.15, python 3.13.12 + 3.12.7 for CI parity
- [x] G2 `README.md` (intro, two-layer design, byte maths, hue buckets, sources,
      measured live-bar numbers, CI instructions)
- [x] G3 `demo.tape` (VHS: 1200x800, font 20)
- [x] G4 `scripts/record_demo.sh` (VHS -> gif, ffmpeg -> mp4, non-fatal fallbacks)
- [x] G5 `scripts/screenshot_github.py` (scoped selectors, 6 KB floor, `.tmp` diagnostic)
- [x] G6 workflow: daily `schedule` + `assets` job + PAT fallback + artifact upload
      + `assert the demo assets exist` gate
- [x] G7 `verify_languages.py` 19/19 on Python 3.12.7 **and** 3.13.12
- [x] G8 `balance_bytes.py` idempotent (0 drift across `hello/core`)
- [x] G9 `bash run.sh` exit 0, 0 malformed escapes, 12-colour greeting
- [x] G10 push `main` — in sync with origin
- [x] G11 CI run 37822464159: gif + mp4 + local bar + GitHub bar all committed

## Bugs found and fixed this session

- [x] `rgb()` emitted `ESC 38;2;R;G;Bm` with no `[` — the greeting was never coloured
- [x] `rainbow.py` stripped colour whenever stdout was not a TTY
- [x] `roll_call()` printed `+0 more` after showing 50 of 694 languages
- [x] VHS release tarball is nested, so `tar -xzf ... vhs` failed (E10)
- [x] checksum verification aborted the install step under `set -e`, and
      `continue-on-error` reported it as success (E10)
- [x] bare `.Progress` matched a 141-byte indicator, not the language bar (E11)
- [x] CRLF/LF mismatch churned `manifest.json` by 81 290 lines (E11)
- [x] `newline=` leaked onto `read_text()`, fatal on Python 3.12 (E12)
- [x] PowerShell splits multi-line `git commit -m` (E13)
- [x] cache-busting blanked the GitHub page (E14) — reverted

## Optional future work (not blocking)

- [ ] Raise `max-parallel` above 1 for the shard matrix if CI minutes allow.
- [ ] Expand `hello/full/` when new language sources appear.
