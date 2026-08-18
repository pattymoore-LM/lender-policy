#!/usr/bin/env python3
"""Ingest a lender or insurer policy PDF into the primary-source layer.

Usage: python3 ingest_pdf.py <pdf> <slug> "<display name>" "<source label>" [pulled_date]

Uses pdftotext -layout (poppler) because credit-policy PDFs are table heavy and layout
mode keeps row labels attached to their content. Chapters come from the PDF's own
bookmarks when it has them, otherwise from a parsed table of contents, otherwise the
whole document lands as one chapter. Everything runs locally; nothing leaves the Mac.

Writes primary/<slug>/<slug>-credit-policy.json (raw, for re-render) and hands off to
render_primary.py for the markdown + INDEX rebuild.
"""
import subprocess, sys, os, re, json, datetime

KB = os.path.expanduser(
    os.environ.get("LENDER_POLICY_KB", "~/.claude/lender-policy")
)  # override with: export LENDER_POLICY_KB=/path/to/kb


def page_texts(pdf, n):
    out = []
    for i in range(1, n + 1):
        r = subprocess.run(["pdftotext", "-layout", "-f", str(i), "-l", str(i), pdf, "-"],
                           capture_output=True, text=True)
        out.append(r.stdout)
    return out


def strip_furniture(doc, pages):
    """Remove running headers and footers, identified by POSITION not just repetition.

    Repetition alone is not enough: a product guide repeats "What is it?" on every
    product page, and that is content. A running header is text that repeats AND sits in
    the top or bottom margin band, so use PyMuPDF's geometry to tell them apart.
    """
    from collections import Counter
    margin_counts = Counter()
    for page in doc:
        h = page.rect.height
        for x0, y0, x1, y1, text, *_ in page.get_text("blocks"):
            if y1 <= h * 0.08 or y0 >= h * 0.92:
                for line in text.splitlines():
                    s = line.strip()
                    if s and len(s) < 120:
                        margin_counts[s] += 1
    threshold = max(3, int(doc.page_count * 0.5))
    boiler = {s for s, c in margin_counts.items() if c >= threshold}
    cleaned = []
    for p in pages:
        keep = [l for l in p.splitlines()
                if l.strip() not in boiler
                and not re.match(r"^\s*Page \d+ of \d+", l)]
        cleaned.append("\n".join(keep))
    return cleaned, sorted(boiler)[:6]


def chapters_from_toc(doc, pages):
    toc = doc.get_toc()
    if not toc:
        return None
    tops = [(t[1].strip(), t[2]) for t in toc if t[0] == 1 and t[2] >= 1]
    if len(tops) < 2:
        tops = [(t[1].strip(), t[2]) for t in toc if t[2] >= 1]
    if len(tops) < 2:
        return None
    chapters = []
    for i, (title, start) in enumerate(tops):
        end = tops[i + 1][1] - 1 if i + 1 < len(tops) else len(pages)
        body = "\n".join(pages[start - 1:end]).strip()
        body = re.sub(r"\n{3,}", "\n\n", body)
        if body:
            chapters.append({"id": str(i + 1), "title": title, "content": body,
                             "pages": f"{start}-{end}"})
    return chapters or None


