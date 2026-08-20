# Australian ID reading rules — read the card the way it is actually printed

Misreading an ID creates false name/DOB mismatches, which are high-severity flags. These rules prevent the classic misreads.

## Driver licences (state layouts differ)

- **QLD is the only state that prints the SURNAME first.** "CITIZEN ALEX JAY" on a QLD licence is Alex Jay Citizen. Every other state prints given names first. Reorder before matching.
- **QLD "Effective" date is NOT the date of birth** and not the issue date of the person - it is the card's current-period start. Take DOB only from the field labelled DOB/Date of Birth.
- Orientation is a state cue: QLD and VIC cards are landscape; NSW, SA, WA, TAS, NT, ACT are portrait; NT places the photo on the left.
- Licence number formats vary by state (6-9 digits) and the label varies (Licence No. / LIC NO. / DRIVER LICENCE NUMBER / Licence No. / CRN).
- **The back of a licence carries an address, not a person.** Never treat a licence back as a separate ID or attach a suburb as a name; pair it with its front (card number matches).
- Expiry drives currency. Also sanity-check the DOB: a "DOB" after ~2010 on an adult's licence is a misread of another date.

## Passports

- Shows **given names only** in the name field order given-then-surname; take the first given name for matching, keep the rest as alias tokens.
- AU passport numbers: 1-2 letters + 7-8 digits; NZ: 2 letters + 6 digits.
- The MRZ (two machine lines at the bottom) is authoritative: if the MRZ and the printed zone disagree on name, number, DOB or expiry, that is an authenticity flag on the document itself, not a transcription choice.
- No address on a passport - it never satisfies the address-bearing-ID requirement.

## Medicare cards

- Name lines read `IRN GIVEN-NAME [INITIAL] SURNAME`; the middle name is an initial only. IRN 1 is the primary holder; all listed people count for the household reconcile.
- **No DOB on a Medicare card** - never use one as DOB evidence or in DOB consistency checks.
- No address either. Valid-to date drives currency.

## Matching discipline

- 2 valid IDs from {passport, licence, Medicare} satisfy the LM identification count; never chase a third once two are valid.
- At least one held ID must show the current residential address - in practice that is the licence. Passport + Medicare alone leaves an address gap: raise it as an action, not a "missing".
- Change-of-name (maiden name on one document): the checklist's marriage-certificate / statutory-declaration items exist for exactly this; link the documents rather than flagging a mismatch.
- All name matching goes through the Step 5 ambiguity gate. Couples sharing a surname are the danger case: initials and given names decide, and an ambiguous read is HELD as possible wrong-person, never guessed.
