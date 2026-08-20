# broker-tools

Two Claude Code plugins for Australian mortgage brokers. Add the marketplace once and
you get both:

```
/plugin marketplace add pattymoore-LM/lender-policy
```

| | |
|---|---|
| **[lender-policy](#lender-policy)** | Your Quickli policy library, searchable in plain English. |
| **[file-audit](#file-audit)** | Read-only compliance audit of a client's document folder, with fraud detection. |

---

# lender-policy

Ask your lender policy library a question in plain English and get every lender's position in seconds, with the policy line quoted verbatim and a freshness date.

```
/policy which lenders accept 100% of essential services overtime
/policy what's ING's policy on casual income
/policy compare SMSF max LVR across my panel
/policy who's my BDM contact at Pepper
```

Instead of opening Quickli and clicking through lender by lender.

## Install

Two lines inside Claude Code. No Terminal, no git, no GitHub account.

```
/plugin marketplace add pattymoore-LM/lender-policy
/plugin install lender-policy@broker-tools
```

Then `/policy build` for the first pull. Takes a few minutes.

Stuck? **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** covers every failure anyone has hit so far.

## Not on Claude Code?

**Nothing to install.** Paste [one script](plugins/lender-policy/scripts/pull-and-build.js)
into Chrome, it downloads your whole panel as a single file, drag that into a Claude
or ChatGPT Project and ask away — on your laptop or your phone.

No Terminal, no Python, no VS Code, no GitHub account. See **[PORTABLE.md](PORTABLE.md)**.

*(Microsoft 365 Copilot can't do this — it cannot read your files, including from
OneDrive. GitHub Copilot can, but only inside VS Code. The Project route is easier
than both.)*

## What you need

1. **A paid Quickli login.** This is the hard floor. The plugin contains no policy content, so without your own subscription there is nothing to pull.
2. **Claude Code**, and ideally the Claude in Chrome extension so the pull runs hands-free. There's a no-extension fallback if not.
3. **Python 3** — already on every Mac. The scripts are standard library only, nothing to install.

## Read this before you start

**The policy content is Quickli's product and you hold it under your own subscription.** This repo contains none of it — only the tooling that builds your copy from your own login.

So keep your rendered files local. Don't share them, don't paste them into web tools or a web chatbot, don't bundle them into anything you hand another broker. If a mate wants this, send them these two install lines and they build their own from their own login. That is the whole design, and it's what makes the thing shareable at all.

**It's a research tool, not advice.** Every answer ends with the snapshot date and "confirm live in Quickli before advice", because the snapshot is a fast lookup and Quickli live is the authority. Lender policy moves. The recommendation is still yours after you look at the client.

## What you get, and what you don't

**You get the machine and the method.** The scripts, the skill, the refresh procedure, and the lessons. Your Quickli layer rebuilds from your own login: same topics, same file shape, your panel, your dates. On day one you have a complete, queryable policy KB.

**You don't get anyone else's library.** Two layers matter here:

- The **Quickli layer** builds itself from your subscription. Nothing to collect.
- The **`primary/` layer** — the lenders' own full credit policy manuals, pulled from their broker portals — starts empty and is where most of the value accumulates over time. You add your main lenders' manuals as you collect them, using the bundled `ingest_pdf.py`. That's your accreditations and your portal logins, so nobody can hand it to you.

The manual beats the summary every time. Quickli tells you a lender's position; the manual tells you the conditions on it. Start with the five or six lenders you actually use.

## How it works

One markdown file per lender, every file using the same `## Topic` headings. That's the whole trick: **a grep for one heading across all the files IS a cross-lender comparison**, so nothing ever has to load thousands of policy blocks to answer one question.

```
~/.claude/lender-policy/
  lenders/<slug>.md    one per lender, identical headings
  INDEX.md             freshness table — what was updated when
  topics.md            the canonical topic list
  desk.md              BDM contacts, policy links, SLAs
  primary/<slug>/      lender credit manuals you add yourself
  _source/<date>/      every raw snapshot + a manifest, kept as history
```

See [`example/example-lender.md`](plugins/lender-policy/example/example-lender.md) for the file shape (synthetic — not a real lender).

Refreshes are incremental: only lenders whose policy actually moved get re-pulled. Monthly is a sensible cadence, or before a tricky placement.

## Docs

| | |
|---|---|
| **[LESSONS.md](LESSONS.md)** | What I got wrong building this, so you don't have to. Worth five minutes. |
| **[PORTABLE.md](PORTABLE.md)** | The no-Claude route: Copilot, Cursor, or no AI tool at all. |
| **[portable/AGENTS.md](portable/AGENTS.md)** | Drop-in instruction file for Copilot/Cursor. Read automatically by VS Code. |
| **[QUICKSTART.md](QUICKSTART.md)** | The DIY version if you'd rather build it yourself than install a plugin. |
| **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** | When it doesn't work. Every failure a real person has hit, with the fix. |

## Updates

When Quickli changes something and the pull breaks, I fix it here and bump the version. Your Claude Code picks it up on the next session. You don't have to do anything.

---

# file-audit

**The file check you'd do if you had an hour per client.** A read-only audit of one
client's document folder, doing two jobs at once.

**Fraud detection.** Is every document what it claims to be? PDF metadata forensics
(what software made it, was it modified after the pay date, hidden edit markers),
payslip arithmetic that must reconcile to the cent, YTD progression across payslips,
ABN check digits, bank-statement balance continuity, salary credits tied back to
payslips, and name and DOB consistency across every document.

**Checklist validation.** Does the file meet the Loan Market minimum supporting
documents checklist? Every item checked as present, in date and showing the right
data, with the freshness windows computed by code rather than judgement.

Every bank statement gets three questions as a minimum: are the salary credits real
(staging tells — wrong payer, round amounts, wrong cadence, deposit-then-sweep), is
there gambling, and is money going out to liabilities nobody disclosed.

You get one self-contained HTML report per audit, branded for your office: checklist
status, the documents still to request, a per-document authenticity card, and a
consolidated action list for the credit officer.

## Install

```
/plugin install file-audit@broker-tools
```

**Then restart Claude Code** — plugins load on start, and until you restart `/audit`
says "Unknown command".

Then, in order:

```
/audit-doctor      confirms the install on your machine
/audit-demo        full audit on a bundled synthetic client — must catch the planted doctored payslip
/audit-setup       points it at your clients folder, sets your office name
/audit <surname>   audit a real client
```

## What it needs

Claude Code, and your client documents in a local folder with one subfolder per
client — Google Drive for Desktop, Dropbox, OneDrive or a plain folder all work the
same. Python 3 makes the metadata forensics available; without it everything else
still runs.

## What it never does

Never writes, renames, moves or deletes anything in a client folder — reports go to
your output folder only. Never records a TFN or Centrelink CRN anywhere, and the
report builder refuses to build if one slips in. Never sends anything anywhere.
Never makes the credit decision: forensic signals are investigation leads, checklist
verdicts are date arithmetic, and the recommendation always belongs to the broker.

Full detail in [plugins/file-audit/README.md](plugins/file-audit/README.md).

---

## Credit

Built by Patrick Moore, mortgage broker at Loan Market Clayfield — lender-policy because clicking through Quickli lender by lender for the same five questions got old, file-audit because the document check that catches a doctored payslip takes an hour nobody has.

Not affiliated with or endorsed by Quickli. MIT licensed — see [LICENSE](LICENSE).
