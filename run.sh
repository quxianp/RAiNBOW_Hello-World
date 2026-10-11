#!/usr/bin/env bash
# RAiNBOW_Hello-World -- the show.
#
#   1. load deps (fallbacks everywhere, never aborts)
#   2. opening animation: core language names flying past with a check mark
#   3. run every runnable core language in parallel (scripts/run_languages.py)
#   4. ASCII-art "Hello World!" via figlet or toilet (or pure python)
#   5. paint it: lolcat if present, otherwise scripts/rainbow.py (24-bit RGB)
#   6. optional system beep
#   7. easter egg: 5 esoteric languages from hello/full/ + interpreter links
#   8. print a rainbow "Hello World!" no matter what
#
#   ./run.sh            full show
#   ./run.sh --quiet    skip the opening animation
#   ./run.sh --jobs 16  parallelism

set -u
cd "$(dirname "$0")" || exit 1
mkdir -p logs

RUN_LOG="logs/run.log"
: > "$RUN_LOG"

QUIET=0
JOBS=8
MAX_SHOWN=50
# Motion budget for the recorded demo. These only take effect on a real
# terminal; pipes and CI logs get the static render.
BRAND_FRAMES=18
BRAND_DELAY=0.055
BAR_FRAMES=44
REVEAL_FRAMES=30
ROLL_DELAY=0.07
DIVIDER_FRAMES=14
SHOW_WIDTH=108

while [ $# -gt 0 ]; do
  case "$1" in
    --quiet|-q) QUIET=1 ;;
    --jobs|-j) shift; JOBS="${1:-8}" ;;
    --max) shift; MAX_SHOWN="${1:-50}" ;;
    --motion) shift; BRAND_FRAMES="${1:-18}" ;;
    --fast) QUIET=1; BRAND_FRAMES=0; BAR_FRAMES=0; REVEAL_FRAMES=0; DIVIDER_FRAMES=0 ;;
    --help|-h)
      sed -n '2,20p' "$0"; exit 0 ;;
    *) ;;
  esac
  shift
done

log()  { printf '%s %s\n' "$(date +%H:%M:%S)" "$*" >> "$RUN_LOG"; }
logf() { printf '%s %s\n' "$(date +%H:%M:%S)" "$*" | tee -a "$RUN_LOG"; }

have() { command -v "$1" >/dev/null 2>&1; }
# The WindowsApps `python3` stub prints nothing, so probe for an interpreter
# that actually runs code instead of trusting `command -v`.
PY=""
for cand in python3 python py; do
  if have "$cand" && [ "$("$cand" -c 'print(1)' 2>/dev/null)" = "1" ]; then
    PY="$cand"
    break
  fi
done
[ -n "$PY" ] || PY=python3

ESC=$'\033'
C_RESET="$ESC[0m"; C_DIM="$ESC[2m"; C_BOLD="$ESC[1m"

rgb() { printf '%s[38;2;%d;%d;%dm' "$ESC" "$1" "$2" "$3"; }

# --------------------------------------------------------------------------
logf "=== RAiNBOW_Hello-World run.sh start ==="
log "args: quiet=$QUIET jobs=$JOBS"

if [ -t 1 ]; then
  printf '%s%s%s' "$ESC" "[?25l" "$C_RESET"
  trap 'printf "%s%s%s" "$ESC" "[?25h" "$C_RESET"' EXIT
  CLEAR=$'\033[2J\033[H'
else
  CLEAR=""
  trap '' EXIT
fi

# --------------------------------------------------------------------------
# 0. dependency detection with fallbacks
# --------------------------------------------------------------------------
FIGLET=""; TOILET=""
have figlet  && FIGLET="figlet"
have toilet  && TOILET="toilet"
LOLCAT=""
have lolcat  && LOLCAT="lolcat"

logf "deps: figlet=${FIGLET:-fallback-python} toilet=${TOILET:-fallback-python} lolcat=${LOLCAT:-fallback-python/rainbow.py} runner=run_languages.py(jobs=$JOBS)"

CORE_COUNT=$(find hello/core -type f 2>/dev/null | wc -l | tr -d ' ')
FULL_COUNT=$(find hello/full -type f 2>/dev/null | wc -l | tr -d ' ')
TOTAL_COUNT=$((CORE_COUNT + FULL_COUNT))
log "core files=$CORE_COUNT full files=$FULL_COUNT"

# --------------------------------------------------------------------------
# 1. opening animation
# --------------------------------------------------------------------------
say() { printf '%s' "$1"; }

banner_line() {
  printf '%s' "$C_BOLD"
  printf '%s' "$(rgb 255 105 180)RAiNBOW$HUE "" ; "
}

