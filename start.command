#!/bin/bash
# macOS / Linux launcher: double-click (macOS) or run ./start.sh. Creates a private .venv on first run.
cd "$(dirname "$0")" || exit 1
PORT="${1:-8120}"

find_python() {
  for c in python3.13 python3.12 python3.11 python3.10 \
           /opt/homebrew/bin/python3 /usr/local/bin/python3 "$HOME/.homebrew/bin/python3" \
           "$HOME/miniforge3/bin/python3" "$HOME/miniconda3/bin/python3" "$HOME/anaconda3/bin/python3" \
           /Library/Frameworks/Python.framework/Versions/Current/bin/python3 python3; do
    p=$(command -v "$c" 2>/dev/null) || continue
    if "$p" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
      echo "$p"; return 0
    fi
  done
  return 1
}

if [ ! -x .venv/bin/python ]; then
  PY=$(find_python) || {
    echo "Python 3.10 or newer is required. Install it from https://www.python.org/downloads/ and try again."
    read -r -p "Press Return to close." _; exit 1; }
  echo "First start: creating .venv with $PY and installing dependencies (one time, about a minute)…"
  "$PY" -m venv .venv && ./.venv/bin/pip install -q --upgrade pip && ./.venv/bin/pip install -q -r requirements.txt || {
    echo "Installation failed. Check your internet connection and try again."; rm -rf .venv
    read -r -p "Press Return to close." _; exit 1; }
fi
exec ./.venv/bin/python serve.py "$PORT"
