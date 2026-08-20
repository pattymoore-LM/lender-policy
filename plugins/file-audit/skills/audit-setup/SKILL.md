---
name: audit-setup
description: Use when the broker types /audit-setup or asks to set up, configure or re-point the file audit (clients folder, office branding, output folder). Runs the first-run wizard. One-word alias for the audit skill's setup mode.
---

# /audit-setup — first-run wizard

This is the one-word alias for the audit skill's setup mode. Read `${CLAUDE_PLUGIN_ROOT}/skills/audit/SKILL.md` and follow `${CLAUDE_PLUGIN_ROOT}/skills/audit/setup.md` exactly as written: locate the folder of client folders (Drive for Desktop or any local folder), confirm it against a live listing, ask the office name for report branding, set the output folder, probe for Python, write `~/.claude/file-audit.config.json`, then offer `/audit-demo`.

Re-running any time is safe; it just rewrites the config.
