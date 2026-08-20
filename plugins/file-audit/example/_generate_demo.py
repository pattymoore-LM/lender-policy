#!/usr/bin/env python3
"""Regenerate the synthetic demo-client PDFs. Stdlib only.

Every document is fabricated SPECIMEN data for the /audit demo: fake people,
fake employer, fake bank, fictional ABN (valid check digit, not allocated).
The doctored payslip is deliberately wrong: Word producer, modified after the
pay date, an extra incremental save, a round net figure and a YTD that does
not reconcile with the clean payslip. /audit demo must catch it.

  python3 _generate_demo.py        writes into ./demo-client/
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent / "demo-client"


def esc(s):
    return s.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def make_pdf(lines, producer, creator, creation, moddate=None, extra_save=False):
    """One-page A4 text PDF with a controlled Info dictionary."""
    content = ["BT /F1 10 Tf 14 TL 50 800 Td"]
    for ln in lines:
        content.append(f"({esc(ln)}) Tj T*")
    content.append("ET")
    stream = "\n".join(content).encode("latin-1", "replace")

    objs = []
    objs.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objs.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    objs.append(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
                b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>")
    objs.append(b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream")
    objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    info = f"<< /Producer ({esc(producer)}) /Creator ({esc(creator)}) /CreationDate (D:{creation})"
    if moddate:
        info += f" /ModDate (D:{moddate})"
    info += " >>"
    objs.append(info.encode("latin-1"))

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objs, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_at = len(out)
    out += f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += (f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R /Info {len(objs)} 0 R >>\n"
            f"startxref\n{xref_at}\n%%EOF\n").encode()
    if extra_save:  # minimal incremental update: an appended empty-ish revision
        upd_obj_at = len(out)
        out += b"7 0 obj\n<< >>\nendobj\n"
        xref2_at = len(out)
        out += (f"xref\n0 1\n0000000000 65535 f \n7 1\n{upd_obj_at:010d} 00000 n \n"
                f"trailer\n<< /Size 8 /Root 1 0 R /Info {len(objs)} 0 R /Prev {xref_at} >>\n"
                f"startxref\n{xref2_at}\n%%EOF\n").encode()
    return bytes(out)


def fictional_abn():
    """A check-digit-valid ABN starting 99 999 (not an allocated range in practice)."""
    weights = [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
    for tail in range(10**5):
        cand = f"999998{tail:05d}"[:11].ljust(11, "0")
        nums = [int(d) for d in cand]
        nums[0] -= 1
        if sum(n * w for n, w in zip(nums, weights)) % 89 == 0:
            return f"{cand[:2]} {cand[2:5]} {cand[5:8]} {cand[8:]}"
    raise RuntimeError("no candidate found")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for sub in ("ID", "Income", "Statements", "Working"):
        (OUT / sub).mkdir(exist_ok=True)
    abn = fictional_abn()

    spec = "*** SPECIMEN - SYNTHETIC DEMO DOCUMENT - NOT A REAL RECORD ***"

    # Clean payslip: everything reconciles. 76.0h x $45.00 = $3,420.00 gross.
    (OUT / "Income" / "Payslip_Alex_08.08.2026.pdf").write_bytes(make_pdf([
        spec, "",
        "DEMOCORP PTY LTD          ABN " + abn,
        "PAYSLIP",
        "Employee: Alex Citizen        Pay date: 08/08/2026",
        "Period: 25/07/2026 - 07/08/2026 (fortnightly)",
        "",
        "Ordinary hours   76.00 @ $45.00        $3,420.00",
        "GROSS                                  $3,420.00",
        "PAYG withholding                         $612.00",
        "NET PAY                                $2,808.00",
        "",
        "Superannuation (12.0% OTE)               $410.40",
        "YTD Gross  $10,260.00   YTD Tax  $1,836.00   YTD Net  $8,424.00",
        "YTD start 01/07/2026",
    ], "MYOB PayGlobal", "MYOB PayGlobal", "20260808180000+10'00'"))

    # Doctored payslip: Word producer, modified AFTER the pay date, extra save,
    # round net, YTD HIGHER than the later clean payslip. Every tell is planted.
    (OUT / "Income" / "Payslip_Alex_25.07.2026.pdf").write_bytes(make_pdf([
        spec, "",
        "DEMOCORP PTY LTD",
        "PAYSLIP",
        "Employee: Alex Citizen        Pay date: 25/07/2026",
        "Period: 11/07/2026 - 24/07/2026 (fortnightly)",
        "",
        "Ordinary hours   76.00 @ $45.00        $3,900.00",
        "GROSS                                  $3,900.00",
        "PAYG withholding                         $900.00",
        "NET PAY                                $3,000.00",
        "",
        "YTD Gross  $14,500.00   YTD Tax  $2,700.00",
    ], "Microsoft Word for Microsoft 365", "Microsoft Word",
       "20260726091400+10'00'", moddate="20260812224100+10'00'", extra_save=True))

    # QLD licence mock: surname first, valid expiry, address on the card.
    (OUT / "ID" / "ID_Drivers_Licence_Alex.pdf").write_bytes(make_pdf([
        spec, "",
        "QUEENSLAND  DRIVER LICENCE",
        "CITIZEN ALEX JAY",
        "12 Sample Street, Demoville QLD 4000",
        "DOB 12/04/1990          Licence No. 123456789",
        "Effective 01/07/2024    Expiry 12/04/2029",
        "Class C                 Card No. A1B2C3D4",
    ], "Quartz PDFContext", "Preview", "20260701100000+10'00'"))

    (OUT / "ID" / "ID_Medicare_Family.pdf").write_bytes(make_pdf([
        spec, "",
        "medicare",
        "2999 99999 1",
        "1  ALEX J CITIZEN",
        "2  SAM CITIZEN",
        "VALID TO 03/2028",
    ], "Quartz PDFContext", "Preview", "20260701100100+10'00'"))

    # Bank statement: balances reconcile page-to-page, salary credits match the
    # clean payslip net, two gambling debits planted for the conduct scan.
    (OUT / "Statements" / "Statements_SunBank_Everyday_4471_Transactions.pdf").write_bytes(make_pdf([
        spec, "",
        "SUNBANK  Everyday Account 4471   Alex Citizen",
        "Statement period 01/07/2026 - 09/08/2026     Page 1 of 1",
        "Opening balance 01/07/2026                       $4,180.55",
        "",
        "11/07/2026  SALARY DEMOCORP PTY LTD     +$2,808.00   $6,988.55",
        "14/07/2026  WOOLWORTHS DEMOVILLE          -$212.40   $6,776.15",
        "18/07/2026  SPORTSBET                     -$200.00   $6,576.15",
        "25/07/2026  SALARY DEMOCORP PTY LTD     +$2,808.00   $9,384.15",
        "26/07/2026  RENT DEMOVILLE RE            -$650.00    $8,734.15",
        "01/08/2026  SPORTSBET                     -$150.00   $8,584.15",
        "08/08/2026  SALARY DEMOCORP PTY LTD     +$2,808.00  $11,392.15",
        "",
        "Total credits $8,424.00    Total debits $1,212.40",
        "Closing balance 09/08/2026                      $11,392.15",
    ], "PDFlib+PDI 9.0.4 (SunBank)", "SunBank Statement Engine", "20260810021000+10'00'"))

    # Google-native stub: exercises the unclassified path.
    (OUT / "Working" / "Serviceability workings.gdoc").write_text(
        '{"url": "https://docs.google.com/document/d/DEMO-ONLY-NOT-REAL/edit"}\n', encoding="utf-8")

    (OUT / "README.txt").write_text(
        "Synthetic demo client for /audit demo. Every document here is fabricated\n"
        "SPECIMEN data: fake people, fake employer, fake bank, fictional ABN.\n"
        "Payslip_Alex_25.07.2026.pdf is DELIBERATELY doctored (Word producer,\n"
        "modified after the pay date, extra incremental save, round net pay,\n"
        "YTD that does not reconcile). The demo audit must catch it.\n"
        "Document dates are fixed at build time, so freshness statuses will age.\n",
        encoding="utf-8")
    print(f"demo client written to {OUT}")


if __name__ == "__main__":
    main()
