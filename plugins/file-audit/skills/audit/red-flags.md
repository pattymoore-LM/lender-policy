# Conduct catalogue — what the statements say about the borrower

Transaction-level scans across every bank, card and loan statement page (skipped in quick mode, and the report banner says so). Each finding: `check` key, severity, evidence quoting date + merchant/description + amount + page, and a credit-officer recommendation. Evidence never includes a TFN or CRN.

Every bank statement gets three questions as a minimum: **are the salary credits real** (staging tells live in `fraud-checks.md` §4, `salary_staging`), **is there gambling**, and **is money going out to liabilities nobody disclosed**. The rest of this catalogue builds on those three.

## `gambling` (medium; high when heavy)

Debits to betting and gaming merchants: Sportsbet, Ladbrokes, TAB, bet365, PointsBet, Betfair, Neds, Unibet, BlueBet, Dabble, TABtouch, keno, casino, "gaming", lotteries when frequent. Report frequency, total for the period and the trend - one lottery ticket is noise, weekly betting is a finding. Recommendation: context from the client; lenders vary widely on tolerance.

## `bnpl` (medium)

Debits to Afterpay, Zip, Klarna, humm, Latitude Pay, PayPal Pay in 4, Openpay. Cross-check against disclosed BNPL statements and the credit report: BNPL activity in the transactions with no disclosure elsewhere is the finding (`undisclosed_liability` applies too).

## `dishonour` (high)

Dishonour fees, "payment reversed - insufficient funds", overdrawn fees, direct debit dishonours. Also flag accounts sitting overdrawn (exclude loan and credit-card accounts where a negative balance is the product).

## `undisclosed_liability` (high)

Regular outgoing payments with no matching liability document and no matching credit-report facility: loan-shaped debits (same amount, same cadence, lender-shaped descriptions), lease payments, SACC/payday lenders (high regardless), child support garnishees. Match credit-report facilities to held statements by last-4 digits then institution name; unmatched facilities on the credit report are the mirror-image finding.

## `large_deposit` (medium)

Single deposits of about $2,000 or more with no evident source (not salary, not transfers between the client's own visible accounts, not Centrelink). Matters for genuine savings and for AML questions the lender will ask. Recommendation: ask for the source; a gift needs a gift letter.

## `liability_implausible` (high) - authenticity-adjacent

Stated repayment implausible against the balance: roughly, monthly repayment below 0.3% of a mortgage balance (e.g. $150 on $473k) or any repayment exceeding the balance. Exclude genuine "extra payment" lines on mortgages. Simple arithmetic, high value.

## `salary_credits_absent` (high)

Payslips on file but no matching salary credits in any held account. Belongs to the fraud pass (`fraud-checks.md` §4) but surfaces here too because the fix is a conduct question: which account does pay actually land in? Request statements for that account.

## Presentation discipline

Group by severity in the report. One flag per pattern, with the instances aggregated in the evidence line ("6 debits totalling $1,150 over the period"), never one flag per transaction. Low-severity observations that resolve themselves (a one-off refund reversal) belong in the document notes, not the flags.
