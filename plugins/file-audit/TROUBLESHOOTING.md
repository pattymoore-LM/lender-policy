# file-audit troubleshooting

Every known failure, with the fix. If you're stuck, run `/audit doctor` and screenshot the output - that one image is usually enough for support.

## Install

**`/plugin marketplace add` says not found.** The address is exactly `pattymoore-LM/lender-policy` (the repo hosts the whole broker-tools marketplace, the name is historical). You need internet access; no GitHub account is required.

**Installed but `/audit` does nothing.** Restart Claude Code - plugins load on start. If it still misses, `/plugin` should list `file-audit@broker-tools` as installed.

**`/audit` runs something else on your machine.** Another tool of yours may own the word. Ask Claude to "run the file-audit plugin's audit skill" - and tell us, so we know the name clashes in the wild.

**You updated but nothing changed.** Claude Code caches plugins by version. If a fix was announced, confirm the version bumped in `/plugin`; restart Claude Code. (For the maintainer: every change must bump the version in BOTH `plugin.json` and `marketplace.json`.)

## Folders and Drive

**"Google Drive has not downloaded these files."** The folder exists but the files are cloud-only placeholders. In Finder (Mac) or File Explorer (Windows), right-click the client folder → "Make available offline" / "Always keep on this device", wait for the sync tick, re-run.

**Client not found.** `/audit` searches two folder levels under your clients root, case-insensitive, and client folders are usually "Surname, Firstname" - try just the surname. If your clients live somewhere else entirely, `/audit setup` and repoint.

**Google Docs / Sheets in the folder.** `.gdoc`/`.gsheet` files are web links, not documents - nothing on your computer can read their contents. The report lists them as "not assessed". Export each one as PDF into the folder to include it.

**Windows drive letter changed.** Drive for Desktop sometimes remounts on a different letter. `/audit setup` and re-pick the folder.

## Python and the report

**"No Python found."** Fine - the audit still runs fully and the report builds via the built-in fallback. The only loss is PDF metadata forensics (producer software, modification dates). To enable them: install Python 3 from python.org with default settings (on Windows tick "Add python.exe to PATH"), then `/audit setup` to re-probe.

**Report builder refused: "TFN-shaped number in findings".** Working as designed - the audit never records tax file numbers. Ask Claude to rewrite the offending evidence line without the number and rebuild.

**The report opens blank.** It computes verdicts in JavaScript. Open it in a normal browser (double-click); if your organisation blocks local JavaScript, print it to PDF from a machine that doesn't, and send the PDF instead.

**Someone emailed the report and it broke.** Some mail systems strip scripts from HTML attachments. Share the report as a PDF: open it, Print → Save as PDF.

## Results

**Everything is flagged stale on the demo.** Expected eventually - the demo documents carry fixed dates and age like real ones. The demo's job is proving the pipeline runs and the doctored payslip gets caught.

**A legitimate document got a tamper signal.** That's what "investigation lead, not proof" means: scanners, email gateways and browser saves re-save PDFs legitimately, and clients photograph IDs into Word. The report weighs signals by document type and says why; if a clean pattern keeps flagging, report it so the weighting table learns.

**The audit takes a while on big files.** It reads every page deliberately. Use `/audit <client> quick` for a fast completeness pass; keep the full run for pre-submission.
