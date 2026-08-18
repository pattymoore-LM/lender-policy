# /policy refresh: re-pull the Quickli policy snapshot

Requires the broker logged into Quickli in Chrome. Every call runs inside their own authenticated session; nothing goes to an external service, and no policy content leaves the machine.

`$KB` below means `~/.claude/lender-policy` unless `LENDER_POLICY_KB` is set. `$SCRIPTS` means `${CLAUDE_PLUGIN_ROOT}/scripts`.

## Steps

1. Open a tab on `https://app.quickli.com.au/policy` (any lender). Confirm they are logged in — the page shows the Policy Library, not a login form. If not, stop and say so.

2. **Staleness check. Cheap, always do this first.**
   - In page context: `fetch('/api/lender-info?lenders=All', {credentials:'include'})`.
   - Compare each lender's `policyUpdateDate` against `$KB/_source/<latest date>/manifest.json`.
   - **`policyConfirmedDate` is a decoy.** It moves constantly as Quickli does its rolling confirmations, and tracking it means re-pulling everything every time for no reason. Only `policyUpdateDate` tells you the policy actually changed.
   - Report "N lenders stale: <names>". If zero, and no specific lender or `all` was asked for, stop here. That is the whole point of an incremental refresh.

3. **Pull.**
   - `GET /api/policy?lenders=<urlencoded JSON array of slugs>&triggers=<urlencoded JSON array of trigger keys>&search=`
   - Response: an array of `{lender, triggers, content, lastVerifiedOn}`.
   - **Trigger keys:** read them from the previous snapshot's `triggers` field rather than hardcoding. If Quickli adds topics, recapture the app's own request from `performance.getEntriesByType('resource')` on the policy page — the app sends the full current list on load, so the live page is always the source of truth for the vocabulary.
   - Loop the stale (or requested) lenders in page context with about 150ms between calls, accumulate onto a `window` variable, then Blob-download one JSON named `quickli-policy-snapshot-YYYY-MM-DD.json`.
   - Keep each in-page call short and poll a progress object rather than running one long blocking call — a long call will look hung and is hard to recover from.
   - Snapshot shape: `{snapshotDate, source, triggers, provenance, policyByLender}`, where `provenance` is the `lender-info` subset and `policyByLender` groups the flat response by its `lender` field.
   - **Partial refresh:** merge the new lenders into a copy of the previous snapshot before rendering, so `render.py` always sees the full panel rather than writing a KB containing only the lenders that moved.

   No Chrome extension available? Have them paste `$SCRIPTS/pull-snapshot.js` into Chrome DevTools on the policy page instead. Same output, no extension needed.

4. Move the download to `$KB/_source/<YYYY-MM-DD>/snapshot.json`.

5. **Render:**
   ```
   python3 $SCRIPTS/render.py $KB/_source/<date>/snapshot.json
   python3 $SCRIPTS/render_desk.py $KB/_source/<date>/snapshot.json
   ```

6. **Regression guard. Do not skip.** `render.py` enforces it: every lender rendered, zero empty blocks, exit code 0. On failure the affected lender keeps its previous file and `INDEX.md` flags it, so a bad pull can never quietly overwrite a good KB. The script also compares block counts against the previous manifest and warns on any lender losing more than 10% — worth acting on even when the pull technically succeeded, because that is what a half-failed pull looks like.

7. Report one line: lenders refreshed, total blocks, any flags. Keep the prior `_source/<date>/` directories; they are the history and the regression baseline.
