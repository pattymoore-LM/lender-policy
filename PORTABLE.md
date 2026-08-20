# Using this without Claude Code

**The easiest route needs no Terminal, no Python, no VS Code and nothing installed.**
One paste into Chrome, one file downloads, drag it into a Claude or ChatGPT Project,
ask it questions. That is the whole thing.

---

## The easy way (start here)

### 1. Get the script

Open [`pull-and-build.js`](plugins/lender-policy/scripts/pull-and-build.js) on
GitHub, click the copy button at the top right of the code, and it's on your
clipboard.

### 2. Run it in Chrome

> **This happens in CHROME, not in Terminal.** Pasting it into Terminal leaves you
> at a `quote>` prompt that never returns. `Ctrl+C` if that happens.

- Log into Quickli in Chrome and open the Policy Library
- Press `Cmd+Option+J` (Mac) or `Ctrl+Shift+J` (Windows). A panel opens **inside the
  Chrome window** with a `>` prompt. That is the console.
- Click into it, paste, press Enter
- If Chrome refuses to paste, type `allow pasting`, Enter, then paste again

It counts through your lenders and downloads one file: `lender-policy-YYYY-MM-DD.md`
— your whole panel, about 4MB.

### 3. Ask it questions

**Claude:** claude.ai → Projects → new project → add the file to the project
knowledge → ask away.

**ChatGPT:** chatgpt.com → Projects → new project → upload the file → ask away.

Either one works on your phone. Ask things like *"which lenders accept 100% of
essential services overtime"* or *"compare SMSF max LVR across my panel"*.

The file carries its own instructions at the top — quote policy word for word, say
"no entry" rather than guessing, stamp answers with the snapshot date — so there is
nothing to configure.

### 4. Add your lenders' own manuals (optional, and where the value is)

Quickli tells you a lender's position. Their credit manual tells you the
conditions on it, and the manual wins whenever they disagree.

**You don't need any tooling for this.** Download your main lenders' policy PDFs
from their broker portals and drag them straight into the same Project — Claude and
ChatGPT both read PDFs. Five or six lenders covers most of a book.

Tell the project, in its instructions: *"The lender PDFs outrank the Quickli file.
Where they disagree, lead with the PDF and say the summary differs."*

(If you already have manuals ingested into a `primary/` folder from the Terminal
route, `build-manuals-file.py` combines them into one file instead. It deliberately
skips servicing-calculator extractions — those are for a calculator, not a policy
question, and they cost several million tokens for nothing.)

### 5. Refresh monthly

Re-run step 2 and replace the file in your project. Lender policy moves, and a stale
answer is worse than none.

---

## The Terminal way

Use this if you want the KB as separate files on disk — one per lender, greppable,
and what the Claude Code plugin expects.

**1. Get the files.** In Terminal:

```bash
mkdir -p ~/lender-policy && cd ~/lender-policy && curl -sO https://raw.githubusercontent.com/pattymoore-LM/lender-policy/main/plugins/lender-policy/scripts/render.py -O https://raw.githubusercontent.com/pattymoore-LM/lender-policy/main/plugins/lender-policy/scripts/lender_names.json -O https://raw.githubusercontent.com/pattymoore-LM/lender-policy/main/plugins/lender-policy/scripts/pull-snapshot.js -O https://raw.githubusercontent.com/pattymoore-LM/lender-policy/main/portable/AGENTS.md
```

**2. Pull.** Put the script on your clipboard, then paste it into Chrome's console
exactly as in step 2 above:

```bash
pbcopy < ~/lender-policy/pull-snapshot.js
```

(Windows: `clip < %USERPROFILE%\lender-policy\pull-snapshot.js`)

This one downloads a `.json`, not a `.md`.

**3. Build.** Change the date to match your file:

```bash
cd ~/lender-policy && python3 render.py ~/Downloads/quickli-policy-snapshot-2026-08-19.json --kb .
```

You get `lenders/` with one file per lender, `INDEX.md` with the freshness table,
and `topics.md` with the heading vocabulary.

Python 3 is on every Mac. On Windows install from python.org and use `python`.

### Then search or ask

**Search, no AI:** open the folder in VS Code and press `Cmd+Shift+F`, then type a
heading like `## Casual Income`. Every lender's position in one list. Or on the
command line, `grep -A15 "^## Casual Income" lenders/*.md`.

**Ask, with GitHub Copilot or Cursor:** step 1 already put `AGENTS.md` in the folder,
which is the whole configuration. Open the folder in VS Code and ask Copilot Chat.

> ### ⚠️ Two different products are called Copilot
>
> **GitHub Copilot** — a VS Code extension, reads your open folder. Free tier
> available from the Extensions panel inside VS Code.
>
> **Microsoft 365 Copilot** (`m365.cloud.microsoft`) — the Word/Excel/Teams one.
> **It cannot read your files at all, including from OneDrive or SharePoint**
> (confirmed 20/08/2026). If it says *"I cannot use your VS Code workspace"*, that
> is this one.
>
> Fair warning: GitHub Copilot works, but it only works inside VS Code, which is a
> developer tool. If that sounds like a hassle for looking up lender policy, it is —
> use the Project route at the top of this page instead.

**On ChatGPT?** Either the Project route above, or **Codex** (included in a ChatGPT
Plus/Pro/Team plan), which reads `AGENTS.md` from the directory you run it in.

---

## When it doesn't work

See **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)**. Every failure listed there has
happened to a real person.
