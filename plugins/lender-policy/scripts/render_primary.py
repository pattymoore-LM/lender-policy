#!/usr/bin/env python3
"""Render a primary-source lender policy pull into the KB.

Usage: python3 render_primary.py <lender-pull.json>
Input:  {lender, source, channel, pulledAt, chapters:[{id,title,content}]}
Output: primary/<lender>/<lender>-credit-policy.md  (one file, chapter headings)
        plus a line in primary/INDEX.md
Primary source outranks the Quickli snapshot: it is the lender's own manual.
Stdlib only.
"""
import json, os, sys, hashlib, datetime

KB = os.path.expanduser(
    os.environ.get("LENDER_POLICY_KB", "~/.claude/lender-policy")
)  # override with: export LENDER_POLICY_KB=/path/to/kb
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import lender_name, au_date


def main(path):
    d = json.load(open(path))
    slug = d["lender"]
    name = d.get("displayName") or lender_name(slug)
    chapters = d["chapters"]
    raw = json.dumps(chapters, sort_keys=True)
    sha = hashlib.sha256(raw.encode()).hexdigest()[:16]
    outdir = os.path.join(KB, "primary", slug)
    os.makedirs(outdir, exist_ok=True)

    lines = [
        f"# {name} credit policy (primary source)",
        "",
        f"> Pulled {au_date(d['pulledAt'])} from {d['source']}"
        + (f" (file: `{d['sourceFile']}`, {d['pages']} pages)" if d.get('sourceFile') else
           ", direct from the lender's own broker portal")
        + f". sha256: {sha}",
        "> This is the lender's own manual, so it outranks the Quickli snapshot in "
        f"`lenders/{slug}.md`. Where the two disagree, this wins and the Quickli entry is the "
        "summary. Still verify anything load-bearing against the live portal.",
        "",
        "## Contents",
        "",
    ]
    for c in chapters:
        anchor = c["title"].lower().replace(" ", "-")
        for ch in "().,–—/&%":
            anchor = anchor.replace(ch, "")
        lines.append(f"- [{c['title']}](#{anchor})")
    lines.append("")

    for c in chapters:
        lines.append(f"## {c['title']}")
        lines.append("")
        lines.append(c["content"].strip())
        lines.append("")

    out_path = os.path.join(outdir, f"{slug}-credit-policy.md")
    with open(out_path, "w") as f:
        f.write("\n".join(lines))

    # Rebuild primary/INDEX.md from whatever pulls exist.
    entries = []
    pdir = os.path.join(KB, "primary")
    for s in sorted(os.listdir(pdir)):
        sub = os.path.join(pdir, s)
        if not os.path.isdir(sub):
            continue
        js = [f for f in os.listdir(sub) if f.endswith(".json")]
        if not js:
            continue
        js.sort()
        dd = json.load(open(os.path.join(sub, js[-1])))
        md = [f for f in os.listdir(sub) if f.endswith(".md")]
        # always point at the policy file, not a companion note that sorts earlier
        md.sort(key=lambda f: (not f.endswith("-credit-policy.md"), f))
        chars = sum(len(x["content"]) for x in dd["chapters"])
        entries.append((dd.get("displayName") or lender_name(s), s, len(dd["chapters"]), chars,
                        au_date(dd["pulledAt"]), dd["source"], md[0] if md else ""))

    with open(os.path.join(pdir, "INDEX.md"), "w") as f:
        f.write("# Primary-source lender policy\n\n")
        f.write("Credit policy manuals straight from the source: each lender's own broker "
                "portal or the policy document they issue to brokers. **These outrank the Quickli "
                "snapshot** in `../lenders/*.md`: Quickli is a summary, this is the source. Same "
                "sharing rule as the rest of the KB, do not share off this machine.\n\n")
        f.write("Helia is the LMI insurer, not a lender. Its guidelines apply on top of the "
                "lender's own policy on any deal insured by Helia, so check it whenever LMI is "
                "in play regardless of which lender is chosen.\n\n")
        f.write("| Lender | Chapters | Size | Pulled | File |\n|---|---|---|---|---|\n")
        for nm, s, nch, chars, pulled, src, mdf in entries:
            f.write(f"| {nm} | {nch} | {chars // 1000}k chars | {pulled} | `{s}/{mdf}` |\n")

    print(f"{name}: {len(chapters)} chapters, {sum(len(c['content']) for c in chapters)//1000}k chars -> {out_path}")


if __name__ == "__main__":
    main(sys.argv[1])
