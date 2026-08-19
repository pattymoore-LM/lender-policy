#!/usr/bin/env python3
"""Regenerate the FALLBACK_TRIGGERS list in pull-snapshot.js from a real snapshot.

    python3 update-fallback-triggers.py <snapshot.json>

Why this exists: pull-snapshot.js carries a hardcoded topic list, used when it
can't read the live one off the page. That list is dated, and a dated list rots.
Run this after any refresh and the fallback tracks reality instead of drifting
further from it every month.

Prints what changed. Exits 0 if nothing did.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = HERE / "pull-snapshot.js"


def wrap(triggers, width=76):
    lines, cur = [], "    "
    for t in triggers:
        piece = f"'{t}', "
        if len(cur) + len(piece) > width:
            lines.append(cur.rstrip())
            cur = "    "
        cur += piece
    lines.append(cur.rstrip().rstrip(","))
    return "\n".join(lines)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)

    snap = json.loads(Path(sys.argv[1]).read_text())
    triggers = snap["triggers"]
    snap_date = snap.get("snapshotDate", "unknown")

    src = TARGET.read_text()
    m = re.search(r"const FALLBACK_TRIGGERS = \[\n(.*?)\n  \];", src, re.S)
    if not m:
        sys.exit("could not find FALLBACK_TRIGGERS in pull-snapshot.js")

    current = re.findall(r"'([a-z0-9_]+)'", m.group(1))
    added = [t for t in triggers if t not in current]
    removed = [t for t in current if t not in triggers]

    if not added and not removed:
        print(f"fallback already current: {len(current)} topics, snapshot {snap_date}")
        return

    src = src[:m.start(1)] + wrap(triggers) + src[m.end(1):]
    # keep the dated comment honest, wherever the date is mentioned
    src = re.sub(r"as at \d{2}/\d{2}/\d{4}",
                 f"as at {snap_date[8:10]}/{snap_date[5:7]}/{snap_date[:4]}", src)
    TARGET.write_text(src)

    print(f"fallback updated: {len(current)} -> {len(triggers)} topics (snapshot {snap_date})")
    if added:
        print("  added:  ", ", ".join(added))
    if removed:
        print("  removed:", ", ".join(removed))
    print("\nBump the plugin version in BOTH manifests and push, or nobody gets it.")


if __name__ == "__main__":
    main()
