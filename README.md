# compliance-gpt

Plan Conversion Compliance Framework — controls, artifacts, and templates to preserve **qualified plan** status during a recordkeeper conversion or Cycle restatement.

## Why this exists

When plans move providers or restate onto a new IRS pre-approved document cycle, you must:
- Maintain reliance under **IRC §401(a)** (tax qualification)
- Evidence ERISA / DOL obligations (written plan, records, disclosures)
- Prove the new document **still says what the old plan said** (or that deliberate changes were approved)

This repo provides the **control stack** and **working artifacts** to do that reliably.

## Quick start

1. Read `/process/README.md` for the control flow.
2. Use `/templates/plan_comparison_workbook.csv` to map old→new plan provisions.
3. Track mismatches in `/templates/exception_log.csv`.
4. Complete `/templates/signoff_checklist.md` and compile the Execution Package.

## Repo map

- `/process` — the four controls (001–004) with scope, triggers, activities, and acceptance criteria.
- `/templates` — CSV/MD templates for the comparison workbook, exception log, and sign-off checklist.
- `/docs` — references (IRC / ERISA / Rev. Proc.) and any firm-specific notes.

## Overview (Mermaid)

```mermaid
flowchart TD
  A[Control 001: Plan Qualification] --> B[Control 002: Document Reconciliation]
  B --> C[Control 003: Exception Handling]
  C --> D[Control 004: Amendment & Sign-off]

  subgraph Inputs
    I1[Old Plan Docs (Basic + Adoption + Amendments)]
    I2[Target Cycle 3 Docs (Basic + Blank Adoption)]
    I3[IRS Opinion Letters & Sponsor Data]
  end

  I1 --> B
  I2 --> B
  I3 --> A

  subgraph Evidence
    E1[Qualification Review Memo]
    E2[Comparison Workbook]
    E3[Exception Log & Approvals]
    E4[Executed Plan Package]
  end

  A --> E1
  B --> E2
  C --> E3
  D --> E4
```
