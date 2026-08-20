# When it doesn't work

Every failure below has either happened to a real person or is one the tooling
can now detect and name. Find your symptom.

---

## The pull (step 2)

### Terminal shows `quote>` or `dquote>` and won't come back

You pasted `pull-snapshot.js` into **Terminal**. It belongs in **Chrome**.

Press `Ctrl+C` to get out. Then:

```bash
pbcopy < ~/lender-policy/pull-snapshot.js
```

Switch to Chrome, on your Quickli tab. `Cmd+Option+J`. Click into the panel that
opens **inside the Chrome window**, `Cmd+V`, Enter.

### "Could not find the topic list"

Fixed in v1.2.1 — the script now falls back to a built-in list instead of giving up.
If you're seeing this, you have an old copy. Re-download it:

```bash
cd ~/lender-policy && curl -sO https://raw.githubusercontent.com/pattymoore-LM/lender-policy/main/plugins/lender-policy/scripts/pull-snapshot.js
```

### "Quickli says you're not signed in"

What it says. Log into Quickli in that tab and paste again.

### "Quickli has moved or renamed this endpoint" / "not in the shape this script expects"

**Not something you did.** Quickli has changed their API and the script needs
updating. Report it at the [issues page](https://github.com/pattymoore-LM/lender-policy/issues)
or tell Pat, and don't burn time on it — no amount of retrying will fix it.

### Chrome refuses to let you paste

Type `allow pasting` into the console, Enter, then paste again. Chrome added this
in 2024 to stop people being talked into pasting things they don't understand,
which is worth taking seriously in general.

### It ran, but some lenders came back empty

Normal. Lenders off your Quickli panel return nothing. The script names them at the
end and carries on.

---

## The build (step 3)

### "No such file or directory"

The date in the command has to match your actual file. Check what you've got:

```bash
ls ~/Downloads/quickli-policy-snapshot-*.json
```

Then use that exact filename.

### "command not found: python3"

**Mac:** it's pre-installed, so this usually means Terminal is confused. Try
`/usr/bin/python3` instead.
**Windows:** install from python.org, and use `python` not `python3`.

### "REGRESSION WARNING — lender X: 78 -> 12 blocks"

The pull half-failed for that lender. Your existing files are untouched, so nothing
is lost. Re-run the pull. If it happens twice for the same lender, report it.

### It says "Rendered 0 lenders"

The snapshot came back empty, which means the pull didn't really work even though
it produced a file. Re-run step 2 and watch the console output this time.

---

## Asking questions (step 4)

### It works but opening VS Code to check policy is a pain

Agreed, and you don't have to. VS Code is a developer tool; nobody is going to open
it mid-call to check whether a lender takes nurse overtime.

Use the Project route instead — see the top of [PORTABLE.md](PORTABLE.md). One paste
into Chrome gives you a single file; drop it into a Claude or ChatGPT Project and ask
questions in a normal chat window, including on your phone. That is the route to give
a team.

### "I cannot use your VS Code workspace" / "I cannot access that folder"

You're in the wrong Copilot. There are two.

| | |
|---|---|
| **GitHub Copilot** | A VS Code extension. Reads your open folder. **This is the one.** Free tier available — Extensions panel in VS Code, search "GitHub Copilot", install, sign in with a GitHub account. |
| **Microsoft 365 Copilot** | `m365.cloud.microsoft` — the Word/Excel/Teams one. **Cannot read these files at all, including from OneDrive or SharePoint** (tested 20/08/2026). It is telling you the truth. Use the Project route in [PORTABLE.md](PORTABLE.md) instead. |

Same name, same company, completely different tools.

You don't need either, though. Open the folder in VS Code and press `Cmd+Shift+F`,
then search a heading like `## Casual Income`. Every lender's position, one list.
See "no AI at all" in [PORTABLE.md](PORTABLE.md).

### Copilot ignores the instructions

Three things to check, in order:

1. Is `AGENTS.md` in the folder you opened, next to `INDEX.md`? Not in a subfolder.
2. Did you open the **folder** in VS Code (File > Open Folder), rather than opening
   a single file?
3. Is it actually Copilot Chat you're typing into, rather than inline suggestions?

### It's making up policy positions

Stop using it and tell Pat. That should be impossible — every lender file lists the
topics it has no entry for, precisely so the honest answer is available. If your
tool is inventing positions anyway, the instruction file isn't being read (see
above) or something is genuinely wrong.

### Answers don't carry a date

Same cause. The instruction file isn't being read.

---

## Keeping it honest

### How do I know if my copy is stale?

Open `INDEX.md`. Every lender has its own "policy updated" and "snapshot" dates.

**Anything older than a month should be confirmed live in Quickli before you rely
on it.** This is a fast lookup, not the source of truth. Lender policy moves, and a
confidently-quoted stale position is worse than no answer.

### How do I refresh?

Re-run steps 2 and 3. Two minutes. Monthly is sensible, or before a tricky placement.

Claude Code users get `/policy refresh`, which only re-pulls lenders whose policy
actually changed.

---

## Still stuck

[Open an issue](https://github.com/pattymoore-LM/lender-policy/issues) with what you
typed and what came back. If you're not a GitHub person, email Pat.

**Never paste your policy files, or screenshots of them, into a public issue.** That
content is Quickli's, held under your subscription. The error message and the command
you ran are enough.
