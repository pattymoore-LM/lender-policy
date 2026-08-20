#!/usr/bin/env python3
"""Render a Quickli policy snapshot JSON into a lender-policy knowledge base.

Usage:
  python3 render.py <snapshot.json> [--kb ~/.claude/lender-policy]

Reads the raw snapshot (produced by pull-snapshot.js, or by the /policy refresh
browser pull) and writes:

  lenders/<slug>.md              one file per lender, canonical ## Topic headings
  INDEX.md                       freshness table + rules
  topics.md                      trigger-key -> plain-English topic map
  <snapshot dir>/manifest.json   per-lender counts, for regression comparison

The identical-headings layout is the whole trick: because every lender file uses
the same `## Topic` headings, a grep for one heading across lenders/*.md IS a
cross-lender comparison. Nothing has to load 3,000+ policy blocks to answer a
question.

Stdlib only. No third-party packages, nothing to install.
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_KB = os.path.expanduser(
    os.environ.get("LENDER_POLICY_KB", "~/.claude/lender-policy")
)  # the other scripts read LENDER_POLICY_KB too; --kb wins over both


def load_lender_names():
    """Slug -> display name. Anything not listed falls back to title-case, so an
    unknown or newly-added lender still renders correctly."""
    path = os.path.join(HERE, "lender_names.json")
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


LENDER_NAMES = load_lender_names()

# Trigger key -> plain-English topic heading. This is Quickli's API enum
# vocabulary, not policy content. Anything not listed gets title-cased.
TOPIC_NAMES = {
    "acceptable_security_type": "Acceptable Security Type",
    "payg": "PAYG Income", "casual": "Casual Income", "commission": "Commission Income",
    "bonus": "Bonus Income", "overtime": "Overtime Income",
    "essential_overtime": "Essential Services Overtime",
    "essential_services": "Essential Services Workers",
    "frequent_bonus_payments": "Frequent Bonus Payments",
    "contract_employment": "Contract Employment", "family_employment": "Family Employment",
    "probation": "Probation", "parental_leave": "Parental Leave",
    "second_job": "Second Job", "car_allowance": "Car Allowance",
    "salary_sacrifice": "Salary Sacrifice", "fully_maintained_vehicle": "Fully Maintained Vehicle",
    "novated_lease": "Novated Lease", "foreign": "Foreign Income",
    "self_employed_income": "Self-Employed Income", "self_employed_addbacks": "Self-Employed Add-backs",
    "simple_self_employed": "Simple Self-Employed / Fast-Track", "low_doc": "Low Doc / Alt Doc",
    "company_borrowers": "Company Borrowers", "company_debt": "Company Debt",
    "investment": "Investment Income", "interest": "Interest Income",
    "annuities": "Annuities", "margin_loan": "Margin Loans",
    "social_security": "Social Security Income", "family_tax_benefit": "Family Tax Benefit",
    "parenting_payments": "Parenting Payments", "carers_income": "Carer's Income",
    "pension": "Pension Income", "child_maintenance": "Child Maintenance",
    "tax_free": "Tax-Free Income", "boarder_income": "Boarder Income",
    "rental_income": "Rental Income", "rental_reliance": "Rental Reliance",
    "rental_yield": "Rental Yield Caps", "rental_holiday": "Holiday / Short-Stay Rental",
    "rental_prestige": "Prestige Property Rental", "negative_gearing": "Negative Gearing",
    "net_rental_affordability_scheme": "NRAS", "notional_rent": "Notional Rent",
    "living_expenses": "Living Expenses (HEM)", "dependants": "Dependants",
    "hecs": "HECS / HELP Debt", "buy_now_pay_later": "Buy Now Pay Later (BNPL)",
    "overdraft": "Overdrafts", "loc": "Line of Credit",
    "common_debt_reducer": "Common Debt Reducer", "credit_scoring": "Credit Scoring",
    "credit_impairment": "Credit Impairment", "dti": "DTI (Debt-to-Income)",
    "lti": "LTI (Loan-to-Income)", "nsr": "NSR (Net Service Ratio)",
    "nms": "NMS (Net Monthly Surplus)", "max_capacity": "Maximum Borrowing Capacity",
    "lvr": "LVR Limits", "lmi_waiver_for_professionals": "LMI Waiver for Professionals",
    "genuine_savings": "Genuine Savings", "first_home_guarantee": "First Home Guarantee (FHBG)",
    "family_guarantor": "Family Guarantor", "gifted_funds": "Gifted Funds",
    "cash_out": "Cash Out", "cashback_offers": "Cashback Offers",
    "refinance_statement_requirements": "Refinance Statement Requirements",
    "streamlined_refinance": "Streamlined Refinance", "fastrefi": "FastRefi",
    "fixed_rates": "Fixed Rates", "rate_lock_policy": "Rate Lock",
    "extended_loan_term": "Extended Loan Term", "exit_strategy": "Exit Strategy",
    "pre_approvals": "Pre-Approvals", "construction_loans": "Construction Loans",
    "bridging_loans": "Bridging Loans", "vacant_land": "Vacant Land",
    "maximum_land_size": "Maximum Land Size", "minimum_security_size": "Minimum Security Size",
    "non_australian_resident": "Non-Australian Residents", "visa_classes": "Visa Classes",
    "verification_of_identity": "Verification of Identity (VOI)",
    "ethical_lending": "Ethical Lending", "policy_niches": "Policy Niches",
    "smsf_acceptable_contributions": "SMSF Acceptable Contributions",
    "smsf_applicant_type": "SMSF Applicant Type",
    "smsf_liquid_asset_position": "SMSF Liquid Asset Position",
    "smsf_max_lvr": "SMSF Maximum LVR",
    "slas": "SLAs / Turnaround",
}


def topic_name(key):
    return TOPIC_NAMES.get(key, key.replace("_", " ").title())


def lender_name(slug):
    return LENDER_NAMES.get(slug, slug.replace("_", " ").title())


def au_date(iso):
    if not iso:
        return "unknown"
    try:
        return datetime.datetime.fromisoformat(iso.replace("Z", "+00:00")).strftime("%d/%m/%Y")
    except (ValueError, AttributeError):
        return iso


def demote_headings(text):
    """Push any markdown heading inside Quickli's own content below our own.

    We use `#` for the lender and `##` for the topic. Quickli's policy text
    carries its own headings — "Acceptable Evidence", "Calculation:" — and a
    `##` in there is indistinguishable from a topic heading. That silently
    truncates every extraction: an awk that stops at the next `^## ` stops at
    "Acceptable Evidence" and drops the rest of the lender's real policy.
    Found 20/08/2026 on Bank Australia's Family Employment section.

    Demoting by two keeps the rendering identical to a reader while making the
    structure unambiguous to anything scanning by heading level.
    """
    def bump(m):
        return "#" * min(len(m.group(1)) + 2, 6) + m.group(2)
    return re.sub(r"^(#{1,6})(\s)", bump, text, flags=re.M)


def clean_content(text):
    # Cosmetic only: collapse Quickli's &nbsp; spacer lines; never touch policy wording.
    text = re.sub(r"^\s*&nbsp;\s*$", "", text, flags=re.M)
    text = demote_headings(text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def render_lender(slug, blocks, prov, canonical, snap_date):
    """Build one lender's markdown. Returns (lines, sha, by_topic)."""
    raw = json.dumps(blocks, sort_keys=True)
    sha = hashlib.sha256(raw.encode()).hexdigest()[:16]

    by_topic = {}
    for b in blocks:
        for t in b["triggers"]:
            by_topic.setdefault(t, []).append(b)

    name = lender_name(slug)
    lines = [
        f"# {name} (Quickli Policy Library snapshot)",
        "",
        f"> Snapshot: {au_date(snap_date)} · Lender policy last updated (Quickli): "
        f"{au_date(prov.get('policyUpdateDate'))} · Quickli last confirmed: "
        f"{au_date(prov.get('policyConfirmedDate'))} · sha256: {sha}",
        "> Quickli is the authority. Confirm live in Quickli before advice.",
        "",
    ]
    if prov.get("offPanel"):
        lines[2:2] = [
            "> **Off-panel:** not on your Quickli lender selection, so Quickli publishes no "
            "update or confirmation date for it. Treat as lower confidence and verify with the lender.",
            "",
        ]

    for t in canonical:
        if t not in by_topic:
            continue
        lines.append(f"## {topic_name(t)}")
        lines.append("")
        for b in by_topic[t]:
            extra = [x for x in b["triggers"] if x != t]
            if extra:
                lines.append(f"*Also covers: {', '.join(topic_name(x) for x in extra)}*")
                lines.append("")
            lines.append(clean_content(b["content"]))
            lv = b.get("lastVerifiedOn")
            if lv:
                lines.append("")
                lines.append(f"*Quickli last verified: {au_date(lv)}*")
            lines.append("")

    # Topics the lender has no entry for, stated explicitly so that absence is
    # visible rather than silent. This is what stops an assistant guessing a
    # policy position the KB never had.
    missing = [topic_name(t) for t in canonical if t not in by_topic]
    if missing:
        lines.append("## No Quickli entry for")
        lines.append("")
        lines.append(", ".join(missing) + ".")
        lines.append("")

    return lines, sha, by_topic


