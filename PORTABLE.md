# Using this without Claude Code

The system is three layers and only the last one is Claude-specific:

1. **The pull** — reads your Quickli library through your own logged-in browser. A pasted JavaScript snippet does this. No AI tool involved.
2. **The render** — turns that into one markdown file per lender. A Python script. No AI tool involved.
3. **The query** — asking questions in plain English. This is the part Claude does.

Layers 1 and 2 work for anyone. What they produce is a folder of well-organised markdown, which is useful on its own and useful to any tool that can read local files.

## Build it with no AI tool at all

**1. Get the two files.** On the repo page, click `plugins/lender-policy/scripts/`, open `pull-snapshot.js` and `render.py`, and use the download button on each. Put them somewhere you can find, like your Downloads folder.

**2. Pull your library.**
- Log into Quickli in Chrome and open the Policy Library at `app.quickli.com.au/policy`
- Click any lender once, so the page loads some policy
- Open DevTools: `Cmd+Option+J` on a Mac, `Ctrl+Shift+J` on Windows
- Paste the whole of `pull-snapshot.js` into the Console and press Enter
- If Chrome asks, type `allow pasting` first, then paste again

It prints progress and downloads `quickli-policy-snapshot-YYYY-MM-DD.json` when it's done.

**3. Render it.** In Terminal:

```bash
python3 ~/Downloads/render.py ~/Downloads/quickli-policy-snapshot-2026-08-19.json --kb ~/lender-policy
```

Change the date to match your file. You get `~/lender-policy/` with one markdown file per lender, an `INDEX.md` freshness table, and a `topics.md` listing every topic heading.

Python 3 is already on every Mac. On Windows, install it from python.org and use `python` instead of `python3`.

## Then use it

### With no AI at all

The files are plain markdown with identical `## Topic` headings, so a single search across the folder is a cross-lender comparison.

```bash
cd ~/lender-policy/lenders
```

Every lender's position on casual income:
```bash
grep -A15 "^## Casual Income" *.md
```

Which lenders say anything about essential services overtime:
```bash
grep -l "Essential Services Overtime" *.md
```

Find the right heading first if you're not sure what it's called:
```bash
grep -i "overtime" ../topics.md
```

One lender, one topic:
```bash
awk '/^## HECS/{f=1;next}/^## /{f=0}f' anz.md
```

Or just open the folder in any editor — VS Code, Sublime, even TextEdit — and use find-in-files. Less magic than asking a question in English, still a great deal faster than clicking through Quickli lender by lender.

### With GitHub Copilot, Cursor, or Codex

The repo ships the instruction file for you — you don't have to write one.

**1.** Download [`portable/AGENTS.md`](portable/AGENTS.md) from this repo and put it
in the root of your KB folder, next to `INDEX.md`:

```
~/lender-policy/
  AGENTS.md          <- this file
  INDEX.md
  topics.md
  lenders/
```

**2.** Open that folder in VS Code (File > Open Folder, pick `~/lender-policy`).

**3.** Ask Copilot Chat a question. That's it.

VS Code reads `AGENTS.md` from the root of any opened folder automatically. No git
repository, no settings to change, no extension beyond Copilot itself.

**Cursor** reads `AGENTS.md` too — same file, nothing extra.

**On ChatGPT?** Use **Codex**, which is included in a ChatGPT Plus, Pro or Team
plan. Codex CLI reads `AGENTS.md` from the project root or the directory you run it
in, so `cd ~/lender-policy` and start Codex there. Same file again.

One instruction file covers all three.

If you'd rather use Copilot's own convention, the repo also ships
[`portable/.github/copilot-instructions.md`](portable/.github/copilot-instructions.md)
with identical content — put it at `~/lender-policy/.github/copilot-instructions.md`
instead. Either works; you don't need both.

**What the instruction file does:** it teaches the tool the same discipline the
Claude Code skill uses — search by `## Topic` heading rather than loading whole
files, quote policy lines verbatim, say "no entry" instead of guessing, respect
lender-manual-beats-Quickli precedence, stamp every answer with the snapshot date,
and never attempt servicing maths.

One difference from Claude Code: none of these drive your browser, so the monthly
refresh is you re-running the DevTools snippet by hand rather than asking for it.
Everything after the pull is identical.

### Not with a web chatbot

ChatGPT, Gemini, Claude.ai and the rest can't read files on your machine, so using them would mean uploading your policy files. Don't. That's Quickli's licensed content going to a third party, and it's the one line this whole design is built to stay on the right side of.

If you want plain-English questions, use a tool that reads the files locally.

## Keeping it current

Re-run the snippet monthly and render it again. Lender policy moves, and a stale answer is worse than no answer.

The plugin version does this incrementally — it checks which lenders actually changed and re-pulls only those. Doing it by hand, you just re-pull everything, which takes a couple of minutes and is fine.