# Animated hue sweep of the word RAiNBOW.
#
# The maths used to live here and was wrong: `h` was computed per character and
# then thrown away in favour of `rgb 255 255 255`, so every frame rendered the
# banner pure white. It now lives in scripts/brand_frames.py, which collapses to
# a single static line when stdout is not a terminal.
animated_brand() {
  if [ "$QUIET" = "1" ] || [ ! -t 1 ]; then
    printf '%sRAiNBOW_Hello-World%s\n' "$C_BOLD" "$C_RESET"
    return
  fi
  "$PY" scripts/brand_frames.py \
    --frames "$BRAND_FRAMES" \
    --delay "$BRAND_DELAY" \
    --subtitle "$(printf '%s%06d+ languages on the bar  .  %s byte-balanced rainbow' \
                     "$C_DIM" "$CORE_COUNT" "$C_RESET")" 2>/dev/null \
    || printf '%sRAiNBOW_Hello-World%s\n' "$C_BOLD" "$C_RESET"
}

# --------------------------------------------------------------------------
if [ "$QUIET" = "0" ]; then
  animated_brand
  printf '\n'
fi

# --------------------------------------------------------------------------
# 2. core language roll call
# --------------------------------------------------------------------------
core_names() {
  if [ -f config/core-langs.txt ]; then
    cat config/core-langs.txt
  else
    find hello/core -mindepth 1 -maxdepth 1 -type d -printf '%f\n' 2>/dev/null \
      || find hello/core -mindepth 1 -maxdepth 1 -type d -exec basename {} \; 2>/dev/null
  fi
}

# A few frames of moving rainbow between sections, so the recording never sits
# on a static prompt for long.
divider() {
  [ "$DIVIDER_FRAMES" -le 0 ] && return 0
  [ -t 1 ] || return 0
  "$PY" scripts/rainbow.py --sweep "$DIVIDER_FRAMES" --sweep-only \
    --width "$SHOW_WIDTH" 2>/dev/null || true
}

roll_call() {
  printf '  %sBooting %s core languages%s\n' "$C_DIM" "$CORE_COUNT" "$C_RESET"
  if [ "$QUIET" = "1" ]; then
    core_names | head -n "$MAX_SHOWN" | while IFS= read -r name; do
      [ -n "$name" ] && printf '    %s+%s %s\n' "$(rgb 120 220 120)" "$C_RESET" "$name"
    done
    printf '    %s... +%d more core languages%s\n' \
      "$C_DIM" "$((CORE_COUNT - MAX_SHOWN > 0 ? CORE_COUNT - MAX_SHOWN : 0))" "$C_RESET"
  else
    # scripts/roll_call.py emits the names one at a time with a travelling hue
    # wave; it degrades to a plain listing when stdout is not a terminal.
    "$PY" scripts/roll_call.py --max "$MAX_SHOWN" --delay "$ROLL_DELAY" \
      --total "$CORE_COUNT" 2>/dev/null \
      || core_names | head -n "$MAX_SHOWN"
  fi
  printf '    %s+%s full-layer languages present in hello/full (%s files)\n' \
    "$(rgb 120 220 120)" "$C_RESET" "$FULL_COUNT"
  printf '\n'
}

divider
roll_call

# --------------------------------------------------------------------------
# 3. parallel execution of every core language we know how to run
#    (the worker pool lives in scripts/run_languages.py --run N)
# --------------------------------------------------------------------------
RUNNERS_FILE="logs/runners.txt"
OUT_DIR="logs/output"
mkdir -p "$OUT_DIR"
: > "$RUNNERS_FILE"

"$PY" scripts/run_languages.py --list > "$RUNNERS_FILE" 2>>"$RUN_LOG" || true
PLANNED=$(wc -l < "$RUNNERS_FILE" | tr -d ' ')
log "planned runnable languages: $PLANNED"

if [ "$PLANNED" -gt 0 ]; then
  printf '  %sExecuting %s languages in parallel (jobs=%s)%s\n' \
    "$C_DIM" "$PLANNED" "$JOBS" "$C_RESET"

  "$PY" scripts/run_languages.py --run 1 --jobs "$JOBS" \
    > "$OUT_DIR/results.tsv" 2>>"$RUN_LOG" || true

  OK_COUNT=$(grep -c $'\tok\t' "$OUT_DIR/results.tsv" 2>/dev/null || echo 0)
  printf '  %s%s spoke, %s silent / unavailable%s\n' \
    "$C_DIM" "${OK_COUNT:-0}" "$PLANNED" "$C_RESET"
  log "executed ok=$OK_COUNT planned=$PLANNED"
fi