def write_topics(kb, canonical):
    with open(os.path.join(kb, "topics.md"), "w") as f:
        f.write("# Quickli policy topics (canonical list)\n\n")
        f.write("Grep the plain-English name as a `## ` heading across `lenders/*.md` "
                "for a cross-lender view. Trigger keys are Quickli's API enums.\n\n")
        f.write("| Trigger key | Topic heading |\n|---|---|\n")
        for t in canonical:
            f.write(f"| `{t}` | {topic_name(t)} |\n")


def write_index(kb, manifest, snap_date, failures):
    with open(os.path.join(kb, "INDEX.md"), "w") as f:
        f.write("# Lender Policy Knowledge Base (Quickli snapshot)\n\n")
        f.write(f"Snapshot of the Quickli Policy Library taken {au_date(snap_date)} "
                "from your own authenticated session. **Quickli is the authority and this is a "
                "cached lookup. Confirm live in Quickli before any advice or lodgement.**\n\n")
        f.write("**Keep this local.** Quickli policy content is Quickli's licensed product and you "
                "hold it under your own subscription. Don't share these files, don't paste them into "
                "web tools, don't bundle them into anything you pass to another broker. They build "
                "their own from their own login.\n\n")
        f.write("- Query: `/policy <question>` (grep `## Topic` headings from `topics.md` "
                "across `lenders/*.md`; load only matching lender files).\n")
        f.write("- Refresh: `/policy refresh [lender|all]` (incremental via `policyUpdateDate`).\n")
        f.write("- Staleness: any answer citing a snapshot older than 30 days must say so.\n")
        f.write("- `desk.md`: BDM and support contacts, policy source links, SLA document links per lender.\n")
        f.write("- Off-panel lenders (marked below) carry no Quickli update or confirmation date. "
                "Lower confidence; verify with the lender.\n\n")
        f.write("| Lender | File | Topics | Blocks | Policy updated | Quickli confirmed | Snapshot |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for slug in sorted(manifest, key=lambda s: manifest[s]["name"].lower()):
            m = manifest[slug]
            if m.get("offPanel"):
                f.write(f"| {m['name']} (off-panel) | `lenders/{slug}.md` | {m['topics']} | {m['blocks']} | "
                        f"not published | not published | {au_date(m['snapshotDate'])} |\n")
                continue
            f.write(f"| {m['name']} | `lenders/{slug}.md` | {m['topics']} | {m['blocks']} | "
                    f"{au_date(m['policyUpdateDate'])} | {au_date(m['policyConfirmedDate'])} | "
                    f"{au_date(m['snapshotDate'])} |\n")
        if failures:
            f.write(f"\n**FAILED / kept previous snapshot:** {', '.join(failures)}\n")


def check_regression(kb, snapshot_dir, manifest, threshold=0.10):
    """Compare block counts against the most recent previous manifest.

    A half-failed pull doesn't error, it just returns fewer blocks — and without
    this check your KB silently shrinks and you never notice. Any lender losing
    more than `threshold` of its blocks gets flagged loudly.
    """
    source_root = os.path.dirname(os.path.abspath(snapshot_dir))
    if not os.path.isdir(source_root):
        return []
    prior_dirs = sorted(
        d for d in os.listdir(source_root)
        if os.path.isdir(os.path.join(source_root, d))
        and os.path.basename(snapshot_dir) != d
        and os.path.exists(os.path.join(source_root, d, "manifest.json"))
    )
    if not prior_dirs:
        return []
    with open(os.path.join(source_root, prior_dirs[-1], "manifest.json")) as f:
        prior = json.load(f)

    warnings = []
    for slug, m in manifest.items():
        was = prior.get(slug, {}).get("blocks")
        if not was:
            continue
        if m["blocks"] < was * (1 - threshold):
            warnings.append(
                f"{lender_name(slug)}: {was} -> {m['blocks']} blocks "
                f"({100 * (was - m['blocks']) / was:.0f}% drop)"
            )
    return warnings


def main():
    ap = argparse.ArgumentParser(
        description="Render a Quickli policy snapshot into a lender-policy knowledge base.")
    ap.add_argument("snapshot", help="path to snapshot.json")
    ap.add_argument("--kb", default=DEFAULT_KB,
                    help=f"knowledge base directory (default: {DEFAULT_KB})")
    args = ap.parse_args()

    kb = os.path.expanduser(args.kb)
    with open(args.snapshot) as f:
        snap = json.load(f)

    snap_date = snap["snapshotDate"]
    canonical = snap["triggers"]
    prov_by_slug = {p["lender"]: p for p in snap["provenance"]}
    manifest, failures = {}, []

    os.makedirs(os.path.join(kb, "lenders"), exist_ok=True)

    for slug in sorted(snap["policyByLender"]):
        blocks = snap["policyByLender"][slug]
        prov = prov_by_slug.get(slug, {})
        # An empty block, or any block with empty content, means a partial pull.
        # Skip the lender entirely rather than overwrite a good file with a bad one.
        if not blocks or any(not (b.get("content") or "").strip() for b in blocks):
            failures.append(slug)
            continue

        lines, sha, by_topic = render_lender(slug, blocks, prov, canonical, snap_date)
        with open(os.path.join(kb, "lenders", f"{slug}.md"), "w") as f:
            f.write("\n".join(lines))

        manifest[slug] = {
            "name": lender_name(slug), "blocks": len(blocks), "topics": len(by_topic),
            "chars": len(json.dumps(blocks, sort_keys=True)), "sha256": sha,
            "policyUpdateDate": prov.get("policyUpdateDate"),
            "policyConfirmedDate": prov.get("policyConfirmedDate"),
            "offPanel": bool(prov.get("offPanel")),
            "snapshotDate": snap_date,
        }

    write_topics(kb, canonical)
    write_index(kb, manifest, snap_date, failures)

    snapshot_dir = os.path.dirname(os.path.abspath(args.snapshot))
    with open(os.path.join(snapshot_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)

    total_blocks = sum(m["blocks"] for m in manifest.values())
    print(f"Rendered {len(manifest)}/{len(snap['policyByLender'])} lenders, "
          f"{total_blocks} policy blocks, {len(canonical)} topics.")
    print(f"KB: {kb}")

    for w in check_regression(kb, snapshot_dir, manifest):
        print(f"  REGRESSION WARNING  {w}", file=sys.stderr)

    if failures:
        print("FAILURES (not rendered, previous files kept):", failures, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
