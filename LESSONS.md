# What I learned building this

A year of small wrong turns, so you can skip them. Most of these are already baked into the scripts and the skill — this is the why, for anyone who wants to understand the thing rather than just run it.

## The manual beats the summary

Quickli tells you a lender's position. The lender's own credit manual tells you the conditions on that position, and the conditions are usually where the deal lives or dies. When the two disagree, the manual wins.

So the KB has two layers and a fixed precedence: **lender manual beats Quickli beats aggregator.** Aggregator content (Brokers' Bible, Brokerpedia and the rest) only gets used where the first two are silent, always labelled as aggregator, never quoted as the lender's own position. Every answer names which layer it came from.

Go and download your main lenders' full policy PDFs from their broker portals. Five or six lenders covers most of your book, and it is the single biggest upgrade you can make to this thing.

## One decoy date, one real one

Quickli publishes two dates per lender. `policyConfirmedDate` moves constantly as they do their rolling confirmations, and it tells you nothing about whether the policy changed. `policyUpdateDate` is the real signal.

I tracked the wrong one first, which meant every refresh looked like everything had changed, which meant re-pulling all 45 lenders every time, which meant I stopped refreshing. Track `policyUpdateDate`, refresh only what moved, and the monthly refresh takes seconds instead of twenty minutes.

## A half-failed pull doesn't look like a failure

If the pull drops a lender's blocks partway through, you don't get an error. You get a smaller file. Your KB quietly shrinks and you carry on quoting a lender whose entry is now three topics deep instead of thirty.

So `render.py` keeps a per-lender block count in a manifest and compares every render against the previous one. Any lender losing more than 10% of its blocks gets flagged loudly. And a lender that comes back empty is skipped entirely rather than overwriting a good file with a bad one.

An absence of change is a finding. Prove it, don't assume it.

## Say "no entry" out loud

Every lender file ends with a `## No Quickli entry for` section listing every topic that lender has nothing on. It looks like clutter. It is the most important part of the file.

Without it, an assistant asked about a topic the KB never covered has nothing to push back against, and a confident guess reads exactly like a real answer. With it, the honest answer is right there in the file. Never let a policy tool invent a policy position.

## The rule often lives only in a formula

On a lender's servicing calculator, the number that matters frequently appears nowhere in a visible label — it is buried in a cell formula. A tool that reads only the displayed text of a workbook will miss the actual rule.

`ingest_xlsx.py` reads cell text **and** the underlying formulas, which is the entire reason it exists.

## A formula cell's cached value is client data

Related, and I got this wrong the first time. When a calculator arrives already filled in for a live deal, "just keep the formulas and drop the constants" feels safe. It isn't. Every formula cell also carries a cached result, and those cached values are the client's name, their income, their loan amount.

`ingest_xlsx_safe.py` handles this: keeps formulas and whitelisted reference sheets, drops typed constants *and* cached values, and prints everything it withheld so you can eyeball it. Never archive a filled workbook into the KB — archive the blank template with a note saying why.

## Don't let a policy KB do arithmetic

This one took a while to accept. A policy summary is the wrong instrument for a servicing calculation, and an assistant holding 3,000 policy blocks will absolutely have a go if you let it.

Keep the split absolute. The KB answers eligibility, shading, documents, security. The number comes from the lender's calculator. If you build a servicing engine as well, keep it separate and check for drift between the two deliberately — they will fall out of step, and the failure is silent.

## Read the surviving sentence, not the deleted one

When a lender shortens a clause, the instinct is to read the deletion as a loosening. Usually it isn't. Documents get tidied constantly, and redundant enumerations are the first thing to go.

The test is what the remaining text still forbids on its own. I nearly acted on a "loosened" rental gearing clause where the governing sentence survived word for word and still excluded exactly what the deleted list had spelled out. A diff tells you what changed; it never tells you what it means.

## Grep is the feature

One file per lender, identical `## Topic` headings across every file. That's it. It means a single grep across the folder is a cross-lender comparison, and nothing has to load the whole library to answer one question.

It also means the KB is useful with no AI tool at all — it's just well-organised markdown. See [PORTABLE.md](PORTABLE.md).
