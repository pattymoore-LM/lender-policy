---
name: audit
description: Use when the broker types /audit <client>, or asks to audit, review or compliance-check a client's document file against the Loan Market minimum supporting documents checklist, or asks whether a client's docs are complete, in date or genuine. Read-only audit of the client's local (Drive-synced) folder. Two lenses at once - fraud detection (tampering, doctored payslips, metadata, arithmetic) and checklist validation (present, in date, right data). Produces a branded HTML report. Also handles /audit setup, /audit demo, /audit doctor and /audit <client> quick.
---

# /audit — mortgage file audit (fraud detector + doc validator)

Read-only compliance audit of one client's document folder. Output: a self-contained branded HTML report with a checklist summary, the outstanding documents to request, per-document authenticity verification, policy considerations and notes for the credit officer. The goal: the broker never has to open a file to know the file is right.

## Rules that never bend

1. **Read-only on the client folder.** Never rename, move, copy, delete, or write anything inside it. No Bash redirects into it. All output goes to the configured output folder only.
2. **Never transcribe a TFN or Centrelink CRN.** Not in findings, evidence, notes, or chat. Record `tfn_present: true` and the words "TFN present on document" only. The report builder refuses to build if a TFN-shaped number appears anywhere in the findings.
3. **Read every page of every document** before classifying it or declaring anything missing. A 4-page PDF's pages 3 and 4 regularly contain the exact statement an auditor wants. "Missing" is a claim about every page held, not every filename.
4. **Classify by content, never by filename.** Filenames lie; the page does not.
5. **Checklist wording is verbatim.** Requirement text comes from `data/lm-checklist.json` unchanged. This is LM's audit standard, not ours - never add, drop or reword an item.
6. **Never guess an unmatched applicant.** A document that fails the name-match gate is flagged as a possible wrong-person document, not credited to anyone.
7. **The model asserts facts; code computes verdicts.** Every current/stale/missing decision is date arithmetic done by the builder and the report's embedded renderer, never by judgement.
8. **Forensic signals are investigation leads, not proof.** State each once, weigh it against the document's other evidence, and never accuse - recommend verification steps.
9. **Fail in plain English.** When something breaks, say what happened and the one step that fixes it. `TROUBLESHOOTING.md` in the plugin root holds the known cases.

## Modes

| Command | What it does |
|---|---|
| `/audit <client>` | Full audit: forensics + every-page read + checklist + red flags + policy + report |
| `/audit <client> quick` | Checklist and freshness only. Skips transaction-level scans and deep forensics. The report banner states the reduced scope. |
| `/audit-setup` | First-run wizard (see `setup.md`). Re-run any time to change folders or branding. |
| `/audit-demo` | Full pipeline on the bundled synthetic client at `${CLAUDE_PLUGIN_ROOT}/example/demo-client/`. Proves the install end to end - it must catch the planted doctored payslip. |
| `/audit-doctor` | Diagnostics: config present, paths resolve, data files readable, Python probe, output dir writable, sample report builds. Short output the broker can screenshot for support. |

The setup, demo and doctor modes are one-word commands (own skills in this plugin) so they autocomplete and nothing in the instructions carries a space. `/audit setup`, `/audit demo` and `/audit doctor` typed with a space reach the same modes - treat the second word as the mode selector, never as a client name.

## Step 0 — Config

Read `~/.claude/file-audit.config.json`. If missing, run the wizard in `setup.md` first. **Exception: the demo and doctor modes run without config** (that is the point of the doctor-demo-setup install order); the demo falls back to office name "Loan Market" and output `~/Documents/LM File Audits/`. Shape:

```json
{ "schema_version": 1,
  "clients_root": "/abs/path/to/folder-of-client-folders",
  "office_name": "Loan Market Ignite",
  "output_dir": "/abs/path (default ~/Documents/LM File Audits)",
  "python": "python3 | python | py -3 | none",
  "os": "mac | windows" }
```

## Step 1 — Resolve the client folder (read-only)

- Glob one and two levels under `clients_root` for directory names containing the query (case-insensitive). Client folders are often `Surname, Firstname` - try surname-only if the full query misses.
- Multiple hits: list them and ask which one. Zero hits: say so and show the nearest names - never scan the whole book unasked.
- **Drive-not-synced guard:** if the folder exists but files read as empty, error, or are placeholder stubs, STOP and say: "Google Drive has not downloaded these files to this computer. Open the folder in Finder/File Explorer, right-click and make it available offline, then re-run." Do not report documents as missing when the drive is simply not synced.

## Step 2 — Inventory

