#!/usr/bin/env bash
# RAiNBOW_Hello-World -- install optional helpers, never fail the build.
#
# Everything here is best-effort: a missing pretty-printer only means the
# demo falls back to scripts/rainbow.py (pure python, 24-bit true colour).

set -u
cd "$(dirname "$0")" || exit 1
mkdir -p logs

LOG="logs/install_deps.log"
: > "$LOG"

log()  { printf '%s %s\n' "$(date +%H:%M:%S)" "$*" | tee -a "$LOG"; }
have() { command -v "$1" >/dev/null 2>&1; }
ok()   { log "OK      $*"; }
miss() { log "MISSING $* (fallback in use)"; }
try()  { if "$@" >>"$LOG" 2>&1; then ok "$*"; else miss "$*"; fi; }

log "=== install_deps start ==="

# ---- core interpreters --------------------------------------------------
log "--- interpreters ---"
for tool in python3 python ruby perl php node lua tclsh jq awk sed perl; do
  if have "$tool"; then ok "$tool -> $(command -v "$tool")"; else miss "$tool"; fi
done

# ---- system package manager --------------------------------------------
SUDO=""
if [ "$(id -u)" -ne 0 ] && have sudo; then SUDO="sudo"; fi

install_pkg() {
  if have apt-get; then
    $SUDO apt-get update -qq >>"$LOG" 2>&1
    $SUDO apt-get install -y -qq "$@" >>"$LOG" 2>&1
  elif have apk; then
    $SUDO apk add --no-cache "$@" >>"$LOG" 2>&1
  elif have dnf; then
    $SUDO dnf install -y "$@" >>"$LOG" 2>&1
  elif have brew; then
    brew install "$@" >>"$LOG" 2>&1
  else
    return 1
  fi
}

# ---- ASCII art ----------------------------------------------------------
log "--- ascii art ---"
if have figlet; then ok "figlet"; else
  install_pkg figlet && ok "figlet (apt)" || miss "figlet"
fi
if have toilet; then ok "toilet"; else
  install_pkg toilet && ok "toilet (apt)" || miss "toilet"
fi

# ---- rainbow colouriser -------------------------------------------------
log "--- colour ---"
if have lolcat; then ok "lolcat"; else
  if have gem; then try gem install --no-document lolcat; fi
  have lolcat && ok "lolcat" || miss "lolcat (scripts/rainbow.py is the fallback)"
fi

# ---- GNU parallel -------------------------------------------------------
if have parallel; then ok "parallel"; else
  install_pkg parallel && ok "parallel (apt)" || miss "parallel (xargs -P is the fallback)"
fi

# ---- esolang interpreters (best effort, tiny set) -----------------------
log "--- esolangs ---"
for pkg in brainfuck whitespace-interpreter intercal ngrok; do
  install_pkg "$pkg" >/dev/null 2>&1 && ok "$pkg" || miss "$pkg"
done

# ---- audio --------------------------------------------------------------
log "--- audio ---"
for tool in afplay aplay paplay pwplay ffplay; do
  have "$tool" && ok "$tool" || miss "$tool"
done

# ---- recording / screenshots -------------------------------------------
log "--- recording ---"
install_pkg ffmpeg >/dev/null 2>&1 && ok "ffmpeg" || miss "ffmpeg"
if have vhs; then ok "vhs"; else
  install_pkg vhs >/dev/null 2>&1 && ok "vhs" || miss "vhs (GitHub Action installs it)"
fi

# ---- github-linguist (optional, used by verify_languages.py) -----------
if have github-linguist; then ok "github-linguist"; else
  have gem && { try gem install --no-document github-linguist; } || miss "github-linguist"
  have github-linguist && ok "github-linguist" || miss "github-linguist (python simulation used)"
fi

# ---- python deps --------------------------------------------------------
log "--- python ---"
PIP=""
have pip3 && PIP="pip3" || { have pip && PIP="pip"; }
if [ -n "$PIP" ]; then
  for mod in yaml requests bs4 matplotlib pillow playwright; do
    if python3 -c "import $mod" >/dev/null 2>&1 || python -c "import $mod" >/dev/null 2>&1; then
      ok "python module $mod"
    else
      try $PIP install --quiet "$mod"
    fi
  done
else
  miss "pip (python extras skipped)"
fi

log "=== install_deps done; run.sh degrades gracefully for anything missing ==="
cat "$LOG"
