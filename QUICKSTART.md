# Build it yourself in about 30 minutes

The plugin does all of this for you. This is the DIY route if you'd rather have Claude build it from scratch on your machine, or you're on a Claude Code version without plugins.

**What you end up with:** your Quickli policy library, plus your lenders' own credit manuals, saved on your laptop. Ask a plain English question like "who takes 100% of nurse overtime" and get every lender's position in seconds.

**You need:** Claude Code (on a Pro or Max plan), the Claude for Chrome extension, and your own Quickli login.

## Steps

1. Install Claude Code and add the Claude for Chrome extension.
2. Log into Quickli in Chrome and open the Policy Library.
3. Open Claude Code and paste the prompt below.
4. Let it run. It reads the library through your own logged-in session and writes one file per lender on your machine. Nothing is uploaded anywhere.
5. Download your main lenders' full credit policy PDFs from their broker portals, drop them in the same folder, and tell Claude to add them. The manual beats the summary every time.
6. Ask it anything. Re-run the refresh once a month.

## The prompt to paste

> Build me a local lender policy knowledge base. I'm logged into Quickli in Chrome.
>
> 1. Create a folder `~/lender-policy`.
> 2. Using the Chrome extension, on the Quickli policy library page, capture the policy content for every lender on my panel. The page requests `/api/policy` with a `triggers` parameter on load — read the current topic list from that request rather than assuming one. Throttle the calls, about 150ms apart.
> 3. Write one markdown file per lender, using identical topic headings across every file, so that searching one topic across all files gives me a cross-lender comparison.
> 4. For each lender, list explicitly the topics it has **no** entry for, so you say "no entry" rather than guessing a position.
> 5. Write an `INDEX.md` listing each lender, its file, its topic count, and its policy update date. Use Quickli's `policyUpdateDate`, not `policyConfirmedDate` — the confirmed date moves constantly and doesn't mean the policy changed.
> 6. Keep the raw snapshot and a manifest of per-lender block counts, so the next refresh can compare against it and warn me if any lender's content shrinks by more than 10%. A half-failed pull returns fewer blocks without erroring, and I want to know.
> 7. Then create a `/policy` skill so I can ask questions in plain English, plus a refresh mode that only re-pulls the lenders whose policy update date has moved since last time.
>
> Rules: everything stays local, never send policy content to a web search or any external service, quote policy lines verbatim rather than paraphrasing, and end every answer with the snapshot date and the line "confirm live in Quickli before advice".

## Two things worth saying

The policy content is Quickli's product under your own subscription. Keep the files on your own machine and don't pass them around — if a mate wants this, send them this page and they build their own.

And it's a research tool, not advice. The recommendation is still yours after you look at the client.

## Optional, once it's running

Ask Claude to schedule a weekly check that compares each lender's policy update date against what you've already got and re-pulls only the ones that moved. Takes seconds, and you stop quoting a lender whose policy changed three weeks ago.

Then read [LESSONS.md](LESSONS.md) — the handful of things that took me longest to work out.
