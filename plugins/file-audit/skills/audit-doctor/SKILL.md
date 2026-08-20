---
name: audit-doctor
description: Use when the broker types /audit-doctor or asks to check, diagnose or troubleshoot the file-audit install. Runs the health checks and prints a short screenshot-able status block. One-word alias for the audit skill's doctor mode.
---

# /audit-doctor — install health check

This is the one-word alias for the audit skill's doctor mode. Read `${CLAUDE_PLUGIN_ROOT}/skills/audit/SKILL.md` and run its **`/audit doctor`** mode exactly as written: config present and paths resolve, the three data files parse, Python probe, both script selftests (`pdf_forensics.py --selftest`, `build_report.py --selftest`), output folder writable.

Output one short block the broker can screenshot for support. Every failure line names the one step that fixes it, per `${CLAUDE_PLUGIN_ROOT}/TROUBLESHOOTING.md`.
