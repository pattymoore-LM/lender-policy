# Using this without Claude Code

The system is three layers and only the last one is Claude-specific:

1. **The pull** — reads your Quickli library through your own logged-in browser. A pasted JavaScript snippet does this. No AI tool involved.
2. **The render** — turns that into one markdown file per lender. A Python script. No AI tool involved.
3. **The query** — asking questions in plain English. This is the part Claude does.

Layers 1 and 2 work for anyone. What they produce is a folder of well-organised markdown, which is useful on its own and useful to any tool that can read local files.

## Build it with no AI tool at all

Three copy-pastes, about fifteen minutes.

**1. Get the files.** Open Terminal and paste this whole block:

```bash
mkdir -p ~/lender-policy && cd ~/lender-policy && curl -sO https://raw.githubusercontent.com/pattymoore-LM/lender-policy/main/plugins/lender-policy/scripts/render.py -O https://raw.githubusercontent.com/pattymoore-LM/lender-policy/main/plugins/lender-policy/scripts/lender_names.json -O https://raw.githubusercontent.com/pattymoore-LM/lender-policy/main/plugins/lender-policy/scripts/pull-snapshot.js -O https://raw.githubusercontent.com/pattymoore-LM/lender-policy/main/portable/AGENTS.md
```

That gets you `render.py`, its lender-name map, the browser snippet, and the
instruction file that Copilot/Cursor/Codex read.

**2. Pull your library.**

> **This step happens in CHROME, not in Terminal.** Pasting the script into Terminal
> is the single most common mistake — it leaves you at a `quote>` or `dquote>`
> prompt that sits there forever. Press `Ctrl+C` if that happens to you.

First, in Terminal, put the script on your clipboard:

```bash
pbcopy < ~/lender-policy/pull-snapshot.js
```

Nothing visible happens. That is correct. (On Windows: `clip < %USERPROFILE%\lender-policy\pull-snapshot.js`)

Now **switch to Chrome**:

- Log into Quickli and open the Policy Library
- Click any lender once, so the page loads some policy (helps, not essential)
- Press `Cmd+Option+J` (Mac) or `Ctrl+Shift+J` (Windows). A panel opens inside the
  **Chrome window** with a `>` prompt. That is the console.
- Click into it, press `Cmd+V` (or `Ctrl+V`), press Enter
- If Chrome refuses to paste, type `allow pasting`, press Enter, then paste again

You'll see progress lines like `10/45 lenders`. When it finishes it downloads
`quickli-policy-snapshot-YYYY-MM-DD.json`.

**3. Build it.** Change the date to match your file:

```bash
cd ~/lender-policy && python3 render.py ~/Downloads/quickli-policy-snapshot-2026-08-19.json --kb .
```

You should see `Rendered N lenders, N policy blocks`. Your folder now looks like:

```
~/lender-policy/
  AGENTS.md          instructions for Copilot / Cursor / Codex
  INDEX.md           freshness table
  topics.md          the topic vocabulary
  lenders/           one file per lender
  render.py          re-run this each refresh
  pull-snapshot.js   re-run this each refresh
```

Python 3 is already on every Mac. On Windows install it from python.org and use
`python` instead of `python3`.

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

Nothing more to install — step 1 above already put `AGENTS.md` in your folder, and
that is the whole configuration.

**Open the folder in VS Code** (File > Open Folder, pick `~/lender-policy`) and ask
Copilot Chat a question. That's it.

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
