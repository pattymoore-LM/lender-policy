#!/usr/bin/env python3
"""file-audit — PDF forensics. Python 3.8+, standard library only.

Extracts tamper-relevant facts from a PDF's raw bytes without rendering it:
producer/creator software, creation vs modification dates, incremental-save
count, text-touchup markers, XMP edit history, encryption, and a page-count
estimate. Also validates an ABN check digit (--abn).

Facts, not verdicts. A scanner or email gateway re-saves PDFs legitimately,
so every signal here is an investigation lead the auditor weighs against the
document's other evidence. The script NEVER fails the audit: any unreadable
or odd file degrades to {"metadata_available": false} and exit code 0.

Usage:
  python3 pdf_forensics.py file1.pdf [file2.pdf ...]     JSON array to stdout
  python3 pdf_forensics.py --abn "12 004 044 937"        {"abn": ..., "valid": true}
  python3 pdf_forensics.py --selftest                    internal checks
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

MAX_READ = 64 * 1024 * 1024  # 64 MB cap; larger files are read head+tail

# Consumer editing / generation tools that have no business producing a payslip,
# bank statement, NOA or contract. Presence is a SIGNAL (weighted by doc type
# later, in fraud-checks.md), not a verdict — e.g. Word is fine for a broker
# note, damning for a bank statement.
EDITOR_TOOLS = [
    "microsoft word", "microsoft® word", "word for", "libreoffice", "openoffice",
    "pages", "google docs", "photoshop", "illustrator", "canva", "ilovepdf",
    "smallpdf", "sejda", "pdfescape", "pdffiller", "dochub", "camscanner",
    "nitro", "foxit phantompdf", "foxit pdf editor", "pdf-xchange editor",
    "pdfelement", "wondershare", "adobe acrobat pro", "acrobat pdfmaker",
    "sodapdf", "pdf24", "pdfsam", "deftpdf", "pdfcandy", "lightpdf",
]

# Tools that re-save PDFs in ordinary, legitimate workflows. Their presence
# downgrades the "modified after creation" signal to informational.
BENIGN_RESAVERS = [
    "quartz", "macos", "mac os x", "preview", "skia", "chrome", "chromium",
    "ghostscript", "gpl ghostscript", "itext", "pdfbox", "print to pdf",
    "microsoft: print to pdf", "scansnap", "epson scan", "hp scan",
    "canon", "brother", "xerox", "ricoh", "kyocera", "naps2", "genius scan",
]


def _decode_pdf_string(raw: bytes) -> str:
    """Decode a PDF literal-string payload (bytes between parens, escapes intact)."""
    out = bytearray()
    i = 0
    while i < len(raw):
        b = raw[i]
        if b == 0x5C and i + 1 < len(raw):  # backslash escape
            n = raw[i + 1]
            mapping = {0x6E: 0x0A, 0x72: 0x0D, 0x74: 0x09, 0x62: 0x08,
                       0x66: 0x0C, 0x28: 0x28, 0x29: 0x29, 0x5C: 0x5C}
            if n in mapping:
                out.append(mapping[n])
                i += 2
                continue
            if 0x30 <= n <= 0x37:  # octal, up to 3 digits
                j = i + 1
                oct_digits = b""
                while j < len(raw) and len(oct_digits) < 3 and 0x30 <= raw[j] <= 0x37:
                    oct_digits += bytes([raw[j]])
                    j += 1
                out.append(int(oct_digits, 8) & 0xFF)
                i = j
                continue
            i += 1  # lone backslash before newline etc: skip
            continue
        out.append(b)
        i += 1
    data = bytes(out)
    if data[:2] in (b"\xfe\xff", b"\xff\xfe"):
        try:
            return data.decode("utf-16")
        except UnicodeDecodeError:
            pass
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1", errors="replace")


def _find_info_value(buf: bytes, key: bytes):
    """Return the LAST occurrence of /Key (...) or /Key <...> in the buffer.
    Last wins because incremental updates append a newer Info dict at the end."""
    best = None
    for m in re.finditer(rb"/" + key + rb"\s*\(", buf):
        # walk to the matching close paren, honouring escapes and nesting
        i = m.end()
        depth = 1
        start = i
        while i < len(buf) and depth > 0:
            c = buf[i]
            if c == 0x5C:
                i += 2
                continue
            if c == 0x28:
                depth += 1
            elif c == 0x29:
                depth -= 1
            i += 1
        if depth == 0:
            best = _decode_pdf_string(buf[start:i - 1])
    for m in re.finditer(rb"/" + key + rb"\s*<([0-9A-Fa-f\s]+)>", buf):
        hexstr = re.sub(rb"\s", rb"", m.group(1))
        try:
            data = bytes.fromhex(hexstr.decode("ascii"))
        except ValueError:
            continue
        if data[:2] in (b"\xfe\xff", b"\xff\xfe"):
            best = data.decode("utf-16", errors="replace")
        else:
            best = data.decode("latin-1", errors="replace")
    return best


def _parse_pdf_date(s):
    """D:YYYYMMDDHHmmSSOHH'mm' -> ISO 8601 string, or None."""
    if not s:
        return None
    m = re.match(r"D?:?(\d{4})(\d{2})?(\d{2})?(\d{2})?(\d{2})?(\d{2})?\s*([Zz+\-])?(\d{2})?'?(\d{2})?", s)
    if not m:
        return None
    try:
        parts = [int(x) if x else d for x, d in zip(m.groups()[:6], (None, 1, 1, 0, 0, 0))]
        if parts[0] is None:
            return None
        dt = datetime(*parts)
        sign, oh, om = m.group(7), m.group(8), m.group(9)
        if sign in ("+", "-") and oh:
            offset = int(oh) * 60 + int(om or 0)
            if sign == "-":
                offset = -offset
            from datetime import timedelta
            dt = dt.replace(tzinfo=timezone(timedelta(minutes=offset)))
        elif sign in ("Z", "z"):
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    except ValueError:
        return None


def _xmp_date(buf: bytes, prop: str):
    pats = [
        rb"<xmp:" + prop.encode() + rb">([^<]+)</xmp:" + prop.encode() + rb">",
        rb"xmp:" + prop.encode() + rb"=\"([^\"]+)\"",
    ]
    best = None
    for p in pats:
        for m in re.finditer(p, buf):
            best = m.group(1).decode("utf-8", errors="replace").strip()
    return best


def abn_valid(abn: str):
    """ABN check-digit validation (ATO modulus-89 algorithm)."""
    digits = re.sub(r"\D", "", abn or "")
    if len(digits) != 11:
        return False
    weights = [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
    nums = [int(d) for d in digits]
    nums[0] -= 1
    return sum(n * w for n, w in zip(nums, weights)) % 89 == 0


def inspect(path: str):
    p = Path(path)
    result = {
        "file": str(p),
        "metadata_available": False,
        "is_pdf": False,
        "size_bytes": None,
        "producer": None,
        "creator": None,
        "creation_date": None,
        "mod_date": None,
        "xmp_create_date": None,
        "xmp_modify_date": None,
        "xmp_history_saves": 0,
        "eof_count": 0,
        "encrypted": False,
        "touchup_textedit": False,
        "annotation_count": 0,
        "page_count_estimate": None,
        "producer_class": None,     # editor | benign_resaver | other | unknown
        "tamper_signals": [],
        "notes": [],
    }
    try:
        size = p.stat().st_size
        result["size_bytes"] = size
        with open(p, "rb") as f:
            if size <= MAX_READ:
                buf = f.read()
            else:
                head = f.read(MAX_READ // 2)
                f.seek(max(0, size - MAX_READ // 2))
                buf = head + f.read()
                result["notes"].append("large file: head+tail scanned only")
    except OSError as e:
        result["notes"].append(f"unreadable: {e.__class__.__name__}")
        return result

    if not buf.lstrip()[:5].startswith(b"%PDF-"):
        result["notes"].append("not a PDF (magic bytes)")
        return result
    result["is_pdf"] = True
    result["metadata_available"] = True

    result["producer"] = _find_info_value(buf, b"Producer")
    result["creator"] = _find_info_value(buf, b"Creator")
    result["creation_date"] = _parse_pdf_date(_find_info_value(buf, b"CreationDate"))
    result["mod_date"] = _parse_pdf_date(_find_info_value(buf, b"ModDate"))
    result["xmp_create_date"] = _xmp_date(buf, "CreateDate")
    result["xmp_modify_date"] = _xmp_date(buf, "ModifyDate")
    result["xmp_history_saves"] = len(re.findall(rb"stEvt:action=\"saved\"|<stEvt:action>saved<", buf))
    result["eof_count"] = buf.count(b"%%EOF")
    result["encrypted"] = b"/Encrypt" in buf
    result["touchup_textedit"] = b"TouchUp_TextEdit" in buf
    result["annotation_count"] = len(re.findall(rb"/Subtype\s*/(?:FreeText|Square|Ink|Stamp|Widget)", buf))
    pages = len(re.findall(rb"/Type\s*/Page[^s]", buf))
    result["page_count_estimate"] = pages if pages else None

    tool_text = " ".join(x for x in (result["producer"], result["creator"]) if x).lower()
    if tool_text:
        if any(t in tool_text for t in EDITOR_TOOLS):
            result["producer_class"] = "editor"
        elif any(t in tool_text for t in BENIGN_RESAVERS):
            result["producer_class"] = "benign_resaver"
        else:
            result["producer_class"] = "other"
    else:
        result["producer_class"] = "unknown"

    sig = result["tamper_signals"]
    if result["producer_class"] == "editor":
        sig.append({"signal": "consumer_editor_producer",
                    "detail": f"Produced/created by an editing tool: {result['producer'] or result['creator']}"})
    if result["touchup_textedit"]:
        sig.append({"signal": "touchup_textedit",
                    "detail": "Acrobat TouchUp text-edit marker present: text was edited in place after creation"})
    if result["eof_count"] > 1:
        sig.append({"signal": "incremental_saves",
                    "detail": f"{result['eof_count']} %%EOF markers: the file was re-saved {result['eof_count'] - 1} time(s) after creation"})
    cd, md = result["creation_date"], result["mod_date"]
    if cd and md and md[:19] != cd[:19]:
        level = "modified_after_creation"
        if result["producer_class"] == "benign_resaver":
            level = "modified_after_creation_benign_tool"
        sig.append({"signal": level,
                    "detail": f"Created {cd} but modified {md}"})
    if result["xmp_history_saves"] > 1:
        sig.append({"signal": "xmp_edit_history",
                    "detail": f"XMP history records {result['xmp_history_saves']} save events"})
    if result["annotation_count"] > 0:
        sig.append({"signal": "annotation_overlays",
                    "detail": f"{result['annotation_count']} overlay annotation(s) (FreeText/Ink/Stamp/etc) sitting on top of the page content"})
    if result["encrypted"]:
        result["notes"].append("encrypted: some metadata may be unreadable")

    return result


def _selftest():
    assert abn_valid("12 004 044 937"), "known-good ABN failed"       # Coles Group Ltd, public record
    assert abn_valid("51 824 753 556"), "known-good ABN failed"       # ATO's own ABN, public record
    assert not abn_valid("12 004 044 938"), "bad check digit passed"
    assert not abn_valid("1234"), "short ABN passed"
    assert _parse_pdf_date("D:20260815093000+10'00'") == "2026-08-15T09:30:00+10:00"
    assert _parse_pdf_date("D:20260815") == "2026-08-15T00:00:00"
    assert _parse_pdf_date(None) is None
    assert _decode_pdf_string(b"MYOB PayGlobal \\(AU\\)") == "MYOB PayGlobal (AU)"
    minimal = (b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\n"
               b"2 0 obj<</Producer(Microsoft Word)/CreationDate(D:20260101120000)"
               b"/ModDate(D:20260301120000)>>endobj\ntrailer<<>>\n%%EOF\n"
               b"3 0 obj<<>>endobj\n%%EOF\n")
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as t:
        t.write(minimal)
        tmp = t.name
    try:
        r = inspect(tmp)
        assert r["producer"] == "Microsoft Word", r
        assert r["eof_count"] == 2, r
        assert r["producer_class"] == "editor", r
        signals = {s["signal"] for s in r["tamper_signals"]}
        assert "consumer_editor_producer" in signals and "incremental_saves" in signals \
            and "modified_after_creation" in signals, signals
    finally:
        os.unlink(tmp)
    print("pdf_forensics selftest: OK")


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__.strip())
    if argv[1] == "--selftest":
        _selftest()
        return
    if argv[1] == "--abn":
        if len(argv) < 3:
            sys.exit("usage: pdf_forensics.py --abn <abn>")
        print(json.dumps({"abn": argv[2], "valid": abn_valid(argv[2])}))
        return
    out = [inspect(a) for a in argv[1:]]
    print(json.dumps(out if len(out) > 1 else out[0], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv)
