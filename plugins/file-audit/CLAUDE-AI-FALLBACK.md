# file-audit without Claude Code — the claude.ai browser route

The plugin needs Claude Code (terminal or desktop app). If you only use claude.ai in the browser, this page gets you a reduced version of the audit in about 10 minutes. Be honest with yourself about the reductions at the bottom before relying on it.

## Set up once

1. In claude.ai, create a **Project** called "File Audit".
2. Add these five files from this folder as **Project knowledge**:
   - `data/lm-checklist.json`
   - `data/checklist_rules.json`
   - `skills/audit/fraud-checks.md`
   - `skills/audit/policy-constraints.md`
   - `skills/audit/id-crossmatch.md`
3. Paste this as the **Project instructions**:

> You audit one mortgage client's documents at a time for an Australian Loan Market broker. Two lenses: authenticity (per fraud-checks.md: doctored payslips, arithmetic that must reconcile, YTD progression, salary staging on bank statements, cross-document name/DOB/employer consistency, visual tells) and completeness against lm-checklist.json with the freshness windows in checklist_rules.json. Client-executed compliance documents (Privacy Consent, Game Plan, Quote) live in the CRM and are out of scope: never list them as missing. Every bank statement gets three questions minimum: are the salary credits real, is there gambling, is money going out to liabilities nobody disclosed (payslip <60 days, statements 60-90 by use, credit report <45 days, 183-day backstop; tighter window always wins; ID judged on expiry; NOA on latest financial year; an ATO income statement marked "not tax ready" is never final-year evidence). Read every page of every document before classifying it or calling anything missing. 2 valid IDs of passport/licence/Medicare suffice; at least one held ID must show the current address. Never transcribe a tax file number or Centrelink CRN - say "TFN present" only. Report: 1) checklist table with status per item (held-current / out of date / missing / check / n-a) and the requirement wording verbatim, 2) outstanding documents to request with the rule that makes them outstanding, 3) authenticity findings per document with evidence and a verification step, 4) policy considerations per policy-constraints.md, 5) a consolidated action list for the credit officer. Australian English, DD/MM/YYYY. You are a screening tool, not credit advice; every judgement belongs to the broker.

## Each audit

Start a new chat in the Project, attach the client's documents (drag the PDFs in — or connect the Google Drive connector and name the client folder), and say: **"Audit this client. Today's date is DD/MM/YYYY."** Always give the date - the browser model must not guess it.

## What this route does NOT do

- **No PDF metadata forensics** (producer software, modification dates, hidden edit markers) - that needs the plugin's local script. Authenticity rests on arithmetic, cross-document and visual checks only.
- **No deterministic date engine.** The model does the day counting itself; treat borderline in-date calls as "check".
- **No branded HTML report**, no config, no demo, no doctor - you get the audit as a chat reply (ask for it as a table).
- **Large files suffer.** The Drive connector and chat attachments may not surface every page of a 90-page statement bundle; the plugin route reads everything.

Treat browser results as a strong first pass. For the full audit, install Claude Code and the plugin - two lines, no Terminal knowledge needed (see `README.md`).