# --------------------------------------------------------------------------
# 4. ASCII art "Hello World!"
# --------------------------------------------------------------------------
ascii_hello() {
  if [ -n "$FIGLET" ]; then
    printf 'Hello World!' | "$FIGLET" -w 110
  elif [ -n "$TOILET" ]; then
    printf 'Hello World!' | "$TOILET" -f banner -w 110
  else
    "$PY" scripts/rainbow.py --hello --plain | sed 's/^/  /'
    cat <<'ART'
   _ _          _ _   _           _
  | | |__   ___| | |_(_)_ __   ___| |
  | | '_ \ / _ \ | __| | '_ \ / _ \ |
  | | | | |  __/ | |_| | | | |  __/ |
  |_|_| |_|\___|_|\__|_|_| |_|\___|_|

   _ _ _         _       _     _
  | | | |___ ___| |_  __| |_ _| |_ _ __
  | | | / __/ _ \ | |/ _` | __| __| | '_ \
  | | | \__ \  __/ | | (_| | |_| |_| | | |
  |___|_|___/\___|_|\__,_|\__|\__|_|_| |_|
ART
  fi
}

ART=$(ascii_hello)

# --------------------------------------------------------------------------
# 5. paint it
# --------------------------------------------------------------------------
printf '\n'
if [ -n "$LOLCAT" ] && [ -t 1 ]; then
  printf '%s\n' "$ART" | "$LOLCAT" -f 0.6 --speed 40
else
  "$PY" scripts/rainbow.py --hello --width 110 2>/dev/null || printf '%s\n' "$ART"
fi

# --------------------------------------------------------------------------
# 6. optional sound
# --------------------------------------------------------------------------
beep() {
  if have afplay;   then afplay /System/Library/Sounds/Ping.aiff >/dev/null 2>&1
  elif have aplay; then printf 'sine 880 60' >/dev/null; aplay -q sine 880 60 >/dev/null 2>&1
  elif have paplay; then paplay /usr/share/sounds/freedesktop/stereo/message.oga >/dev/null 2>&1
  elif have pwplay; then pwplay -q /usr/share/sounds/freedesktop/stereo/message.oga >/dev/null 2>&1
  else printf '\a'; fi
}
beep >/dev/null 2>&1 || true
log "beep attempted"

# --------------------------------------------------------------------------
# 7. easter egg: esoteric languages
# --------------------------------------------------------------------------
eggs=$(find hello/full -type f 2>/dev/null | grep -Ei 'brainfuck|whitespace|malbolge|intercal|lolcode|befunge|piet|forth|smalltalk|chef' | head -3)
if [ -n "$eggs" ]; then
  printf '\n  %sEaster egg: esoteric corner of hello/full/%s\n' "$C_DIM" "$C_RESET"
  printf '%s\n' "$eggs" | while IFS= read -r f; do
    printf '    %s%s%s\n' "$(rgb 255 180 60)" "$f" "$C_RESET"
    sed -n '1,4p' "$f" 2>/dev/null | sed 's/^/      /'
  done
  printf '    %sinterpreters: https://esolangs.org/  https://rosettacode.org/%s\n' \
    "$C_DIM" "$C_RESET"
fi

# --------------------------------------------------------------------------
# 8. the finale: language bar, then the big rainbow art, then the greeting.
#    The money shot goes last so it is what a recording still shows when the
#    show has scrolled -- an earlier layout put the art mid-show, where the
#    easter egg pushed it off screen.
# --------------------------------------------------------------------------
printf '\n'
divider
"$PY" scripts/rainbow.py --bar --fill-frames "$BAR_FRAMES" --width "$SHOW_WIDTH" 2>/dev/null \
  || "$PY" scripts/rainbow.py --bar --width "$SHOW_WIDTH" 2>/dev/null || true

printf '\n'
"$PY" scripts/rainbow.py --hello --reveal-frames "$REVEAL_FRAMES" --width "$SHOW_WIDTH" 2>/dev/null \
  || "$PY" scripts/rainbow.py --hello --width "$SHOW_WIDTH" 2>/dev/null || printf '%s\n' "$ART"

printf '\n'
final_rainbow_hello() {
  local msg="Hello World!"
  local i n=${#msg}
  for (( i = 0; i < n; i++ )); do
    local h=$(( (i * 360 / n) ))
    printf '%s%s%s' "$(rgb $((255 - h / 4)) $((120 + h / 3)) $((60 + h / 2)))" \
      "${msg:$i:1}" "$C_RESET"
  done
  printf '\n'
}

# Emit the true-colour greeting even when redirected: run.log, CI logs and the
# recorded demo all want to see the rainbow. NO_COLOR opts out.
if [ -n "${NO_COLOR:-}" ]; then
  printf 'Hello World!\n'
else
  final_rainbow_hello
  printf '%s  %s languages on the bar  .  %s files in the repo%s\n' \
    "$C_DIM" "$CORE_COUNT" "$TOTAL_COUNT" "$C_RESET"
  printf '%s  https://github.com/quxianp/RAiNBOW_Hello-World%s\n' "$C_DIM" "$C_RESET"
fi

log "=== run.sh done ==="
exit 0