def chapters_from_printed_contents(pages):
    """Parse a printed contents page (dotted leaders ending in a page number).

    Many lender PDFs ship no bookmarks but do print a contents page. Entries look like
    "3B. Income - PAYG ........ 20". Parent headings that share a start page with their
    first child are dropped so chapters do not duplicate.
    """
    entries = []
    for pno, p in enumerate(pages[:6], start=1):   # contents lives at the front
        for line in p.splitlines():
            m = re.match(r"^\s*(.{3,90}?)\s*\.{5,}\s*(\d{1,3})\s*$", line)
            if m:
                title = re.sub(r"\s+", " ", m.group(1)).strip(" .")
                if title and not re.match(r"^\d{1,3}$", title):
                    entries.append((title, int(m.group(2))))
    if len(entries) < 4:
        return None

    # Drop duplicates, keep document order, require non-decreasing page numbers.
    cleaned, seen = [], set()
    for title, page in entries:
        key = title.lower()
        if key in seen or page > len(pages):
            continue
        if cleaned and page < cleaned[-1][1]:
            continue
        seen.add(key)
        cleaned.append((title, page))
    if len(cleaned) < 4:
        return None

    # Verify the printed numbering matches PDF page indices; correct a constant offset.
    def hits(offset):
        n = 0
        for title, page in cleaned[:12]:
            idx = page - 1 + offset
            if 0 <= idx < len(pages):
                head = re.sub(r"[^a-z0-9]", "", title.lower())[:18]
                body = re.sub(r"[^a-z0-9]", "", pages[idx].lower())
                if head and head in body:
                    n += 1
        return n
    offset = max(range(-2, 3), key=hits)
    if hits(offset) < max(2, len(cleaned[:12]) // 3):
        return None

    # Group entries that start on the same page: they share one chapter, and every title
    # is kept in the heading so a grep for any of them still lands.
    groups = []
    for title, page in cleaned:
        if groups and groups[-1][1] == page:
            groups[-1][0].append(title)
        else:
            groups.append([[title], page])

    chapters = []
    for i, (titles, page) in enumerate(groups):
        start = page + offset
        end = (groups[i + 1][1] + offset - 1) if i + 1 < len(groups) else len(pages)
        if end < start:
            end = start
        body = re.sub(r"\n{3,}", "\n\n", "\n".join(pages[start - 1:end]).strip())
        if body:
            chapters.append({"id": str(len(chapters) + 1), "title": " / ".join(titles),
                             "content": body, "pages": f"{start}-{end}"})
    return chapters or None


def chapters_from_headings(pages):
    """Fallback: split on numbered top-level headings like '5 Employment and income'."""
    joined = [(i + 1, p) for i, p in enumerate(pages)]
    marks = []
    for pno, p in joined:
        for line in p.splitlines():
            m = re.match(r"^\s{0,8}(\d{1,2})\.?\s+([A-Z][A-Za-z][^\.]{3,70})\s*$", line)
            if m and not re.search(r"\.{4,}", line):
                marks.append((int(m.group(1)), m.group(2).strip(), pno))
    seen, tops = set(), []
    for num, title, pno in marks:
        if num in seen or num != len(seen) + 1:
            continue
        seen.add(num)
        tops.append((f"{num}. {title}", pno))
    if len(tops) < 3:
        return [{"id": "1", "title": "Full document", "pages": f"1-{len(pages)}",
                 "content": re.sub(r"\n{3,}", "\n\n", "\n".join(pages).strip())}]
    chapters = []
    for i, (title, start) in enumerate(tops):
        end = tops[i + 1][1] - 1 if i + 1 < len(tops) else len(pages)
        body = re.sub(r"\n{3,}", "\n\n", "\n".join(pages[start - 1:end]).strip())
        if body:
            chapters.append({"id": str(i + 1), "title": title, "content": body,
                             "pages": f"{start}-{end}"})
    return chapters


def main():
    pdf, slug, name, source = sys.argv[1:5]
    pulled = sys.argv[5] if len(sys.argv) > 5 else datetime.date.today().isoformat()
    import fitz
    doc = fitz.open(pdf)
    pages = page_texts(pdf, doc.page_count)
    pages, boiler = strip_furniture(doc, pages)
    chapters = (chapters_from_toc(doc, pages) or chapters_from_printed_contents(pages)
                or chapters_from_headings(pages))

    outdir = os.path.join(KB, "primary", slug)
    os.makedirs(outdir, exist_ok=True)
    payload = {"lender": slug, "displayName": name, "source": source,
               "sourceFile": os.path.basename(pdf), "pages": doc.page_count,
               "pulledAt": pulled, "chapters": chapters}
    jpath = os.path.join(outdir, f"{slug}-credit-policy-{pulled}.json")
    json.dump(payload, open(jpath, "w"))
    total = sum(len(c["content"]) for c in chapters)
    print(f"{name}: {doc.page_count} pages -> {len(chapters)} chapters, {total//1000}k chars")
    print("  stripped furniture:", "; ".join(boiler[:3]) or "none")
    print("  chapters:", ", ".join(c["title"][:40] for c in chapters[:8]),
          "..." if len(chapters) > 8 else "")
    print("  json:", jpath)


if __name__ == "__main__":
    main()
