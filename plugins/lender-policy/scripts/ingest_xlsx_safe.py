#!/usr/bin/env python3
"""Ingest a CLIENT-POPULATED lender calculator into the primary layer without the client data.

Usage:
  python3 ingest_xlsx_safe.py <workbook> <slug> "<display name>" "<source label>" \
      --template <blank workbook> [--ref-sheets "A|B|C"] [--date YYYY-MM-DD]

Why this exists: some calculators only reach us already filled in for a live deal. The
policy lives in the formulas and the reference tables; the client's figures live in the
input cells. The KB is a no-PII zone (rules/compliance.md), so this keeps the first and
drops the second.

What survives:
  - every formula (formulas are template logic, never client data)
  - every cell on a --ref-sheets sheet (rate cards, HEM, tax scales, postcodes, notes)
  - constant cells whose text also appears in the blank template's string table, i.e.
    field captions and dropdown values that ship with the workbook

What is dropped, and counted per sheet:
  - any other constant: every number the broker typed, every free-text entry

Stdlib only: zipfile + xml, no openpyxl in this environment.
"""
import zipfile, sys, os, re, json, datetime
import xml.etree.ElementTree as ET

KB = os.path.expanduser(
    os.environ.get("LENDER_POLICY_KB", "~/.claude/lender-policy")
)  # override with: export LENDER_POLICY_KB=/path/to/kb
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RNS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def load_shared(z):
    try:
        root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    return ["".join(t.text or "" for t in si.iter(f"{NS}t")) for si in root.findall(f"{NS}si")]


def sheet_rows(z, path, shared):
    root = ET.fromstring(z.read(path))
    rows = []
    for row in root.iter(f"{NS}row"):
        cells = []
        for c in row.findall(f"{NS}c"):
            ref = c.get("r", "")
            t = c.get("t")
            f = c.find(f"{NS}f")
            v = c.find(f"{NS}v")
            is_el = c.find(f"{NS}is")
            text, shared_str = "", False
            if t == "s" and v is not None and v.text and v.text.isdigit():
                idx = int(v.text)
                text = shared[idx] if idx < len(shared) else ""
                shared_str = True
            elif is_el is not None:
                text = "".join(x.text or "" for x in is_el.iter(f"{NS}t"))
            elif v is not None:
                text = v.text or ""
            formula = ("=" + f.text) if (f is not None and f.text) else ""
            if text.strip() or formula:
                cells.append({"ref": ref, "text": text.strip(), "formula": formula,
                              "shared": shared_str})
        if cells:
            rows.append(cells)
    return rows


def render_sheet(name, rows, template_strings, is_ref, audit=None):
    """Same shape as ingest_xlsx.render_sheet, with client constants withheld."""
    out = [f"### {name}", ""]
    dropped = 0
    for cells in rows:
        keep = []
        for c in cells:
            if not c["text"]:
                continue
            if is_ref:
                keep.append(c["text"])
            elif c["shared"] and c["text"] in template_strings:
                keep.append(c["text"])
            elif c["formula"]:
                # The formula is policy and is emitted below. Its CACHED VALUE is this
                # deal's answer, computed from the client's figures, so it never renders.
                dropped += 1
            else:
                dropped += 1
                if audit is not None:
                    audit.append((name, c["ref"], c["text"]))
        line = " | ".join(keep)
        if line.strip(" |"):
            out.append(f"- {line}")

    formulas = [(c["ref"], c["formula"]) for cells in rows for c in cells if c["formula"]]
    uniq, seen = [], set()
    for ref, f in formulas:
        key = re.sub(r"\d+", "#", f)          # collapse row-repeated formulas
        if key in seen:
            continue
        seen.add(key)
        uniq.append((ref, f))
    if uniq:
        out += ["", f"**Formulas ({len(formulas)} cells, {len(uniq)} distinct patterns):**", ""]
        for ref, f in uniq[:120]:
            out.append(f"- `{ref}`: `{f}`")
        if len(uniq) > 120:
            out.append(f"- ...and {len(uniq)-120} further distinct formulas")
    if dropped:
        out += ["", f"> {dropped} constant cell(s) withheld from this sheet: entered for a live "
                    "deal, so they are client data rather than policy."]
    out.append("")
    return "\n".join(out), dropped


def main():
    path, slug, name, source = sys.argv[1:5]
    rest = sys.argv[5:]
    template = ref_sheets = None
    pulled = datetime.date.today().isoformat()
    audit = None
    drop_sheets, keep_labels = set(), False
    i = 0
    while i < len(rest):
        if rest[i] == "--template":
            template = rest[i + 1]; i += 2
        elif rest[i] == "--ref-sheets":
            ref_sheets = {s.strip() for s in rest[i + 1].split("|")}; i += 2
        elif rest[i] == "--date":
            pulled = rest[i + 1]; i += 2
        elif rest[i] == "--audit":
            audit = []; i += 1          # print every withheld value, nothing written to disk
        elif rest[i] == "--drop-sheets":
            drop_sheets |= {s.strip() for s in rest[i + 1].split("|")}; i += 2
        elif rest[i] == "--keep-labels":
            keep_labels = True; i += 1
        else:
            i += 1
    ref_sheets = ref_sheets or set()

    z = zipfile.ZipFile(path)
    template_strings = set()
    if template:
        template_strings = set(load_shared(zipfile.ZipFile(template)))
    if keep_labels:
        # Only for a workbook checked cell by cell and shown to hold no typed text: every
        # shared string is a caption the workbook ships with, so client data is numeric.
        template_strings |= set(load_shared(z))
    if not template_strings and not ref_sheets:
        sys.exit("refusing to run: no --template and no --ref-sheets, nothing would be scrubbed")

    shared = load_shared(z)
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rel_map = {r.get("Id"): r.get("Target") for r in rels}

    chapters, total_dropped = [], 0
    for sh in wb.iter(f"{NS}sheet"):
        sname = sh.get("name")
        target = rel_map.get(sh.get(f"{RNS}id"), "")
        if not target or sname in drop_sheets:
            continue
        part = "xl/" + target.lstrip("/").replace("xl/", "", 1)
        try:
            rows = sheet_rows(z, part, shared)
        except KeyError:
            continue
        body, dropped = render_sheet(sname, rows, template_strings, sname in ref_sheets, audit)
        total_dropped += dropped
        if len(body) > 120:                    # skip empty scratch sheets
            chapters.append({"id": str(len(chapters) + 1), "title": f"Sheet: {sname}",
                             "content": body, "pages": sname})

    outdir = os.path.join(KB, "primary", slug)
    os.makedirs(outdir, exist_ok=True)
    payload = {"lender": slug, "displayName": name, "source": source,
               "sourceFile": os.path.basename(path), "pages": len(chapters),
               "pulledAt": pulled, "scrubbed": True, "cellsWithheld": total_dropped,
               "referenceSheets": sorted(ref_sheets), "chapters": chapters}
    jp = os.path.join(outdir, f"{slug}-credit-policy-{pulled}.json")
    json.dump(payload, open(jp, "w"))
    print(f"{name}: {len(chapters)} sheets, "
          f"{sum(len(c['content']) for c in chapters)//1000}k chars, "
          f"{total_dropped} client cells withheld")
    for c in chapters:
        print(f"   {c['title']}: {len(c['content'])//1000}k")
    print("  json:", jp)
    if audit is not None:
        print(f"\n--- withheld ({len(audit)}), review before trusting the scrub ---")
        for sname, ref, text in audit:
            print(f"  [{sname}] {ref}: {text[:160]}")


if __name__ == "__main__":
    main()
