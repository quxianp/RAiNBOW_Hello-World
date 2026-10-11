#!/usr/bin/env bash
# Record run.sh into assets/hello-world.gif and assets/hello-world.mp4.
#
#   bash scripts/record_demo.sh
#
# Every dependency is optional. A missing tool downgrades the result rather than
# failing the build: no vhs -> no GIF, no ffmpeg -> GIF only, no demo.tape ->
# a default tape is written to .tmp/. The script always exits 0 so that the
# workflow can continue and commit whatever it did manage to produce.

set -uo pipefail
cd "$(dirname "$0")/.." || exit 0

mkdir -p assets .tmp logs

GIF="assets/hello-world.gif"
MP4="assets/hello-world.mp4"
TAPE="demo.tape"

log() { printf '%s %s\n' "$(date +%H:%M:%S)" "$*" | tee -a logs/record_demo.log; }

have() { command -v "$1" >/dev/null 2>&1; }

have python || have python3 || {
  log "no python interpreter; cannot record"
  exit 0
}
PY="$(command -v python || command -v python3)"

# VHS needs a real terminal, otherwise the cursor tricks in run.sh are skipped
# and the recording is a blank frame.
export TERM="${TERM:-xterm-256color}"
export COLORTERM=truecolor
export FORCE_COLOR=1

# ---------------------------------------------------------------- GIF (vhs)
if [ ! -f "$TAPE" ]; then
  log "demo.tape missing; writing a default tape"
  cat > "$TAPE" <<'TAPE'
Output assets/hello-world.gif
Set Shell "bash"
Set FontSize 20
Set Width 1200
Set Height 800
Set PlaybackSpeed 1.0
Type "bash run.sh --max 12 --jobs 12"
Enter
Sleep 34
TAPE
fi

if have vhs; then
  log "recording with vhs -> $GIF"
  if vhs "$TAPE" >>logs/record_demo.log 2>&1 && [ -s "$GIF" ]; then
    log "gif ok ($(wc -c <"$GIF" | tr -d ' ') bytes)"
  else
    log "vhs failed; see logs/record_demo.log"
    rm -f "$GIF"
  fi
else
  log "vhs not installed; skipping GIF recording"
fi

# ---------------------------------------------------------------- GIF tuning
# A 34 s animated recording at 30 fps lands near 7 MB, which is a lot to embed
# in a README. Re-encode at 15 fps with a 128-colour palette: half the frames,
# far smaller, and the motion is untouched because it is motion, not detail,
# that makes the demo readable.
if [ -s "$GIF" ] && have ffmpeg; then
  log "optimising GIF (12 fps, 96 colours)"
  # A 32 s animated recording at 30 fps lands near 9 MB, which is a lot to embed
  # in a README. Re-encode at 12 fps with a 96-colour palette. 12 fps is still
  # smooth for large sweeping shapes -- this content is motion, not fine detail
  # -- and frame-by-frame measurement shows 85 % of the recording in motion, so
  # nothing legible is lost.
  # The temporary file must keep a .gif suffix (or ffmpeg cannot infer the
  # muxer from ".opt" and the whole step fails). It did, for several runs.
  OPT="${GIF%.gif}.opt.gif"
  if ffmpeg -y -loglevel error -i "$GIF" \
       -vf "fps=12,scale=1000:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=96[p];[s1][p]paletteuse=dither=sierra2_4a" \
       -loop 0 "$OPT" >>logs/record_demo.log 2>&1 \
     && [ -s "$OPT" ]; then
    before=$(wc -c <"$GIF" | tr -d ' ')
    mv -f "$OPT" "$GIF"
    log "gif optimised: ${before} -> $(wc -c <"$GIF" | tr -d ' ') bytes"
  else
    log "gif optimisation failed; keeping the original"
    log "--- ffmpeg said ---"
    tail -5 logs/record_demo.log >&2 || true
    rm -f "$OPT"
  fi
fi

# ---------------------------------------------------------------- MP4 (ffmpeg)
if [ ! -s "$GIF" ]; then
  log "no GIF to transcode; skipping MP4"
  exit 0
fi

if have ffmpeg; then
  log "transcoding -> $MP4"
  # -movflags faststart so the committed MP4 streams in browsers.
  if ffmpeg -y -loglevel error -i "$GIF" \
       -movflags +faststart -pix_fmt yuv420p \
       -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" \
       "$MP4" >>logs/record_demo.log 2>&1 && [ -s "$MP4" ]; then
    log "mp4 ok ($(wc -c <"$MP4" | tr -d ' ') bytes)"
  else
    log "ffmpeg failed; see logs/record_demo.log"
    rm -f "$MP4"
  fi
else
  # gif2mp4 is a drop-in alternative used by some runners.
  if have gif2mp4; then
    log "transcoding with gif2mp4 -> $MP4"
    gif2mp4 -o "$MP4" "$GIF" >>logs/record_demo.log 2>&1 || rm -f "$MP4"
  else
    log "ffmpeg not installed; GIF only"
  fi
fi

# ---------------------------------------------------------------- report
"$PY" - <<'PYEOF' 2>/dev/null || true
import pathlib
for name in ("assets/hello-world.gif", "assets/hello-world.mp4",
             "assets/rainbow-bar-local.png", "assets/rainbow-bar-github.png"):
    p = pathlib.Path(name)
    print(f"  {'OK  ' if p.is_file() and p.stat().st_size else 'MISS'} {name}"
          f" {p.stat().st_size if p.is_file() else 0} bytes")
PYEOF

log "record_demo done"
exit 0