List every file recursively (Glob, read-only). Record path, extension, size. Nothing is skipped silently:
- `.gdoc` / `.gsheet` / `.gslides` are Google-native stubs that cannot be read from disk → `unclassified[]` with "export as PDF to include".
- Password-protected or unreadable files → `unclassified[]` + ask the broker for an open copy.
- Images (jpg/png/heic) are documents too - they get the visual pass but no PDF forensics.

## Step 3 — PDF forensics (skip in quick mode)

Run once over every PDF:

```
<python> "${CLAUDE_PLUGIN_ROOT}/scripts/pdf_forensics.py" "file1.pdf" "file2.pdf" ...
```

Attach each result to the document. Interpret producer/creator, dates, incremental saves and edit markers using the per-doc-type weighting in `fraud-checks.md` - a Word-produced ID photo is routine, a Word-produced payslip is a high flag. If Python is unavailable (`"python": "none"`), note "metadata forensics unavailable on this machine" once and continue - the visual and arithmetic checks still run.

## Step 4 — Read every page

Use the Read tool on each document. PDFs over 10 pages: read in page-range chunks until the last page is covered. Record `pages_total` and `pages_read` - any shortfall shows in the report.

While reading, in one pass per document:
- **Classify** against `data/doc-type-taxonomy.json` (`classifier_signals`). Valid `type` values are the taxonomy keys plus the compliance keys in `data/checklist_rules.json` (`privacy_consent`, `game_plan`, `client_quote`). Unknown content → `"unknown"`, never a guess.
- **Split multi-document files**: one PDF holding a licence (p1) and a Medicare card (p2) becomes two `documents[]` entries sharing a file path.
- **Extract the key date** using the `date_label` for the type in `data/checklist_rules.json` (`period_end`, `statement_end`, `expiry`, `financial_year`, `executed`, `issue`, `none`). Prefer `date_source: "content"`; use `filename` or `metadata` only when the pages genuinely carry no date.
- **Note visual tells** per `fraud-checks.md`: fonts, alignment, spelling, paste artefacts, layout vs the institution's real format.
- **TFN/CRN discipline** per rule 2. ID documents follow `id-crossmatch.md` (QLD reads surname-first, the "Effective" date is not a DOB, Medicare has no DOB, a licence back carries a suburb not a person).

After every 3-4 documents, append what you have to the findings JSON on disk (Step 9 path). A crash or interruption then loses minutes, not the run; on a same-day re-run, offer to resume from the partial findings.

## Step 5 — Applicant matching

Derive applicant names from the folder name and the ID documents. For each document bearing a person's name, fuzzy-match against the applicants (token-set similarity in [0,1], `score` = best, `second` = runner-up):

```
matched = (score >= 0.50) if one applicant
          else (score >= 0.62 and (score - second) >= 0.12)
```

Fail the gate → `applicant_match.status: "unmatched"` → red flag `wrong_person_doc`. Never guess. DOB from ID documents seeds the cross-document DOB consistency check (Medicare cards carry no DOB - never use one for DOB matching).

## Step 6 — Deal-profile inference

From the documents themselves: contract of sale → purchase; home-loan statements or discharge with no contract → refinance; builder's contract or plans → construction. Payslips → PAYG; tax returns + entity financials → self-employed full doc; accountant's letter or BAS without returns → alt doc. Conditional categories (rental, government income, child support, guarantors, trusts) switch on only when evidence exists.

Always `confirmed: false` unless the broker stated the deal type - the report header then shows "ASSUMED, confirm". If purchase and refinance signals genuinely conflict, ask one clarifying question before writing findings.

## Step 7 — Checklist assessment

Build `checklist_items[]` from `data/lm-checklist.json` for every applicable category: `requirement` = the item label verbatim, `need` from `logic` (`one-of` → 1, `count-2` → 2, `all` → per item), `rule_text` from `data/checklist_rules.json`. Stamp each document's `max_age_days` from `doc_currency` (the builder applies `category_overrides` per item automatically - the same bank statement can be current as salary evidence and stale for living expenses).

Baked-in judgement calls:
- **Compliance execution documents are out of scope.** Client-executed Privacy Consent, Game Plan and Quote are signed and stored in the CRM, outside the client's document folder - the checklist data deliberately omits them. Never audit them, never list them as missing, and never re-add them from general knowledge. If one happens to be in the folder, it appears in the document inventory like any other file, with no checklist item.
- **2 valid IDs of {passport, licence, Medicare} satisfy identification** - never request a third once two are valid. But at least one held ID must show the current residential address; Medicare and passports never do, so cover the gap with an action, not a "missing".
- An ATO income statement marked **"not tax ready"** is never final-year evidence: set `is_latest_fy: null` so it lands as "check", and say why in the action.
- Payslip recency (<60 days) and **2+ pay cycles in YTD** are separate findings - a fresh payslip with 3 weeks of YTD passes recency and still raises the policy flag.
- Write a specific `action` for anything not clean; the builder supplies generic defaults otherwise.

