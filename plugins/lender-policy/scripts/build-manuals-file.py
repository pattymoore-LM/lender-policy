#!/usr/bin/env python3
"""Combine the primary/ credit manuals into one file for a Claude/ChatGPT Project.

    python3 build-manuals-file.py [--kb ~/.claude/lender-policy] [-o OUT]

Pairs with the Quickli file that pull-and-build.js produces. Two files in a
Project gives you both layers, with the manual outranking the summary.

Deliberately EXCLUDES the servicing-calculator dumps. Those are cell-by-cell
workbook extractions — the right input for a servicing engine, and pure noise
for "what is their casual income policy". Including them costs ~4.9M tokens and
buys nothing for a policy question.

Stdlib only.
"""
import argparse
import datetime
import os
import re
import sys
from pathlib import Path

HEADER = """# Lender credit policy manuals

The lenders' own credit policy documents, pulled from their broker portals.

**These outrank the Quickli summary.** Where this file and the Quickli policy
file disagree, this one wins — Quickli tells you a lender's position, the manual
tells you the conditions on it. Say which source an answer came from, and when
they differ, lead with this one and note that the summary differs.

Quote the wording word for word rather than paraphrasing. If a lender is not in
this file, say so — do not infer their manual from another lender's.

Insurer guidelines (Helia, QBE) are not a lender's policy. They apply on top of
whichever lender is chosen, so check them whenever the deal is above 80% LVR.

Research, not advice. The recommendation belongs to the broker after looking at
the client.

Not included: servicing calculator workbook extractions. Those answer "what
number does this lender's calculator produce", which is a different question and
belongs in a calculator, not here.

---

"""


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kb", default=os.environ.get("LENDER_POLICY_KB",
                                                   "~/.claude/lender-policy"))
    ap.add_argument("-o", "--out", default=None)
    args = ap.parse_args()

    kb = Path(os.path.expanduser(args.kb))
    primary = kb / "primary"
    if not primary.is_dir():
        sys.exit(f"no primary/ layer at {primary}")

    today = datetime.date.today().isoformat()
    out_path = Path(args.out) if args.out else Path.home() / "Downloads" / f"lender-manuals-{today}.md"

    docs = []
    for f in sorted(primary.rglob("*.md")):
        if f.name in ("INDEX.md", "PORTALS.md", "NOTE.md"):
            continue
        # the calculator dumps live in *-calc directories
        if "-calc" in f.parent.name:
            continue
        docs.append(f)

    if not docs:
        sys.exit("no credit manuals found (only calculator dumps?)")

    parts = [HEADER, "## Documents in this file\n\n"]
    for f in docs:
        parts.append(f"- {f.parent.name} — `{f.name}`\n")
    parts.append("\n---\n\n")

    for f in docs:
        text = f.read_text(errors="ignore")
        # Demote the document's own headings below our `##` lender level, so the
        # structure stays unambiguous. Same defect that bit the Quickli renderer.
        text = re.sub(r"^(#{1,6})(\s)",
                      lambda m: "#" * min(len(m.group(1)) + 2, 6) + m.group(2),
                      text, flags=re.M)
        parts.append(f"## {f.parent.name}\n\n{text.strip()}\n\n---\n\n")

    body = "".join(parts)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(body)

    print(f"{len(docs)} manuals -> {out_path}")
    print(f"  {len(body)/1024/1024:.2f} MB, roughly {int(len(body)/3.5):,} tokens")
    if len(body) / 3.5 > 2_000_000:
        print("  WARNING: over ChatGPT's 2M token ceiling for one file. Claude is fine;")
        print("  for ChatGPT, split it or drop the lenders you rarely use.", file=sys.stderr)


if __name__ == "__main__":
    main()
