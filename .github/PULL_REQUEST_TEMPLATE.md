<!--
  Keep the box ticked or the acceptance job will do the work for you anyway.
-->

## What this changes

<!-- One or two sentences. -->

## Why

<!-- The problem, not the implementation. -->

## Checklist

- [ ] `python scripts/verify_languages.py` passes (19/19)
- [ ] `python scripts/validate_delivery.py` passes
- [ ] `python scripts/balance_bytes.py` produces **zero drift** on `hello/core/`
- [ ] `bash run.sh` exits 0
- [ ] Nothing under `hello/core/` was edited by hand
- [ ] `logs/ERRORS.log` or `logs/DECISIONS.md` updated if this closes a defect
      or records a trade-off

## Verification

<!-- The commands you ran and their real output. Screenshots of the terminal are
     fine; screenshots of GitHub's language panel are not, because it is served
     from an edge cache and may show a stale breakdown. -->

```
$ python scripts/verify_languages.py
...
```

## For asset or demo changes

- [ ] The recording was regenerated (`bash scripts/record_demo.sh`)
- [ ] Frame-by-frame motion was measured, not eyeballed
- [ ] `assets/hero-banner.png` regenerated if any count changed