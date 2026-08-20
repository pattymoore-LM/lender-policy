---
name: audit-demo
description: Use when the broker types /audit-demo or asks to run the file-audit demo. Runs the full audit pipeline on the bundled synthetic client so the broker can prove the install on their machine before touching real client data. One-word alias for the audit skill's demo mode.
---

# /audit-demo — prove the install on synthetic data

This is the one-word alias for the audit skill's demo mode. Read `${CLAUDE_PLUGIN_ROOT}/skills/audit/SKILL.md` and run its **`/audit demo`** mode exactly as written: full pipeline (forensics, every-page read, checklist, red flags, report) over the bundled synthetic client at `${CLAUDE_PLUGIN_ROOT}/example/demo-client/`.

The demo must catch the planted doctored payslip (`Income/Payslip_Alex_25.07.2026.pdf`) - if it does not, something is wrong; point the broker at `${CLAUDE_PLUGIN_ROOT}/TROUBLESHOOTING.md`. Every document in the demo folder is fabricated SPECIMEN data; no real client is involved.

**No config needed.** The demo runs before `/audit-setup` on a fresh install: if `~/.claude/file-audit.config.json` does not exist, do NOT run the setup wizard - use office name "Loan Market", write output to `~/Documents/LM File Audits/`, and carry on. If a config exists, use its office name and output folder.
