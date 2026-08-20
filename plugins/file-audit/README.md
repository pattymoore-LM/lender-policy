# file-audit — the file check you'd do if you had an hour per client

A read-only audit of one client's document folder, run inside Claude Code. Two jobs at once:

1. **Fraud detector.** Is every document what it claims to be? PDF metadata forensics (what software made it, was it modified after the pay date, hidden edit markers), payslip arithmetic that must reconcile to the cent, YTD progression across payslips, ABN check digits, bank-statement balance continuity, salary credits tied back to payslips, name and DOB consistency across every document, and visual tells (fonts, alignment, spelling) called out page by page.
2. **Doc validator.** Does the file meet the Loan Market minimum supporting documents checklist (v4)? Every item checked as present, in date and showing the right data, with the exact freshness windows (payslips under 60 days, statements 60 to 90 by use, credit reports under 45, the 6-month backstop) computed by code, not judgement.

Every bank statement gets three questions as a minimum: are the salary credits real (staging tells: wrong payer, round amounts, wrong cadence, deposit-then-sweep), is there gambling, and is money going out to liabilities nobody disclosed.

**Scope note:** client-executed compliance documents (Privacy Consent, Game Plan, Quote) are signed and stored in your CRM, outside the client's document folder, so the audit deliberately does not check for them.

The output is one self-contained HTML report per audit, branded for your office: checklist status, the outstanding documents to request, a per-document authenticity card, policy considerations (short YTD, new job, alt-doc ABN age), and a consolidated action list for the credit officer. The goal: you never need to open a file to know the file is right.

## Install

Inside Claude Code:

```
/plugin marketplace add pattymoore-LM/lender-policy
/plugin install file-audit@broker-tools
```

Then, in order:

```
/audit doctor     confirms the install on your machine
/audit demo       runs a full audit on a bundled synthetic client (it must catch the planted doctored payslip)
/audit setup      points the tool at your clients folder and sets your office name
/audit <client>   your first real audit
```

## What it needs

- **Claude Code** (this plugin runs in it; your Claude subscription is the AI, there are no API keys and no other accounts).
- **Your client documents in a local folder** - one subfolder per client. Google Drive for Desktop is the usual way (it makes your Drive a normal folder); Dropbox, OneDrive or a plain folder work the same. If your Drive is browser-only, install Drive for Desktop from google.com/drive/download (5 minutes), or see `CLAUDE-AI-FALLBACK.md`.
- Python 3 makes the metadata forensics available. **Optional** - without it everything else still runs and the report builds via a built-in fallback.

## What it never does

- Never writes, renames, moves or deletes anything in a client folder. Reports and working files go to your output folder only (default `~/Documents/LM File Audits`).
- Never records a TFN or Centrelink CRN anywhere - findings, report or chat. The report builder refuses to build if one slips in.
- Never sends anything anywhere. Documents are read locally; the report is a local file.
- Never makes the credit decision. Forensic signals are investigation leads; the checklist verdicts are date arithmetic; the recommendation always belongs to the broker.

## Cost and time

A full audit reads every page of every document, and that's the point - page 3 of a "repayment letter" is where the missing statement lives, and the transaction pages are where the gambling and the undisclosed debts live. A 30-document file typically takes a few minutes. `/audit <client> quick` skips the transaction-level and forensic passes for a fast completeness check, and the report banner says so.

## Updating

New versions install automatically when you restart Claude Code. Nothing to do.

## Sharing

Share freely with other Loan Market businesses. No client data ships with this plugin and none ever enters the repo; the checklist and rules are LM's own standard. Keep the attribution.
