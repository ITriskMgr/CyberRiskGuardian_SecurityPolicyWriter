#!/usr/bin/env python3
"""Copy the Writer engine (crg_writer/) into a CyberRiskGuardian Desktop folder.

Usage:  python3 tools/sync_to_desktop.py /path/to/CyberRiskGuardian_ThreatIntel/desktop/app

The desktop helper (serve.py) imports crg_writer from its own folder. This repository is the source of the
engine; the desktop repository carries a copy. The script refuses a folder without serve.py, replaces the
old copy entirely, and checks that the desktop's js/version.js names the same Writer version.
© 2026 Marc-André Léger. CC BY-NC 4.0
"""
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "crg_writer"


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    dest = pathlib.Path(argv[1]).expanduser().resolve()
    if not (dest / "serve.py").exists():
        print(f"{dest} is not a CyberRiskGuardian Desktop folder (no serve.py).")
        return 1
    target = dest / "crg_writer"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(SRC, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    ver = re.search(r'VERSION = "([\d.]+)"', (SRC / "__init__.py").read_text()).group(1)
    js = (dest / "js" / "version.js").read_text(encoding="utf-8")
    m = re.search(r"WRITER_VERSION = '([\d.]+)'", js)
    print(f"crg_writer {ver} copied to {target}")
    if not m or m.group(1) != ver:
        print(f"WARNING: js/version.js says WRITER_VERSION {m and m.group(1)!r}; update it (tools/version_check.py will fail).")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