## Step 8 — Fraud, conduct and policy passes

- **Authenticity** (`fraud-checks.md`): arithmetic reconciliation (payslip internals, YTD progression, ABN checksum via `pdf_forensics.py --abn`, statement balance continuity), cross-document ties (net pay vs salary credits, salary staging, employer and ABN everywhere, name and DOB consistency), forensic signal weighting, payslip fraud score, per-document `authenticity` block with verdict `clean | review | fail`.
- **Bank statements always get the three-question scan** (full mode): are the salary credits real (staging tells), is there gambling, and is money going out to liabilities nobody disclosed. These three run on every statement page, every time.
- **Conduct** (`red-flags.md`): gambling, BNPL vs disclosed, dishonours, undisclosed regular repayments, large unexplained deposits, liability repayment sanity. Transaction-level scans are skipped in quick mode.
- **Policy** (`policy-constraints.md`): short YTD, new employment, casual and variable income history, alt-doc ABN and GST age, ATO debt, HECS, visa conditions.

Each red flag: `check` key from the catalogue, `severity` high/medium/low, one-line `summary`, `evidence` quoting date + merchant + page (never a TFN/CRN), `doc_ids`, `pages`, and a `recommendation` phrased for the credit officer.

## Step 9 — Findings JSON

Written to `<output_dir>/<Client>/<Client> - findings <YYYY-MM-DD>.json`. **Never inside the client folder.** All dates ISO `YYYY-MM-DD` except `financial_year` docs, whose `key_date` is the FY year ("2026"). No statuses anywhere - the builder computes them.

```jsonc
{
  "schema_version": 1, "generated_by": "file-audit <version>",
  "client": "...", "run_date": "YYYY-MM-DD",
  "office": { "name": "<from config>" },
  "freshness_backstop_days": 183,
  "applicants": [ { "name", "aliases": [], "dob", "dob_sources": [], "role", "employment" } ],
  "deal_profile": { "purpose", "doc_basis", "confirmed": false, "basis",
                    "applicable_categories": [], "na_categories": [ { "id", "reason" } ] },
  "documents": [ { "id": "d001", "file": "<relative to client folder>",
      "pages_total", "pages_read", "type", "type_confidence",
      "applicant_match": { "name", "score", "second", "status" },
      "key_date", "date_label", "date_source", "max_age_days",
      "counted_under": [], "is_latest_fy": null, "in_date_override": null,
      "tfn_present": false,
      "authenticity": { "producer", "creator", "creation_date", "mod_date", "eof_count",
        "tamper_signals": [ { "signal", "detail" } ],
        "checks": [ { "name", "result": "pass|flag|info|unavailable", "detail" } ],
        "fraud_score", "verdict": "clean|review|fail" },
      "notes": "" } ],
  "checklist_items": [ { "category_id", "category_label", "applicable", "basis",
      "requirement": "<verbatim>", "logic", "need", "optional", "rule_text",
      "doc_ids": [], "action": "" } ],
  "red_flags": [ { "id", "check", "severity", "summary", "evidence",
      "doc_ids": [], "pages": [], "recommendation" } ],
  "policy_flags": [ { "id", "topic", "observed", "why_it_matters",
      "resolving_evidence", "doc_ids": [] } ],
  "unclassified": [ { "file", "reason" } ],
  "notes": []
}
```

`example/example-findings.json` is a complete worked example.

## Step 10 — Build the report and summarise

```
<python> "${CLAUDE_PLUGIN_ROOT}/scripts/build_report.py" "<findings.json>"
```

It validates, injects the findings and the live rules file into `report-template.html`, writes `<Client> - File Audit <YYYY-MM-DD>.html` beside the findings, and prints the deterministic tallies. Open the report for the broker (`open` on Mac, `start` on Windows).

**No Python on this machine:** Read `scripts/report-template.html`, replace `__RULES_JSON__` with the exact contents of `data/checklist_rules.json` and `__FINDINGS_JSON__` with the findings JSON you authored (replace any `</` with `<\/` in both), and Write the result to the same output path. The embedded JavaScript does all the arithmetic, so the report is identical either way. Perform the TFN-shape scan yourself first (rule 2).

Then give the chat summary, Australian English, DD/MM/YYYY: file verdict and completeness, deal profile (flagged ASSUMED if inferred), top flags by severity, the outstanding list, and the report path. Keep it short - the report carries the detail.
