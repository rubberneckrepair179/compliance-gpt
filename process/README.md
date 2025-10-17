# `/process` — Plan Conversion Compliance Controls

This folder defines the **Plan Conversion Compliance Framework**: four sequential, auditable controls.

## Controls

1. **[control_001_plan_qualification.md](./control_001_plan_qualification.md)** — Plan Qualification Framework (regulatory objective & reliance)
2. **[control_002_document_reconciliation.md](./control_002_document_reconciliation.md)** — Provision mapping & variance detection
3. **[control_003_exception_handling.md](./control_003_exception_handling.md)** — Variance tracking to closure
4. **[control_004_amendment_and_restated_plan_signoff.md](./control_004_amendment_and_restated_plan_signoff.md)** — Final execution, sign-off, archive

## Evidence produced

- Qualification Review Memo
- Plan Comparison Workbook
- Exception Log with approvals
- Executed Restated Plan Package (incl. Opinion Letter)

## Control flow

```mermaid
flowchart TD
  A[001: Plan Qualification] --> B[002: Reconciliation]
  B --> C[003: Exceptions]
  C --> D[004: Sign-off]
```
