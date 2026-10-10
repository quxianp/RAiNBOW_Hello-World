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
Type "./run.sh --jobs 8"
Enter
Sleep 25
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
