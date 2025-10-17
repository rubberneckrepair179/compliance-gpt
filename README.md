# compliance-gpt

**AI-assisted plan document compliance** — automate the reconciliation, exception tracking, and sign-off workflows that preserve **qualified plan** status during recordkeeper conversions and Cycle restatements.

## The problem

When retirement plans move providers or restate onto a new IRS pre-approved document cycle, compliance teams must:
- Maintain reliance under **IRC §401(a)** (tax qualification)
- Evidence ERISA / DOL obligations (written plan, records, disclosures)
- Prove the new document **still says what the old plan said** (or that deliberate changes were approved)

Today this is done manually with Word redlines, Excel spreadsheets, and email chains. It's error-prone, slow, and doesn't scale.

## What compliance-gpt does

compliance-gpt automates the four-control framework defined in [`/process`](./process/):

1. **Plan Qualification** — verify document lineage and Opinion Letter reliance
2. **Document Reconciliation** — AI-powered provision mapping and variance detection
3. **Exception Handling** — structured tracking of deviations to closure
4. **Sign-off** — automated execution package assembly and audit trail

## Status

**In development.** The compliance process framework is documented in [`/process`](./process/README.md). Requirements for the software implementation are being finalized in `/requirements`.

## Repo map

- **[`/process`](./process/README.md)** — the four-control compliance framework (the "spec")
- **`/requirements`** — functional and technical requirements for the software (coming soon)

See [`/process/README.md`](./process/README.md) for detailed control flow and documentation.
