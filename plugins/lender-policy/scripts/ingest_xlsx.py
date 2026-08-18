#!/usr/bin/env python3
"""Ingest a lender calculator workbook (.xlsx/.xlsm) into the primary-source layer.

Usage: python3 ingest_xlsx.py <workbook> <slug> "<display name>" "<source label>" [date]

Lender servicing calculators encode the real rules: shading percentages, buffers, floor
rates, thresholds. This reads BOTH the visible cell text AND the underlying formulas, so
a rule expressed only as a formula (e.g. an IF chain on months employed) is captured.

Stdlib only: zipfile + xml, no openpyxl in this environment.
"""
import zipfile, sys, os, re, json, datetime
import xml.etree.ElementTree as ET

KB = os.path.expanduser(
    os.environ.get("LENDER_POLICY_KB", "~/.claude/lender-policy")
)  # override with: export LENDER_POLICY_KB=/path/to/kb
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RNS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def col_of(ref):
    m = re.match(r"([A-Z]+)", ref or "")
    return m.group(1) if m else ""


def row_of(ref):
    m = re.search(r"(\d+)", ref or "")
    return int(m.group(1)) if m else 0


def load_shared(z):
    try:
        root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    out = []
    for si in root.findall(f"{NS}si"):
        out.append("".join(t.text or "" for t in si.iter(f"{NS}t")))
    return out


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
            text = ""
            if t == "s" and v is not None and v.text and v.text.isdigit():
                idx = int(v.text)
                text = shared[idx] if idx < len(shared) else ""
            elif is_el is not None:
                text = "".join(x.text or "" for x in is_el.iter(f"{NS}t"))
            elif v is not None:
                text = v.text or ""
            formula = ("=" + f.text) if (f is not None and f.text) else ""
            if text.strip() or formula:
                cells.append({"ref": ref, "text": text.strip(), "formula": formula})
        if cells:
            rows.append(cells)
    return rows


def render_sheet(name, rows):
    """Emit a sheet as readable lines: visible text laid out by row, formulas listed after."""
    out = [f"### {name}", ""]
    for cells in rows:
        line = " | ".join(c["text"] for c in cells if c["text"])
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
    out.append("")
    return "\n".join(out)


def main():
    path, slug, name, source = sys.argv[1:5]
    pulled = sys.argv[5] if len(sys.argv) > 5 else datetime.date.today().isoformat()
    z = zipfile.ZipFile(path)
    shared = load_shared(z)

    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rel_map = {r.get("Id"): r.get("Target") for r in rels}

    chapters = []
    for sh in wb.iter(f"{NS}sheet"):
        sname = sh.get("name")
        target = rel_map.get(sh.get(f"{RNS}id"), "")
        if not target:
            continue
        part = "xl/" + target.lstrip("/").replace("xl/", "", 1)
        try:
            rows = sheet_rows(z, part, shared)
        except KeyError:
            continue
        body = render_sheet(sname, rows)
        if len(body) > 120:                    # skip empty scratch sheets
            chapters.append({"id": str(len(chapters) + 1), "title": f"Sheet: {sname}",
                             "content": body, "pages": sname})

    outdir = os.path.join(KB, "primary", slug)
    os.makedirs(outdir, exist_ok=True)
    payload = {"lender": slug, "displayName": name, "source": source,
               "sourceFile": os.path.basename(path), "pages": len(chapters),
               "pulledAt": pulled, "chapters": chapters}
    jp = os.path.join(outdir, f"{slug}-credit-policy-{pulled}.json")
    json.dump(payload, open(jp, "w"))
    print(f"{name}: {len(chapters)} sheets, "
          f"{sum(len(c['content']) for c in chapters)//1000}k chars")
    for c in chapters:
        print(f"   {c['title']}: {len(c['content'])//1000}k")
    print("  json:", jp)


if __name__ == "__main__":
    main()
