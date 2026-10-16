# The demo

`assets/hello-world.gif` is a recording of `run.sh` made by
`scripts/record_demo.sh` in GitHub Actions, using
[VHS](https://github.com/charmbracelet/vhs) and a headless Chrome. The MP4 is
transcoded from the same take.

Everything here exists because of one specific failure, and it is worth stating
before the mechanics.

## The failure

The published GIF once spent 22 of its 33 seconds on a single still frame. Every
signal the build had said the demo was fine:

- the recording step succeeded;
- the encoder succeeded, and produced a plausible four-megabyte file;
- `run.sh` printed `=== run.sh done ===` to the run log;
- all nineteen acceptance checks passed.

The GIF was frozen because `run.sh` was crashing at line 279 with

```
run.sh: line 279: FAST: unbound variable
```

written across the middle of the screen, above a still image that occupied two
thirds of the recording.

`measure_motion.py` reported "367 of 418 transitions frozen" and could not say
why. Coverage tells you that nothing changed; only a picture tells you that
something changed into an error message. Three commits were spent shortening a
sleep before anybody extracted a frame and read it.

## The three tools, in the order to reach for them

| | |
|---|---|
| `python scripts/check_demo_motion.py` | **Is anything moving?** A gate. Fails the build before the assets are committed. |
| `python scripts/measure_motion.py` | **Where does it stop?** Coverage by time bucket, and the longest frozen runs. |
| `python scripts/inspect_frames.py` | **What is on screen?** A contact sheet of frames across the runtime. |

The third is the one that finds things the first two cannot. A nine-frame tile
across the runtime shows a crash printed mid-frame, a blank screen at 14.9 s and
a blank final screen, in one image. Both of the latter were real and neither was
visible to any statistic.

```bash
python scripts/inspect_frames.py                 # 9-frame contact sheet
python scripts/inspect_frames.py --at 0,8,16     # specific times
python scripts/inspect_frames.py --json          # measurements only
```

## The gate

`check_demo_motion.py` runs after the recording and before `git add`, so a static
take is never published. Two independent checks, because either alone has a blind
spot:

| check | threshold | why |
|---|---|---|
| frozen transitions | ≤ 50 % | the same boundary `measure_motion.py` already calls "monotonous" |
| mean coverage | ≥ 3.0 % | catches drift — moving a little, reading as a still image with flicker |

A missing GIF exits 0, so a VHS CDN outage cannot block the pipeline. The
measurement goes to the run summary and to `logs/demo_motion.json`, which is
gitignored because the assets job does `git add -A logs` and it changes every run.

Calibration is every failure this has actually had, which is the only honest one
available without pretending to more runs than have been done:

| | mean coverage | frozen |
|---|---|---|
| the crash | 1.79 % | 84 % |
| a hold that skipped itself | 1.93 % | 88 % |
| measured now | 8.10 % | 28.9 % |

`tests/test_demo_assets.py` asserts the *committed* GIF is animated too, so a
file restored from a backup or copied from another branch is caught locally. It
also asserts the gate's own thresholds have not been quietly widened — that is
the one-number edit somebody under pressure to green a build would make.

## The tape

`demo.tape` types `FORCE_HOLD=1 bash run.sh --max 12 --jobs 12` and sleeps. Three
things in it are load-bearing and each was arrived at by measurement:

- **`FORCE_HOLD=1`.** The closing hold is guarded on `[ -t 1 ]`, which is false
  whenever stdout is a pipe — and a recorder drives `run.sh` exactly that way.
- **`Sleep 28`.** The show takes about 16 s and the hold 10 s. Earlier values of
  32 s and 18 s each came from reasoning about the program rather than timing it,
  and each was wrong in the direction of leaving the last third frozen.
- **No cold open.** One was tried: a hue sweep before the show, so the video would
  open on colour. It cost about four seconds of typing to buy a little over one
  second of visible sweep, and the first frame was still blank.

## The encoding

Seven settings were re-encoded from the same source and scored on bytes and on
frame-to-frame coverage:

| setting | size | mean coverage | frozen |
|---|---:|---:|---:|
| 12 fps, full width, 256 colours | 13.5 MB | 6.20 % | 32.7 % |
| **10 fps, 800 px, 128 colours** | **5.2 MB** | **7.18 %** | **28.7 %** |

Smaller *and* more animated, which is not obvious in advance: shrinking the frame
makes each changed pixel a larger fraction of it, so measured coverage rises while
the byte count falls.

The 96-colour setting that preceded this was blamed for freezing the recording
across two commits. It was innocent — the show was crashing. Chasing a codec for a
crash is the comfortable mistake: a setting is a number you can change and a
crash is a bug you have to find.
