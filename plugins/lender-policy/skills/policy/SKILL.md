---
name: policy
description: Use when the broker asks what a lender's policy is on anything (casual income, HECS, LVR, construction, self-employed, visas, SMSF), which lenders accept a scenario ("who takes 100% overtime for nurses"), any credit policy comparison across lenders, or who to call at a lender (BDM contacts). Also handles `/policy build` for the first-time setup and `/policy refresh` to re-pull. Local snapshot of the broker's own Quickli subscription; Quickli live is the authority; the snapshot never leaves their machine.
---

# /policy: lender policy lookup

Knowledge base: `~/.claude/lender-policy/` (override with `LENDER_POLICY_KB`). A local snapshot of the broker's own Quickli Policy Library, one markdown file per lender in `lenders/<slug>.md`.

**The layout is the trick.** Every lender file uses the same `## Topic` headings, taken from `topics.md`. So grepping one heading across all the files IS a cross-lender comparison, and you never load thousands of policy blocks to answer one question. Read `INDEX.md` first for the freshness table, `topics.md` for the canonical headings.

If `~/.claude/lender-policy/lenders/` does not exist yet, this is a first run: go to **Build mode** below.

## Query mode: `/policy <question>`

1. Read `INDEX.md` and `topics.md`.
2. Map the question to one to three topic headings from `topics.md`. "Nurse overtime" maps to Essential Services Overtime plus Overtime Income. "HELP debt" maps to HECS / HELP Debt.
3. **Single lender:** read only that lender's section. Extract with awk rather than loading the whole file:
   ```
   awk '/^## <Topic>/{f=1;next}/^## /{f=0}f' ~/.claude/lender-policy/lenders/<slug>.md
   ```
4. **Cross-lender:** run the same extraction across all `lenders/*.md`, then compare. Answer as a table — lender, position, key conditions. Name the best fits first, and quote the load-bearing policy line verbatim rather than paraphrasing it.
5. End every answer with the source line: "Quickli snapshot dd/mm/yyyy, lender policy last updated dd/mm/yyyy. Confirm live in Quickli before advice."
6. **Staleness:** if the cited lender's snapshot is more than 30 days old, say so and suggest `/policy refresh <lender>`.
7. **Never invent policy.** If a lender has no entry for the topic, check that file's `## No Quickli entry for` section and say the KB has no entry. An absent entry is a real answer; a guessed one is a liability.

## Source precedence

Where more than one layer covers the same question:

**Lender's own manual beats Quickli beats aggregator.**

- `primary/<slug>/` holds full credit policy manuals pulled from the lender's own broker portal, if the broker has added any. Search it first for anything about rates, buffers, thresholds or document standards — Quickli is the summary, this is the manual.
- Where the two disagree, lead with the manual and say the Quickli entry differs.
- Aggregator content (Brokers' Bible, Brokerpedia and similar) is used only where the first two layers are silent, always labelled as aggregator with its own date, and never quoted as the lender's own position.
- **Always name which layer the answer came from.**

`primary/` is optional and starts empty. It is also where most of the value accumulates over time, so encourage the broker to add their main lenders' manuals as they collect them (see Adding sources below).

**LMI insurer guidelines** (Helia, QBE) are not a lender's policy and sit on top of whichever lender is chosen. If the broker has added them under `primary/`, check them whenever the deal is above 80% LVR or LMI is otherwise in play — an insurer's DTI and security rules can bind even where the lender's own policy is satisfied.

## Build mode: `/policy build`

First run, when no KB exists yet. Requires the broker logged into Quickli in Chrome.

1. Confirm they have a paid Quickli login and are logged in. Without it there is nothing to pull.
2. Follow `refresh.md` in this directory, with the first-pull specifics it describes (no previous snapshot to compare against).
3. If the Claude in Chrome extension is unavailable, fall back to the bundled snippet: have them paste `${CLAUDE_PLUGIN_ROOT}/scripts/pull-snapshot.js` into Chrome DevTools on the Quickli policy page. It downloads the same snapshot JSON with no extension required.
4. Render it:
   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/render.py <path-to-snapshot.json>
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/render_desk.py <path-to-snapshot.json>
   ```
5. Verify `render.py` exits 0 with every lender rendered and no empty blocks, then show them the `INDEX.md` freshness table.

## Refresh mode: `/policy refresh [lender|all]`

Follow `refresh.md`. Incremental by default: only lenders whose Quickli `policyUpdateDate` is newer than the stored manifest value get re-pulled. Monthly is a sensible cadence, or before a tricky placement.

`render.py` compares block counts against the previous manifest and warns on any lender that loses more than 10% of its blocks. That guard exists because a half-failed pull returns fewer blocks without erroring, which silently shrinks the KB. Take the warning seriously and re-pull that lender.

## Adding primary sources

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ingest_pdf.py <pdf> <slug> "<Name>" "<source>"
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ingest_xlsx.py <workbook> <slug> "<Name>" "<source>"
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/render_primary.py <the JSON either wrote>
```

`ingest_pdf.py` needs PyMuPDF and poppler; the other scripts are stdlib only.

`ingest_xlsx.py` reads cell text **and** the underlying formulas, which is the point — on a servicing calculator the real rule often lives only in a formula, never in a visible label.

If a workbook arrives already filled in for a live deal, use `ingest_xlsx_safe.py` instead. It keeps formulas and whitelisted reference sheets, drops every other typed constant, and prints what it withheld. **A formula cell's cached value is client data**, so a naive "keep the formulas" pass leaks names and loan amounts. Never archive a filled workbook into the KB — archive the blank template with a note.

## Contacts

`desk.md` holds BDM and support contacts, policy source links and SLA document links per lender. Use it for "who do I call at X" and "where's their policy PDF". These are Quickli's records and can be stale or wrong, so confirm before quoting them to anyone.

## Scope

This KB answers **policy**: eligibility, shading, documents, security. It does **not** do servicing maths. Do not compute a borrowing capacity from these files — the numbers that matter live in the lender's own calculator, and a policy summary is the wrong instrument for arithmetic. Answer the policy question and say the number needs the lender's calculator or a dedicated servicing tool.

## Guard rails

- **BID / NCCP:** a policy lookup is research, not a recommendation. If an answer strays into "which lender should we use", add the line that the final recommendation is the broker's after reviewing the client's circumstances.
- **Licensing:** the KB content is Quickli's licensed product, held under the broker's own paid subscription. Never share these files or their content off the machine, never paste them into a web search or a web chatbot, never bundle them into anything passed to another broker. Another broker builds their own from their own login — that is the whole design.
- **No client PII** lives in this KB and none should be added to it.
- **Off-panel lenders** carry no Quickli update or confirmation date, because Quickli only publishes those for lenders on the broker's own panel. `render.py` marks them in `INDEX.md`. Flag them as lower confidence whenever they appear in an answer.
