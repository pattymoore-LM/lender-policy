#!/usr/bin/env python3
"""Render the lender desk sheet (BDM contacts, policy source links, SLA docs) from the snapshot.

Usage: python3 render_desk.py <snapshot.json>
Writes ~/.claude/lender-policy/desk.md. Stdlib only.
"""
import json, os, sys, datetime

KB = os.path.expanduser(
    os.environ.get("LENDER_POLICY_KB", "~/.claude/lender-policy")
)  # override with: export LENDER_POLICY_KB=/path/to/kb
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import lender_name, au_date  # reuse the same name/date handling


def main(snapshot_path):
    snap = json.load(open(snapshot_path))
    prov = [p for p in snap["provenance"] if not p.get("offPanel")]
    prov.sort(key=lambda p: lender_name(p["lender"]).lower())

    out = [
        "# Lender desk sheet (Quickli snapshot)",
        "",
        f"BDM and support contacts, policy source links and SLA documents, captured "
        f"{au_date(snap['snapshotDate'])} alongside the policy pull. Contact details are "
        "Quickli's record and can go stale; confirm before quoting them to a client.",
        "",
        "**Do not share outside this machine** (same rule as the rest of this KB).",
        "",
    ]

    for p in prov:
        name = lender_name(p["lender"])
        contacts = p.get("brokersContact") or []
        links = []
        if p.get("policySourceUrl"):
            links.append(f"[policy source]({p['policySourceUrl']})")
        if p.get("slaSourceUrl"):
            links.append(f"[SLA source]({p['slaSourceUrl']})")
        sla_desc = (p.get("slaDescription") or "").strip()
        rates = (p.get("ratesDescription") or "").strip()
        upcoming = (p.get("upcomingRateChange") or "").strip() if isinstance(p.get("upcomingRateChange"), str) else ""

        if not (contacts or links or sla_desc or rates or upcoming):
            continue

        out.append(f"## {name}")
        out.append("")
        if links:
            out.append("Links: " + " · ".join(links))
            out.append("")
        if sla_desc:
            out.append(f"SLA note ({au_date(p.get('slaUpdateDate'))}): {sla_desc}")
            out.append("")
        if rates:
            out.append(f"Rates: {rates}")
            out.append("")
        if upcoming:
            out.append(f"Upcoming rate change: {upcoming}")
            out.append("")
        if contacts:
            out.append("| Contact | Role | Email | Phone |")
            out.append("|---|---|---|---|")
            for c in contacts:
                if not isinstance(c, dict):
                    continue
                out.append("| {} | {} | {} | {} |".format(
                    (c.get("brokerName") or "").strip() or "-",
                    (c.get("contactRole") or "").strip() or "-",
                    (c.get("brokerEmail") or "").strip() or "-",
                    (c.get("brokerPhoneNumber") or "").strip() or "-",
                ))
            out.append("")

    with open(os.path.join(KB, "desk.md"), "w") as f:
        f.write("\n".join(out))
    sections = sum(1 for l in out if l.startswith("## "))
    print(f"Wrote desk.md: {sections} lenders with contact or link data.")


if __name__ == "__main__":
    main(sys.argv[1])
