# TODO — G-RAINBOW-HELLO

- [x] G1 toolchain: git 2.55.0, bash 5.3.15, python 3.13.12 discovered under `D:\Git` / `C:\hclaw`
- [ ] G2 `README.md` (project intro, principle, core/full counts, asset block between markers)
- [ ] G3 `demo.tape` (VHS: 1200x800, font 20, 30 s)
- [ ] G4 `scripts/record_demo.sh` (VHS -> gif, ffmpeg -> mp4, non-fatal fallbacks)
- [ ] G5 `scripts/screenshot_github.py` (Playwright language-bar capture)
- [ ] G6 workflow gains `schedule` trigger + `assets` job (VHS/ffmpeg/Playwright/README push)
- [ ] G7 re-run `scripts/verify_languages.py` -> expect 19/19
- [ ] G8 re-run `scripts/balance_bytes.py` -> expect idempotent
- [ ] G9 `bash run.sh` -> rainbow `Hello World!`
- [ ] G10 commit + push `main`
- [ ] G11 Actions run produces assets

## Known gaps to close

- `README.md` missing (acceptance blocker).
- `demo.tape` missing (referenced by `.gitattributes` and by the recording step).
- `scripts/record_demo.sh` + `scripts/screenshot_github.py` missing.
- `.github/` untracked: workflow never reached the remote, so no CI has ever run.
- Workflow lacks `schedule` trigger and the whole asset-generation / README-update job.
