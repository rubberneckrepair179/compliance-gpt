# `/requirements` — compliance-gpt Software Requirements

This folder defines the **functional and technical requirements** for the compliance-gpt MVP, informed by market research and the process framework defined in `/process`.

## Contents

- **[functional_requirements.md](./functional_requirements.md)** — Complete functional requirements organized by control (001-004)

## Purpose

These requirements translate the **manual compliance process** (defined in `/process`) into **software specifications** for an AI-assisted automation tool.

## Key Findings from Market Research

**What we learned** (see `/research/market_research.pdf`):
- Existing TPA platforms (FIS Relius, ASC, Wolters Kluwer ftwilliam) automate **document generation** but NOT **document comparison**
- "True document-to-document reconciliation remains largely manual" — relies on human expertise
- Exception tracking is "Excel spreadsheets or Word tables" — no specialized tools
- Only one AI competitor (PlanPort, 2025) does single-document analysis, not doc-to-doc comparison
- Pain points: sheer volume, labor-intensive, requires "extreme specialized knowledge"

**Our differentiation:**
- **Only AI tool focused on doc-to-doc comparison** (the #1 manual bottleneck)
- **Cross-vendor semantic mapping** (e.g., Relius → ASC with different templates)
- **Variance classification + exception tracking** (replaces manual spreadsheets)
- **Confidence scoring** (70-90% automation target, human-in-loop for validation)

## Requirements Organization

Requirements are organized by the four controls from `/process`:

1. **Control 001: Plan Qualification** (REQ-010 to REQ-012)
   - Opinion Letter extraction
   - Document lineage verification
   - Qualification checklist generation

2. **Control 002: Document Reconciliation** (REQ-020 to REQ-024) ⭐ **CORE MVP**
   - Provision extraction
   - **Semantic provision mapping** (critical differentiator)
   - **Variance detection and classification** (prevents errors like the Relius→ASC HCE example)
   - Comparison workbook generation
   - Confidence scoring with graduated thresholds (90/70/low)

3. **Control 003: Exception Handling** (REQ-030 to REQ-032)
   - Exception log auto-population from variances
   - Exception tracking and status management
   - Evidence linking

4. **Control 004: Sign-off** (REQ-040 to REQ-043)
   - Execution package compilation
   - Pre-sign-off validation
   - Compliance review memo generation
   - Audit trail

**Cross-cutting requirements:**
- **Document Ingestion** (REQ-001 to REQ-004) - PDF/Word upload, locked-PDF resilience, batch processing
- **Output & Export** (REQ-050 to REQ-051) - CSV templates, human-in-loop review interface
- **Non-Functional** (REQ-060 to REQ-062) - Performance, security, extensibility

## MVP Scope

**In Scope:**
- Batch document ingestion (folder upload, locked-PDF fallback)
- Semantic provision mapping across vendor documents
- AI-powered variance detection with classification (Admin/Design/Regulatory)
- Confidence scoring (High 90-100%, Medium 70-89%, Low <70%)
- CSV output matching `/process/templates/` schema
- Human-in-loop approval workflow

**Out of Scope (Post-MVP):**
- Integration with TPA platforms (Relius API, ASC DGEM)
- Real-time collaboration (multi-user editing)
- Automated approval workflows (e-signature integration)
- Amendment language drafting (detection only for MVP)

## Traceability

Each requirement maps to:
- A specific **control** in `/process`
- A **user story** defining the need
- **Acceptance criteria** for validation
- **Context** from market research (where applicable)

## Next Steps

1. ✅ **Market research complete** — Gap analysis confirms strong differentiation
2. ✅ **Functional requirements drafted** — Control-by-control specifications
3. ⬜ **Technical architecture** — System design, LLM strategy, data models
4. ⬜ **Prototype** — Proof-of-concept for semantic mapping (REQ-021)
5. ⬜ **User testing** — Validate 70-90% automation target with real plan documents
