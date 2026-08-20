#!/usr/bin/env python3
"""file-audit — build the HTML audit report from a findings JSON. Stdlib only.

  python3 build_report.py <findings.json> [out.html]
  python3 build_report.py --selftest

Owns the deterministic date arithmetic (a port of the linda-agent build_review.py
logic, kept in lockstep with the identical JavaScript inside report-template.html
via --selftest and example/expected-statuses.json). The model asserts facts
(types, dates, evidence); this code computes every current/stale/missing verdict.

The report is a single self-contained HTML file: the template's __RULES_JSON__
and __FINDINGS_JSON__ slots are filled at build time, so the shipped
data/checklist_rules.json is always the rules copy the renderer uses.

Refuses to build if anything TFN-shaped appears in the findings text.
"""
import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN_ROOT = HERE.parent
TEMPLATE = HERE / "report-template.html"
RULES = PLUGIN_ROOT / "data" / "checklist_rules.json"

STATUSES = ("current", "stale", "missing", "check", "na")
TFN_SHAPE = re.compile(r"\b\d{3}[ \-]\d{3}[ \-]\d{3}\b")


def parse_d(s):
    if not s:
        return None
    s = str(s).strip()[:10]
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def effective_max_age(doc, category_id, rules):
    ov = rules.get("category_overrides", {}).get(category_id, {})
    if isinstance(ov.get(doc.get("type")), (int, float)):
        return ov[doc["type"]]
    if isinstance(doc.get("max_age_days"), (int, float)):
        return doc["max_age_days"]
    dc = rules.get("doc_currency", {}).get(doc.get("type"))
    return dc.get("max_age_days") if dc else None


def doc_in_date(doc, category_id, run_d, rules, backstop):
    """True / False / None. Mirror of the JS docInDate() in report-template.html."""
    if doc.get("in_date_override") is not None:
        return bool(doc["in_date_override"])
    label = doc.get("date_label")
    dd = parse_d(doc.get("key_date"))
    if label == "expiry":
        return (dd >= run_d) if dd else None
    if label == "financial_year":
        v = doc.get("is_latest_fy")
        return None if v is None else bool(v)
    if label in (None, "", "none", "executed"):
        if dd is None:
            return True
        return (run_d - dd).days <= backstop
    mad = effective_max_age(doc, category_id, rules)
    if dd is None or mad is None:
        return None
    age = (run_d - dd).days
    return age < 0 or age <= min(mad, backstop)


def item_status(item, docs_by_id, run_d, rules, backstop):
    """Mirror of the JS itemStatus(). Optional items with nothing held are N/A."""
    if item.get("applicable", True) is False:
        return "na"
    docs = [docs_by_id[i] for i in item.get("doc_ids", []) if i in docs_by_id]
    if not docs:
        return "na" if item.get("optional") else "missing"
    flags = [doc_in_date(d, item.get("category_id"), run_d, rules, backstop) for d in docs]
    need = int(item.get("need", 1))
    if sum(1 for f in flags if f is True) >= need:
        return "current"
    if any(f is None for f in flags) and not any(f is False for f in flags):
        return "check"
    return "stale"


def walk_strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from walk_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk_strings(v)


def validate(findings):
    errs = []
    for key in ("client", "run_date", "documents", "checklist_items"):
        if key not in findings:
            errs.append(f"missing required key: {key}")
    if parse_d(findings.get("run_date")) is None:
        errs.append("run_date must be YYYY-MM-DD")
    ids = set()
    for d in findings.get("documents", []):
        if not d.get("id"):
            errs.append(f"document without id: {d.get('file')}")
        elif d["id"] in ids:
            errs.append(f"duplicate document id: {d['id']}")
        ids.add(d.get("id"))
        if d.get("key_date") and d.get("date_label") not in ("financial_year",) \
                and parse_d(d["key_date"]) is None:
            errs.append(f"{d.get('id')}: key_date not YYYY-MM-DD: {d['key_date']}")
    for it in findings.get("checklist_items", []):
        for i in it.get("doc_ids", []):
            if i not in ids:
                errs.append(f"checklist item references unknown doc id: {i}")
    for f in findings.get("red_flags", []):
        if f.get("severity") not in ("high", "medium", "low"):
            errs.append(f"red flag {f.get('id')}: bad severity {f.get('severity')}")
    # TFN guard: a separator-grouped 9-digit run anywhere in the findings text is
    # TFN-shaped. Hard refusal — the audit must re-write the evidence without it.
    for s in walk_strings(findings):
        if TFN_SHAPE.search(s):
            errs.append(f"TFN-shaped number in findings text (never record TFN/CRN values): '{s[:60]}...'")
            break
    return errs


