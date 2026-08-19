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
 *      (Helps, but is no longer required — if the script can't read the topic
 *      list off the page it falls back to a built-in list and carries on.)
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

  // Quickli's topic list as at 17/08/2026. Used only when the live recovery
  // above comes up empty — which happens more than you'd think, because Chrome
  // caps the performance resource buffer and evicts old entries on a busy page.
  // A slightly stale list still pulls everything; a failed run pulls nothing.
  const FALLBACK_TRIGGERS = [
    'acceptable_security_type', 'self_employed_addbacks', 'car_allowance',
    'low_doc', 'boarder_income', 'bonus', 'bridging_loans',
    'buy_now_pay_later', 'cash_out', 'cashback_offers', 'casual',
    'child_maintenance', 'commission', 'common_debt_reducer',
    'company_borrowers', 'company_debt', 'construction_loans',
    'contract_employment', 'credit_impairment', 'credit_scoring', 'dti',
    'dependants', 'essential_overtime', 'essential_services',
    'ethical_lending', 'exit_strategy', 'extended_loan_term',
    'family_employment', 'family_guarantor', 'family_tax_benefit',
    'fastrefi', 'first_home_guarantee', 'fixed_rates', 'foreign',
    'carers_income', 'frequent_bonus_payments', 'fully_maintained_vehicle',
    'genuine_savings', 'social_security', 'hecs', 'rental_holiday',
    'interest', 'investment', 'lmi_waiver_for_professionals', 'lti', 'loc',
    'living_expenses', 'margin_loan', 'max_capacity', 'lvr',
    'maximum_land_size', 'minimum_security_size',
    'net_rental_affordability_scheme', 'nsr', 'negative_gearing', 'nms',
    'non_australian_resident', 'notional_rent', 'novated_lease',
    'overdraft', 'overtime', 'payg', 'parental_leave',
    'parenting_payments', 'pension', 'policy_niches', 'pre_approvals',
    'rental_prestige', 'probation', 'rate_lock_policy',
    'refinance_statement_requirements', 'rental_income', 'rental_reliance',
    'rental_yield', 'smsf_acceptable_contributions', 'smsf_applicant_type',
    'smsf_liquid_asset_position', 'smsf_max_lvr', 'salary_sacrifice',
    'second_job', 'self_employed_income', 'simple_self_employed',
    'streamlined_refinance', 'annuities', 'tax_free', 'vacant_land',
    'verification_of_identity', 'visa_classes'
  ];

  let triggers = recoverTriggers();
  if (triggers) {
    log(`found ${triggers.length} topics from the live page`);
  } else {
    triggers = FALLBACK_TRIGGERS;
    warn(`could not read the topic list off the page, using the built-in list ` +
         `of ${triggers.length} topics (correct as at 17/08/2026). ` +
         `If Quickli has added topics since, they won't be included — ` +
         `everything else pulls normally.`);
  }

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
