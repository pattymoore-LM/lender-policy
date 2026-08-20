/* ---------------------------------------------------------------------------
 * pull-and-build.js — your whole Quickli policy library as ONE file, from the
 * browser. No Terminal, no Python, no VS Code, nothing to install.
 *
 *   >>> THIS GOES IN CHROME, NOT IN TERMINAL. <<<
 *
 * WHAT TO DO
 *   1. Log into Quickli in Chrome and open the Policy Library:
 *        https://app.quickli.com.au/policy
 *   2. Press Cmd+Option+J (Mac) or Ctrl+Shift+J (Windows). A panel opens
 *      inside the Chrome window with a > prompt. That is the console.
 *   3. Paste this whole file in there and press Enter.
 *      (If Chrome refuses, type:  allow pasting  then paste again.)
 *   4. Wait a minute. It downloads ONE file:
 *        lender-policy-YYYY-MM-DD.md
 *
 * THEN, to ask it questions in plain English:
 *   - Claude: claude.ai > Projects > new project > add that file to the
 *     project knowledge > ask away.
 *   - ChatGPT: chatgpt.com > Projects > new project > upload the file > ask away.
 *   Either works on your phone too.
 *
 * Everything runs inside your own logged-in Quickli session, in your own
 * browser. The file lands in your Downloads and goes nowhere you don't put it.
 *
 * Re-run it monthly. Lender policy moves, and a stale answer is worse than none.
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
  // Failures here get told apart deliberately. "Are you logged in?" is the right
  // advice for a 401 and completely misleading for a 404 — and a 404 is what a
  // broker sees on the day Quickli renames an endpoint, which is not something
  // they can fix by logging in again.
  const SUPPORT = 'the repo issues page: github.com/pattymoore-LM/lender-policy/issues';
  let provenance;
  try {
    const res = await fetch('/api/lender-info?lenders=All', { credentials: 'include' });
    if (res.status === 401 || res.status === 403) {
      console.error(`[snapshot] Quickli says you're not signed in (HTTP ${res.status}).\n` +
        'Log into Quickli in this tab, then paste this again.');
      return;
    }
    if (res.status === 404) {
      console.error('[snapshot] Quickli has moved or renamed this endpoint (HTTP 404).\n' +
        'Nothing you did — the script needs updating. Please report it at ' + SUPPORT);
      return;
    }
    if (!res.ok) {
      console.error(`[snapshot] Quickli returned HTTP ${res.status}.\n` +
        'If it keeps happening, report it at ' + SUPPORT);
      return;
    }
    provenance = await res.json();
  } catch (e) {
    console.error('[snapshot] Could not reach Quickli:', e.message,
      '\nCheck your connection, make sure this tab is on app.quickli.com.au, and try again.');
    return;
  }

  // Validate the shape, not just the status. A 200 carrying a restructured
  // response is the quiet version of the same failure.
  if (!Array.isArray(provenance) || !provenance.length ||
      typeof provenance[0] !== 'object' || !('lender' in provenance[0])) {
    console.error('[snapshot] Quickli responded, but not in the shape this script expects.\n' +
      'That means their API has changed. Nothing you did — please report it at ' + SUPPORT +
      '\nWhat came back:', provenance);
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

  // --- 4. Render to one markdown file --------------------------------------
  // Same output shape as render.py, built here so nobody needs Python.
  const snapDate = new Date().toISOString().slice(0, 10);

  const TOPIC_NAMES = {
    "acceptable_security_type": "Acceptable Security Type",
    "annuities": "Annuities", "boarder_income": "Boarder Income",
    "bonus": "Bonus Income", "bridging_loans": "Bridging Loans",
    "buy_now_pay_later": "Buy Now Pay Later (BNPL)",
    "car_allowance": "Car Allowance", "carers_income": "Carer's Income",
    "cash_out": "Cash Out", "cashback_offers": "Cashback Offers",
    "casual": "Casual Income", "child_maintenance": "Child Maintenance",
    "commission": "Commission Income",
    "common_debt_reducer": "Common Debt Reducer",
    "company_borrowers": "Company Borrowers", "company_debt": "Company Debt",
    "construction_loans": "Construction Loans",
    "contract_employment": "Contract Employment",
    "credit_impairment": "Credit Impairment",
    "credit_scoring": "Credit Scoring", "dependants": "Dependants",
    "dti": "DTI (Debt-to-Income)",
    "essential_overtime": "Essential Services Overtime",
    "essential_services": "Essential Services Workers",
    "ethical_lending": "Ethical Lending", "exit_strategy": "Exit Strategy",
    "extended_loan_term": "Extended Loan Term",
    "family_employment": "Family Employment",
    "family_guarantor": "Family Guarantor",
    "family_tax_benefit": "Family Tax Benefit", "fastrefi": "FastRefi",
    "first_home_guarantee": "First Home Guarantee (FHBG)",
    "fixed_rates": "Fixed Rates", "foreign": "Foreign Income",
    "frequent_bonus_payments": "Frequent Bonus Payments",
    "fully_maintained_vehicle": "Fully Maintained Vehicle",
    "genuine_savings": "Genuine Savings", "gifted_funds": "Gifted Funds",
    "hecs": "HECS / HELP Debt", "interest": "Interest Income",
    "investment": "Investment Income",
    "living_expenses": "Living Expenses (HEM)",
    "lmi_waiver_for_professionals": "LMI Waiver for Professionals",
    "loc": "Line of Credit", "low_doc": "Low Doc / Alt Doc",
    "lti": "LTI (Loan-to-Income)", "lvr": "LVR Limits",
    "margin_loan": "Margin Loans",
    "max_capacity": "Maximum Borrowing Capacity",
    "maximum_land_size": "Maximum Land Size",
    "minimum_security_size": "Minimum Security Size",
    "negative_gearing": "Negative Gearing",
    "net_rental_affordability_scheme": "NRAS",
    "nms": "NMS (Net Monthly Surplus)",
    "non_australian_resident": "Non-Australian Residents",
    "notional_rent": "Notional Rent", "novated_lease": "Novated Lease",
    "nsr": "NSR (Net Service Ratio)", "overdraft": "Overdrafts",
    "overtime": "Overtime Income", "parental_leave": "Parental Leave",
    "parenting_payments": "Parenting Payments", "payg": "PAYG Income",
    "pension": "Pension Income", "policy_niches": "Policy Niches",
    "pre_approvals": "Pre-Approvals", "probation": "Probation",
    "rate_lock_policy": "Rate Lock",
    "refinance_statement_requirements": "Refinance Statement Requirements",
    "rental_holiday": "Holiday / Short-Stay Rental",
    "rental_income": "Rental Income",
    "rental_prestige": "Prestige Property Rental",
    "rental_reliance": "Rental Reliance", "rental_yield": "Rental Yield Caps",
    "salary_sacrifice": "Salary Sacrifice", "second_job": "Second Job",
    "self_employed_addbacks": "Self-Employed Add-backs",
    "self_employed_income": "Self-Employed Income",
    "simple_self_employed": "Simple Self-Employed / Fast-Track",
    "slas": "SLAs / Turnaround",
    "smsf_acceptable_contributions": "SMSF Acceptable Contributions",
    "smsf_applicant_type": "SMSF Applicant Type",
    "smsf_liquid_asset_position": "SMSF Liquid Asset Position",
    "smsf_max_lvr": "SMSF Maximum LVR",
    "social_security": "Social Security Income",
    "streamlined_refinance": "Streamlined Refinance",
    "tax_free": "Tax-Free Income", "vacant_land": "Vacant Land",
    "verification_of_identity": "Verification of Identity (VOI)",
    "visa_classes": "Visa Classes"
  };
  
  const LENDER_NAMES = {
    "_86400": "86 400", "adelaide": "Adelaide Bank",
    "advantedge": "Advantedge", "amp": "AMP", "anz": "ANZ", "apollo": "Apollo",
    "assetline": "Assetline", "auswide": "Auswide Bank",
    "bankaustralia": "Bank Australia", "bankofsydney": "Bank of Sydney",
    "bankwest": "Bankwest", "bendigo": "Bendigo Bank", "beyond": "Beyond Bank",
    "bluestone": "Bluestone", "brighten": "Brighten", "cba": "CBA",
    "firstmac": "Firstmac", "granite": "Granite Home Loans",
    "gsb": "Great Southern Bank", "heritage": "Heritage Bank", "ing": "ING",
    "latrobe": "La Trobe Financial", "liberty": "Liberty",
    "macquarie": "Macquarie", "mamoney": "MA Money",
    "mcf": "Mortgage Choice Freedom", "mebank": "ME Bank", "mezy": "Mezy",
    "mystate": "MyState", "nab": "NAB", "newcastleperm": "Newcastle Permanent",
    "orde": "ORDE", "ownhome": "OwnHome", "peopleschoice": "People's Choice",
    "pepper": "Pepper Money", "redzed": "RedZed", "resimac": "Resimac",
    "skip": "Skip", "stgeorge": "St George", "suncorp": "Suncorp",
    "teachersmutual": "Teachers Mutual", "thinktank": "Thinktank",
    "virgin": "Virgin Money", "vmg": "VMG", "wavemoney": "WaveMoney",
    "westpac": "Westpac", "zeus": "Zeus Mortgages"
  };

  const topicName = k => TOPIC_NAMES[k] ||
    k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  const lenderName = s => LENDER_NAMES[s] ||
    s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

  const auDate = iso => {
    if (!iso) return 'unknown';
    const d = new Date(iso);
    if (isNaN(d)) return iso;
    const p = n => String(n).padStart(2, '0');
    return `${p(d.getDate())}/${p(d.getMonth() + 1)}/${d.getFullYear()}`;
  };

  // Cosmetic only: drop Quickli's &nbsp; spacer lines, demote any headings that
  // live inside Quickli's own content, collapse runs of blanks. Policy wording
  // is never touched.
  //
  // The demotion matters. We use ## for the lender and ### for the topic, and
  // Quickli's policy text carries its own headings ("Acceptable Evidence",
  // "Calculation:"). Left alone, a ## in the content is indistinguishable from
  // a lender heading, and anything scanning by heading level reads it as a new
  // lender. Push them below ours and the structure stays unambiguous.
  const clean = t => (t || '')
    .replace(/^\s*&nbsp;\s*$/gm, '')
    .replace(/^(#{1,6})(\s)/gm, (m, h, s) => '#'.repeat(Math.min(h.length + 3, 6)) + s)
    .replace(/\n{3,}/g, '\n\n')
    .trim();

  const provBySlug = {};
  provenance.forEach(p => { provBySlug[p.lender] = p; });

  const out = [
    '# Lender policy library',
    '',
    `Snapshot taken ${auDate(snapDate)} from your own Quickli subscription.`,
    '',
    'HOW TO USE THIS FILE. Every lender below uses the same `###` topic headings,',
    'so one topic across all lenders is a like-for-like comparison. When you answer',
    'a question from it: quote the policy line word for word rather than',
    'paraphrasing it, say so plainly when a lender has no entry for a topic rather',
    'than guessing (each lender lists what it has no entry for), and finish with the',
    "snapshot date above plus \"confirm live in Quickli before advice\".",
    '',
    'This is research, not advice. Quickli live is the authority, lender policy',
    'moves, and the recommendation belongs to the broker after looking at the',
    'client. It does not answer servicing maths — those numbers live in the',
    "lender's own calculator.",
    '',
    'Quickli licensed content, held under your own subscription. Keep it to',
    'yourself; another broker builds their own from their own login.',
    '',
    '---',
    '',
  ];

  const renderedSlugs = Object.keys(policyByLender).sort(
    (a, b) => lenderName(a).toLowerCase().localeCompare(lenderName(b).toLowerCase()));

  // Contents, so a retrieval pass can see the whole panel at a glance
  out.push('## Lenders in this file', '');
  renderedSlugs.forEach(s => {
    const pr = provBySlug[s] || {};
    out.push(`- ${lenderName(s)} — policy last updated ${auDate(pr.policyUpdateDate)}`);
  });
  out.push('', '---', '');

  let blockCount = 0;
  for (const slug of renderedSlugs) {
    const blocks = policyByLender[slug];
    const pr = provBySlug[slug] || {};
    out.push(`## ${lenderName(slug)}`, '');
    out.push(`*Policy last updated ${auDate(pr.policyUpdateDate)}. ` +
             `Quickli last confirmed ${auDate(pr.policyConfirmedDate)}.*`, '');

    const byTopic = {};
    blocks.forEach(b => (b.triggers || []).forEach(t => {
      (byTopic[t] = byTopic[t] || []).push(b);
    }));

    for (const t of triggers) {
      if (!byTopic[t]) continue;
      out.push(`### ${topicName(t)}`, '');
      for (const b of byTopic[t]) {
        const extra = (b.triggers || []).filter(x => x !== t);
        if (extra.length) {
          out.push(`*Also covers: ${extra.map(topicName).join(', ')}*`, '');
        }
        out.push(clean(b.content), '');
        blockCount++;
      }
    }

    // Absence stated out loud, so "no entry" is an available answer and a
    // guess never has to fill the gap.
    const missing = triggers.filter(t => !byTopic[t]).map(topicName);
    if (missing.length) {
      out.push('### No Quickli entry for', '', missing.join(', ') + '.', '');
    }
    out.push('---', '');
  }

  // --- 5. Download ----------------------------------------------------------
  const name = `lender-policy-${snapDate}.md`;
  const md = out.join('\n');
  const blob = new Blob([md], { type: 'text/markdown' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 5000);

  log(`DONE — ${renderedSlugs.length} lenders, ${blockCount} policy blocks, ` +
      `${(md.length / 1024 / 1024).toFixed(2)} MB`);
  log(`downloaded: ${name}`);
  if (failed.length) {
    warn(`${failed.length} returned nothing (normal for lenders off your panel):`,
         failed.join(', '));
  }
  log('Next: add that file to a Claude or ChatGPT Project, then ask it questions.');
})();
