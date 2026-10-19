#!/bin/bash
# macOS launcher: double-click. Creates a private virtual environment on first run.
cd "$(dirname "$0")" || exit 1
if [ ! -d .venv ]; then
  echo "First start: installing dependencies into .venv (one time)…"
  python3 -m venv .venv && ./.venv/bin/pip install -q -r requirements.txt || { echo "Installation failed."; read -r; exit 1; }
fi
./.venv/bin/python serve.py "${1:-8120}"
