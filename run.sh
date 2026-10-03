#!/usr/bin/env bash
# RAiNBOW_Hello-World -- the show.
#
#   1. load deps (fallbacks everywhere, never aborts)
#   2. opening animation: core language names flying past with a check mark
#   3. run every runnable core language in parallel (xargs -P / GNU parallel)
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

while [ $# -gt 0 ]; do
  case "$1" in
    --quiet|-q) QUIET=1 ;;
    --jobs|-j) shift; JOBS="${1:-8}" ;;
    --max) shift; MAX_SHOWN="${1:-50}" ;;
    --help|-h)
      sed -n '2,20p' "$0"; exit 0 ;;
    *) ;;
  esac
  shift
done

log()  { printf '%s %s\n' "$(date +%H:%M:%S)" "$*" >> "$RUN_LOG"; }
logf() { printf '%s %s\n' "$(date +%H:%M:%S)" "$*" | tee -a "$RUN_LOG"; }

have() { command -v "$1" >/dev/null 2>&1; }
PY=python3; have python3 || PY=python

ESC=$'\033'
C_RESET="$ESC[0m"; C_DIM="$ESC[2m"; C_BOLD="$ESC[1m"

rgb() { printf '%s38;2;%d;%d;%dm' "$ESC" "$1" "$2" "$3"; }

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
PARALLEL=""
have parallel && PARALLEL="parallel"

logf "deps: figlet=${FIGLET:-fallback-python} toilet=${TOILET:-fallback-python} lolcat=${LOLCAT:-fallback-python/rainbow.py} parallel=${PARALLEL:-fallback-xargs}"

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

# Animated hue sweep of the word RAiNBOW
animated_brand() {
  if [ "$QUIET" = "1" ] || [ ! -t 1 ]; then
    printf '%sRAiNBOW_Hello-World%s\n' "$C_BOLD" "$C_RESET"
    return
  fi
  local msg="RAiNBOW_Hello-World"
  local n=${#msg}
  local frame
  for frame in 0 1 2 3 4 5 6 7; do
    printf '%s' "$CLEAR"
    printf '  %s' "$C_BOLD"
    local i
    for (( i = 0; i < n; i++ )); do
      local ch="${msg:$i:1}"
      local h
      h=$(( ( (frame * 24 + i * 8) % 360 ) ))
      printf '%s' "$(rgb 255 255 255)"
      printf '%s' "$ch"
    done
    printf '%s\n' "$C_RESET"
    printf '  %s%06d+ languages on the bar  .  %s byte-balanced rainbow%s\n' \
      "$C_DIM" "$CORE_COUNT" "$C_RESET" "$C_RESET"
    sleep 0.08
  done
  printf '%s' "$CLEAR"
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

roll_call() {
  local shown=0
  printf '  %sBooting %s core languages%s\n' "$C_DIM" "$CORE_COUNT" "$C_RESET"
  while IFS= read -r name; do
    [ -z "$name" ] && continue
    shown=$((shown + 1))
    if [ "$QUIET" = "1" ]; then continue; fi
    if [ "$shown" -le "$MAX_SHOWN" ]; then
      printf '    %s+%s %s\n' "$(rgb 120 220 120)" "$C_RESET" "$name"
    fi
  done < <(core_names)
  printf '    %s... +%d more core languages%s\n' "$C_DIM" \
    "$((CORE_COUNT - shown > 0 ? CORE_COUNT - shown : 0))" "$C_RESET"
  printf '    %s+%s full-layer languages present in hello/full (%s files)\n' \
    "$(rgb 120 220 120)" "$C_RESET" "$FULL_COUNT"
  printf '\n'
}

roll_call

# --------------------------------------------------------------------------
# 3. parallel execution of every core language we know how to run
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

  run_one() {
    # $1 = language, $2 = command, $3 = path
    local name="$1" cmd="$2" path="$3"
    local out
    out=$(eval "$cmd" 2>&1 | head -c 400)
    if [ -n "$(printf '%s' "$out" | tr -d '[:space:]')" ]; then
      printf '%s\t%s\t%s\n' "$name" "ok" "$(printf '%s' "$out" | tr '\n' ' ' | tr '\t' ' ')" \
        >> "$OUT_DIR/results.tsv"
    else
      printf '%s\t%s\t%s\n' "$name" "silent" "-" >> "$OUT_DIR/results.tsv"
    fi
  }
  export -f run_one
  : > "$OUT_DIR/results.tsv"

  if [ -n "$PARALLEL" ]; then
    awk -F'\t' '{print $1 "\t" $2 "\t" $3}' "$RUNNERS_FILE" \
      | parallel -j "$JOBS" -k 'run_one {}' >/dev/null 2>>"$RUN_LOG" || true
  else
    while IFS=$'\t' read -r name cmd path; do
      printf '%s\0%s\0%s\0' "$name" "$cmd" "$path"
    done < "$RUNNERS_FILE" \
      | xargs -0 -P "$JOBS" -I{} -n1 true 2>/dev/null || true
    # xargs has no 3-tuple split, so fall back to a plain parallel loop
    while IFS=$'\t' read -r name cmd path; do
      printf '%s\t%s\t%s\n' "$name" "$cmd" "$path"
    done < "$RUNNERS_FILE" \
      | xargs -d '\n' -P "$JOBS" -I{} bash -c 'run_one {}' >/dev/null 2>>"$RUN_LOG" || true
  fi

  OK_COUNT=$(grep -c "	ok	" "$OUT_DIR/results.tsv" 2>/dev/null || echo 0)
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
eggs=$(find hello/full -type f 2>/dev/null | grep -Ei 'brainfuck|whitespace|malbolge|intercal|lolcode|befunge|piet|forth|smalltalk|chef' | head -5)
if [ -n "$eggs" ]; then
  printf '\n  %sEaster egg: esoteric corner of hello/full/%s\n' "$C_DIM" "$C_RESET"
  printf '%s\n' "$eggs" | while IFS= read -r f; do
    printf '    %s%s%s\n' "$(rgb 255 180 60)" "$f" "$C_RESET"
    sed -n '1,6p' "$f" 2>/dev/null | sed 's/^/      /'
  done
  printf '    %sinterpreters: https://esolangs.org/  https://rosettacode.org/%s\n' \
    "$C_DIM" "$C_RESET"
fi

# --------------------------------------------------------------------------
# 8. the rainbow language bar + final rainbow Hello World!
# --------------------------------------------------------------------------
printf '\n'
"$PY" scripts/rainbow.py --bar --width 108 2>/dev/null || true

printf '\n'
final_rainbow_hello() {
  local msg="Hello World!"
  local i n=${#msg}
  for (( i = 0; i < n; i++ )); do
    local h=$(( (i * 360 / n) ))
    printf '%s%s%s' "$(rgb $((255 - h / 4)) $((120 + h / 3)) $((60 + h / 2))" \
      "${msg:$i:1}" "$C_RESET"
  done
  printf '\n'
}

if [ "$QUIET" = "1" ] || [ ! -t 1 ]; then
  printf 'Hello World!\n'
else
  final_rainbow_hello
  printf '%s  %s languages on the bar  .  %s files in the repo%s\n' \
    "$C_DIM" "$CORE_COUNT" "$TOTAL_COUNT" "$C_RESET"
  printf '%s  https://github.com/quxianp/RAiNBOW_Hello-World%s\n' "$C_DIM" "$C_RESET"
fi

log "=== run.sh done ==="
exit 0
