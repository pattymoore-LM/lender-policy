/* ---------------------------------------------------------------------------
 * pull-snapshot.js — build your Quickli policy snapshot with no AI tool at all.
 *
 *   >>> THIS GOES IN CHROME, NOT IN TERMINAL. <<<
 *
 * If you paste this into Terminal you will get a `quote>` or `dquote>` prompt
 * that never returns. Press Ctrl+C to get out, then read on.
 *
 * Fastest way to get it into Chrome, from Terminal:
 *     pbcopy < ~/lender-policy/pull-snapshot.js
 * then switch to Chrome and paste into the console (Cmd+Option+J).
 *
 * HOW TO USE
 *   1. Log into Quickli in Chrome and open the Policy Library:
 *        https://app.quickli.com.au/policy
 *   2. Click any lender once, so the page makes its normal policy request.
 *      (This script reads that request to learn the current topic list.)
 *   3. Open DevTools:  Cmd+Option+J  (Mac)  /  Ctrl+Shift+J  (Windows)
 *   4. Paste this entire file into the Console and press Enter.
 *   5. Wait. It prints progress as it goes, then downloads
 *      quickli-policy-snapshot-YYYY-MM-DD.json to your Downloads folder.
 *
 * Then render it:
 *   python3 render.py ~/Downloads/quickli-policy-snapshot-YYYY-MM-DD.json
 *
 * Everything runs inside your own logged-in session, in your own browser.
 * Nothing is uploaded anywhere. The file lands on your machine and stays there.
 *
 * If Chrome says "allow pasting" the first time, type: allow pasting
 * ------------------------------------------------------------------------- */

(async () => {
  const THROTTLE_MS = 150;   // be a polite neighbour; don't hammer the API
  const log = (...a) => console.log('%c[snapshot]', 'color:#0a7', ...a);
  const warn = (...a) => console.warn('[snapshot]', ...a);

  if (!location.hostname.includes('quickli')) {
    console.error('[snapshot] Run this on app.quickli.com.au/policy, not here.');
    return;
  }

  // --- 1. Recover the current topic list from the app's own request ---------
  // The page requests /api/policy?...&triggers=[...] on load. Reading it back
  // from the performance timeline means we always use Quickli's current
  // vocabulary rather than a hardcoded list that goes stale.
  function recoverTriggers() {
    const entries = performance.getEntriesByType('resource')
      .map(e => e.name)
      .filter(n => n.includes('/api/policy') && n.includes('triggers='));
    for (const url of entries.reverse()) {
      try {
        const raw = new URL(url).searchParams.get('triggers');
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed) && parsed.length > 10) return parsed;
      } catch (e) { /* try the next one */ }
    }
    return null;
  }

  const triggers = recoverTriggers();
  if (!triggers) {
    console.error(
      '[snapshot] Could not find the topic list.\n' +
      'Fix: click a lender in the Policy Library so the page loads some policy, ' +
      'then paste this again. Do not reload the page in between.'
    );
    return;
  }
  log(`found ${triggers.length} topics`);

  // --- 2. Lender list + provenance -----------------------------------------
  let provenance;
  try {
    const res = await fetch('/api/lender-info?lenders=All', { credentials: 'include' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    provenance = await res.json();
  } catch (e) {
    console.error('[snapshot] Could not load the lender list:', e.message,
      '\nAre you still logged in? Reload the page, log in, and try again.');
    return;
  }

  const slugs = provenance.map(p => p.lender).filter(Boolean);
  log(`found ${slugs.length} lenders — starting pull, roughly ${Math.ceil(slugs.length * (THROTTLE_MS + 400) / 1000)}s`);

  // --- 3. Pull each lender -------------------------------------------------
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const encode = o => encodeURIComponent(JSON.stringify(o));
  const policyByLender = {};
  const failed = [];

  for (let i = 0; i < slugs.length; i++) {
    const slug = slugs[i];
    try {
      const url = `/api/policy?lenders=${encode([slug])}&triggers=${encode(triggers)}&search=`;
      const res = await fetch(url, { credentials: 'include' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blocks = await res.json();
      if (!Array.isArray(blocks) || blocks.length === 0) {
        failed.push(slug);
        warn(`${slug}: empty (likely off-panel)`);
      } else {
        policyByLender[slug] = blocks;
      }
    } catch (e) {
      failed.push(slug);
      warn(`${slug}: ${e.message}`);
    }
    if ((i + 1) % 10 === 0 || i === slugs.length - 1) {
      log(`${i + 1}/${slugs.length} lenders`);
    }
    await sleep(THROTTLE_MS);
  }

  // --- 4. Assemble and download -------------------------------------------
  const snapshotDate = new Date().toISOString().slice(0, 10);
  const snapshot = {
    snapshotDate,
    source: 'app.quickli.com.au/api/policy + /api/lender-info',
    triggers,
    provenance,
    policyByLender,
  };

  const blocks = Object.values(policyByLender).reduce((n, b) => n + b.length, 0);
  const name = `quickli-policy-snapshot-${snapshotDate}.json`;
  const blob = new Blob([JSON.stringify(snapshot)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 5000);

  log(`DONE — ${Object.keys(policyByLender).length} lenders, ${blocks} policy blocks`);
  log(`downloaded: ${name}`);
  if (failed.length) {
    warn(`${failed.length} returned nothing (normal for lenders off your panel):`, failed.join(', '));
  }
  log('Next:  python3 render.py ~/Downloads/' + name);
})();
