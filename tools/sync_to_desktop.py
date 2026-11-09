#!/usr/bin/env python3
"""Keep the Writer engine (crg_writer/) in step with the CyberRiskGuardian Desktop copy — Writer 0.1.1 (NV-W01).

Author decision D1 (8 November 2026): **the desktop copy is canonical.** This script therefore syncs in that
direction by default — it copies the desktop's `crg_writer/` INTO this repository — and never overwrites a tree that
has diverged from the other side without being told to:

    python3 tools/sync_to_desktop.py /path/to/CyberRiskGuardian_ThreatIntel/desktop/app            # desktop → here
    python3 tools/sync_to_desktop.py /path/to/.../desktop/app --to-desktop                        # here → desktop (legacy direction)
    python3 tools/sync_to_desktop.py /path/to/.../desktop/app --check                             # compare only, exit 1 on a difference
    python3 tools/sync_to_desktop.py /path/to/.../desktop/app --force                             # overwrite even a diverged copy

Before copying, both trees are hashed (the same hash as desktop/app/tools/writer_tree_hash.py: SHA-256 over
"relative path\\0SHA-256 of the file" for every *.py, line endings normalised) and compared with the hash the
desktop records beside WRITER_VERSION in js/version.js (WRITER_TREE_HASH). The script:
  * does nothing when the trees are identical;
  * refuses to overwrite when the destination tree has changed since the two were last in step (its hash is not the
    one js/version.js records), prints the unified diff file by file, and exits 2 — `--force` overrides;
  * after a copy, checks that the Writer version of this package and WRITER_VERSION agree (exit 1 otherwise), and
    reminds that js/version.js must record the new tree hash (`python3 tools/writer_tree_hash.py --write`).
© 2026 Marc-André Léger. CC BY-NC 4.0
"""
import difflib
import hashlib
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
HERE = ROOT / "crg_writer"


def tree_hash(folder: pathlib.Path) -> str:
    h = hashlib.sha256()
    for p in sorted(x for x in folder.rglob("*.py") if "__pycache__" not in x.parts):
        data = p.read_bytes().replace(b"\r\n", b"\n")
        h.update(p.relative_to(folder).as_posix().encode("utf-8") + b"\0" + hashlib.sha256(data).hexdigest().encode() + b"\n")
    return h.hexdigest()


def version_of(folder: pathlib.Path) -> str:
    m = re.search(r'VERSION = "([\d.]+)"', (folder / "__init__.py").read_text(encoding="utf-8"))
    return m.group(1) if m else "?"


def recorded_hash(dest: pathlib.Path) -> str | None:
    js = dest / "js" / "version.js"
    if not js.exists():
        return None
    m = re.search(r"WRITER_TREE_HASH = '([0-9a-f]{64})'", js.read_text(encoding="utf-8"))
    return m.group(1) if m else None


def show_diff(src: pathlib.Path, dst: pathlib.Path) -> int:
    """Print the unified diff of the two trees (what copying src over dst would change); return the file count."""
    files = sorted({p.relative_to(src).as_posix() for p in src.rglob("*.py") if "__pycache__" not in p.parts}
                   | {p.relative_to(dst).as_posix() for p in dst.rglob("*.py") if "__pycache__" not in p.parts})
    n = 0
    for rel in files:
        a, b = dst / rel, src / rel
        at = a.read_text(encoding="utf-8").splitlines(keepends=True) if a.exists() else []
        bt = b.read_text(encoding="utf-8").splitlines(keepends=True) if b.exists() else []
        if at == bt:
            continue
        n += 1
        sys.stdout.writelines(difflib.unified_diff(at, bt, fromfile=f"{dst.name}/{rel} (current)", tofile=f"{src.name}/{rel} (incoming)", n=2))
    return n


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    flags = {a for a in argv[1:] if a.startswith("--")}
    if len(args) != 1:
        print(__doc__)
        return 2
    dest = pathlib.Path(args[0]).expanduser().resolve()
    if not (dest / "serve.py").exists():
        print(f"{dest} is not a CyberRiskGuardian Desktop folder (no serve.py).")
        return 1
    desk = dest / "crg_writer"
    to_desktop = "--to-desktop" in flags
    src, dst = (HERE, desk) if to_desktop else (desk, HERE)
    h_src, h_dst = tree_hash(src), tree_hash(dst)
    rec = recorded_hash(dest)
    print(f"desktop copy  {version_of(desk)}  {tree_hash(desk)[:16]}…   (js/version.js records {rec[:16] + '…' if rec else 'no hash'})")
    print(f"this repo     {version_of(HERE)}  {tree_hash(HERE)[:16]}…")
    if h_src == h_dst:
        print("The two copies are identical; nothing to do.")
        return 0
    if "--check" in flags:
        n = show_diff(src, dst)
        print(f"{n} file(s) differ.")
        return 1
    # The destination has diverged when its hash is not the one the desktop recorded the last time the trees were in step.
    diverged = rec is None or h_dst != rec if not to_desktop else (rec is None or h_dst != rec)
    if diverged and "--force" not in flags:
        print(f"REFUSED: the destination ({'desktop copy' if to_desktop else 'this repository'}) has changed since the two copies were last "
              "in step — copying would silently revert those changes. The differences:\n")
        show_diff(src, dst)
        print("\nRun again with --force to overwrite anyway (the author's decision D1: the desktop copy is canonical).")
        return 2
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    print(f"crg_writer {version_of(src)} copied {'to the desktop' if to_desktop else 'into this repository'} ({tree_hash(dst)[:16]}…).")
    js = (dest / "js" / "version.js").read_text(encoding="utf-8")
    m = re.search(r"WRITER_VERSION = '([\d.]+)'", js)
    if not m or m.group(1) != version_of(dst):
        print(f"WARNING: js/version.js says WRITER_VERSION {m and m.group(1)!r}; the engine is {version_of(dst)!r} — update it (tools/version_check.py fails otherwise).")
        return 1
    if to_desktop and rec != tree_hash(desk):
        print("Reminder: record the new tree hash in the desktop — cd desktop/app && python3 tools/writer_tree_hash.py --write — and bump WRITER_VERSION.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