def compute_tallies(findings, rules):
    backstop = int(findings.get("freshness_backstop_days")
                   or rules.get("freshness_backstop_days") or 183)
    run_d = parse_d(findings.get("run_date")) or date.today()
    docs_by_id = {d["id"]: d for d in findings.get("documents", []) if d.get("id")}
    tally = {s: 0 for s in STATUSES}
    per_item = []
    for it in findings.get("checklist_items", []):
        st = item_status(it, docs_by_id, run_d, rules, backstop)
        tally[st] += 1
        per_item.append({"category_id": it.get("category_id"),
                         "requirement": (it.get("requirement") or "")[:60], "status": st})
    return tally, per_item


def inject(findings, rules_text):
    tpl = TEMPLATE.read_text(encoding="utf-8")
    for slot in ("__RULES_JSON__", "__FINDINGS_JSON__"):
        if slot not in tpl:
            sys.exit(f"template is broken: {slot} slot not found in {TEMPLATE}")
    payload = json.dumps(findings, ensure_ascii=False).replace("</", "<\\/")
    return tpl.replace("__RULES_JSON__", rules_text.replace("</", "<\\/")) \
              .replace("__FINDINGS_JSON__", payload)


def selftest():
    rules = json.loads(RULES.read_text(encoding="utf-8"))
    ex_dir = PLUGIN_ROOT / "example"
    findings = json.loads((ex_dir / "example-findings.json").read_text(encoding="utf-8"))
    expected = json.loads((ex_dir / "expected-statuses.json").read_text(encoding="utf-8"))
    errs = validate(findings)
    if errs:
        sys.exit("selftest FAILED — example findings invalid:\n  " + "\n  ".join(errs))
    _, per_item = compute_tallies(findings, rules)
    got = {f"{p['category_id']}::{p['requirement']}": p["status"] for p in per_item}
    bad = []
    for key, want in expected.items():
        if got.get(key) != want:
            bad.append(f"{key}: expected {want}, got {got.get(key)}")
    for key in got:
        if key not in expected:
            bad.append(f"unexpected item not covered by vectors: {key}")
    if bad:
        sys.exit("selftest FAILED — status vectors:\n  " + "\n  ".join(bad))
    html = inject(findings, RULES.read_text(encoding="utf-8"))
    if "__FINDINGS_JSON__" in html or "__RULES_JSON__" in html:
        sys.exit("selftest FAILED — placeholder survived injection")
    out = ex_dir / "example-report.html"
    out.write_text(html, encoding="utf-8")
    print(f"build_report selftest: OK ({len(expected)} vectors) — sample report at {out}")


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--selftest":
        selftest()
        return
    if len(sys.argv) < 2:
        sys.exit(__doc__.strip())
    fpath = Path(sys.argv[1])
    findings = json.loads(fpath.read_text(encoding="utf-8"))
    rules_text = RULES.read_text(encoding="utf-8")
    rules = json.loads(rules_text)
    errs = validate(findings)
    if errs:
        sys.exit("REFUSED — findings invalid:\n  " + "\n  ".join(errs))
    if len(sys.argv) >= 3:
        out = Path(sys.argv[2])
    else:
        client = str(findings.get("client", "client")).replace("/", "-")
        out = fpath.parent / f"{client} - File Audit {findings.get('run_date')}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(inject(findings, rules_text), encoding="utf-8")
    tally, _ = compute_tallies(findings, rules)
    applicable = sum(v for k, v in tally.items() if k != "na")
    pct = round(100 * tally["current"] / applicable) if applicable else 0
    print(f"wrote {out}")
    print(f"items: current={tally['current']} stale={tally['stale']} missing={tally['missing']} "
          f"check={tally['check']} na={tally['na']} | completeness {pct}% | "
          f"docs={len(findings.get('documents', []))} flags={len(findings.get('red_flags', []))} "
          f"policy={len(findings.get('policy_flags', []))}")


if __name__ == "__main__":
    main()
