# /audit setup — first-run wizard

Creates `~/.claude/file-audit.config.json`. Runs automatically when `/audit` finds no config; `/audit setup` re-runs it any time. Everything here is read-only except writing the config file and creating the output folder.

## 1. Find the clients folder

The tool needs one local folder that contains one subfolder per client. Google Drive for Desktop is the usual route, but ANY local folder works (Dropbox, OneDrive, a plain folder).

Auto-detect candidates, then let the broker pick or paste a path:

- **Mac:** Glob `~/Library/CloudStorage/GoogleDrive-*/` — offer `My Drive` and each folder under `Shared drives/`.
- **Windows:** check `G:/My Drive` and `G:/Shared drives` (and other drive letters if G: is absent — Drive for Desktop mounts as a lettered drive), plus the legacy `%USERPROFILE%/Google Drive`.
- Nothing found: ask whether they use Google Drive for Desktop. If their Drive is web-only, point them at the plugin README's 5-minute Drive for Desktop install, or the `CLAUDE-AI-FALLBACK.md` route.

Confirm the choice by listing the folder (read-only) and asking: "these look like your client folders — correct?" If clients are nested (A-Z folders, year folders), note it — `/audit` searches two levels deep by default.

## 2. Branding

Ask for the office name exactly as it should appear on reports. If the chosen Drive folder sits under a Shared Drive whose name reads like an office (for example "Loan Market Somewhere"), offer that as the default; otherwise default to plain **Loan Market**. Enter accepts the default. This is the only branding input; the report handles the rest.

## 3. Output folder

Default `~/Documents/LM File Audits` (Enter accepts). Create it if needed — the only folder this tool ever creates, always outside the client tree. Reports and findings land in `<output>/<Client>/`.

## 4. Python probe

Try in order: `python3 --version`, `python --version`, `py -3 --version`. Record the first that works as `"python"`; record `"none"` if nothing does and say: "No Python found — the audit still works fully; the report is built by the built-in fallback and PDF metadata forensics are skipped. Nothing to install unless you want them: python.org, default settings."

## 5. Write config and prove the install

Write `~/.claude/file-audit.config.json`, echo it back in plain English, then offer `/audit demo` — the bundled synthetic client proves the whole pipeline on this machine, including catching the planted doctored payslip, before any real client data is touched.
