# CLAUDE.md — Project Context for AI Assistants

This file provides context for AI assistants (Claude, GPT, etc.) working on the compliance-gpt project across multiple conversation sessions.

---

## Project Overview

**compliance-gpt** is an AI-assisted plan document compliance tool that automates the **manual reconciliation bottleneck** for qualified retirement plan conversions and IRS Cycle restatements.

**The Problem We Solve:**
Existing TPA platforms (FIS Relius, ASC, ftwilliam) automate **document generation** but NOT **document comparison**. Compliance teams today perform provision-by-provision reconciliation manually using Word redlines and Excel spreadsheets. This doesn't scale, requires extreme specialized knowledge, and is error-prone under deadline pressure.

**Our Differentiation:**
We are the **only AI tool focused on doc-to-doc comparison** — specifically semantic provision mapping across different vendor document formats (e.g., Relius → ASC).

---

## Repository Structure

```
compliance-gpt/
├── README.md                    # Project overview, status, repo map
├── CLAUDE.md                    # This file - context for AI assistants
├── LICENSE                      # MIT License
│
├── process/                     # The compliance framework (the "spec")
│   ├── README.md               # Index of controls, templates, docs
│   ├── control_001_plan_qualification.md
│   ├── control_002_document_reconciliation.md
│   ├── control_003_exception_handling.md
│   ├── control_004_amendment_and_restated_plan_signoff.md
│   ├── templates/              # CSV/MD templates for artifacts
│   │   ├── plan_comparison_workbook.csv
│   │   ├── exception_log.csv
│   │   └── signoff_checklist.md
│   └── docs/
│       └── references.md       # Regulatory references (IRC, ERISA, Rev. Proc.)
│
├── requirements/                # Software requirements (informed by market research)
│   ├── README.md               # Requirements overview, MVP scope, traceability
│   └── functional_requirements.md  # 62 requirements organized by control
│
└── research/                    # Market research & competitive analysis
    ├── README.md
    └── market_research.pdf     # DeepResearch output on TPA tools, gaps, AI opportunities
```

---

## Project Status

**Phase:** Requirements Complete ✅
**Next:** Technical architecture → Prototype → User testing

**What's Done:**
1. ✅ Process framework defined (`/process`) - Four sequential controls (001-004)
2. ✅ Market research completed (`/research/market_research.pdf`)
3. ✅ Functional requirements drafted (`/requirements/functional_requirements.md`)
4. ✅ Competitive analysis (PlanPort is only AI competitor, does single-doc analysis only)

**What's Next:**
1. ⬜ Technical architecture (LLM strategy, data models, system design)
2. ⬜ Proof-of-concept for REQ-021 (semantic provision mapping)
3. ⬜ User testing with real plan documents
4. ⬜ MVP implementation

---

## Key Design Decisions

### 1. MVP Scope (MVP = Minimum Viable Product)

**In Scope:**
- Batch document ingestion (folder upload, PDF/Word, locked-PDF resilience via OCR/vision)
- **Semantic provision mapping** across vendor documents (core differentiator)
- **AI-powered variance detection** with classification (Administrative/Design/Regulatory)
- **Confidence scoring** (High 90-100%, Medium 70-89%, Low <70%)
- CSV output matching `/process/templates/` schema
- Human-in-loop approval workflow

**Out of Scope (Post-MVP):**
- Integration with TPA platforms (Relius API, ASC DGEM export)
- Real-time collaboration (multi-user editing)
- Automated approval workflows (e-signature integration)
- Amendment language drafting (detection only for MVP)

### 2. Human-in-the-Loop Philosophy

**Never fully autonomous, always reviewed.**
- Inspired by PlanPort's "70-90% of the way there" approach
- AI drafts, human approves
- Graduated confidence thresholds:
  - High (90-100%): Suggest bulk approval option
  - Medium (70-89%): Require individual review
  - Low (<70%): Abstain, mark "Requires Manual Review"

### 3. Locked PDF Handling

**Context:** Market research confirmed locked/encrypted PDFs are a "known issue" in the industry. Providers lock documents to prevent tampering, but this blocks programmatic text extraction.

**Solution:** Fallback strategy
1. Try standard PDF text extraction APIs first
2. If locked/encrypted, fall back to vision-based extraction (OCR or multimodal LLM)
3. Preserve document structure (sections, headers, tables) regardless of method

### 4. Cross-Vendor Semantic Mapping

**Context:** Different document providers (Relius, ASC, ftwilliam, DATAIR) use different templates, section numbering, and phrasing for identical concepts.

**Example from research:**
- Relius: "forfeitures will be used to reduce employer contributions"
- ASC: "the Plan Administrator may apply forfeitures to future contribution obligations"
- **Must be recognized as semantically equivalent**

**Solution:** LLM-powered semantic understanding (not keyword matching or section number alignment)

### 5. Target User: Teams with "Just PDFs and Spreadsheets"

Market research validated this represents the **majority workflow**:
- Smaller TPAs without expensive Relius/ASC subscriptions
- Even teams WITH those tools reconcile manually (tools don't compare across providers)
- Current state: Word redlines, Excel comparison spreadsheets, email chains for approvals

---

## Critical Requirements (MVP Focus)

### REQ-021: Semantic Provision Mapping ⭐ CRITICAL - Core Differentiator
**Why Critical:** This is the #1 manual bottleneck confirmed by market research. No existing tools do this.

**What It Does:**
- Matches provisions semantically using LLM understanding (not just section numbers)
- Handles cross-vendor comparisons (e.g., Relius BPD → ASC prototype)
- Recognizes equivalent provisions despite different wording/placement/formatting
- Assigns confidence score (0-100%) with reasoning
- Flags missing provisions (source → target omissions) as HIGH priority
- Flags new provisions (target additions) as MEDIUM priority

### REQ-022: Variance Detection and Classification
**Why Critical:** Prevents errors like the real-world Relius→ASC example from research where a TPA inadvertently dropped the HCE inclusion in safe harbor contributions (not caught until after year-end).

**What It Does:**
- Detects text differences, missing provisions, new provisions, default value changes
- Proposes classification: Administrative / Design / Regulatory
- Assigns impact level (High/Medium/Low) with justification
- Flags "None" (identical) as low-priority

### REQ-024: Confidence Scoring and Abstention
**Why Critical:** Enables the 70-90% automation target. AI must know when it's uncertain.

**What It Does:**
- Scores each mapping/classification (0-100%)
- Graduated thresholds (90/70/low)
- Displays reasoning with specific evidence
- Tracks accuracy over time (% of high-confidence mappings accepted vs rejected)

### REQ-030: Exception Log Auto-Population
**Why Critical:** Replaces manual Excel spreadsheet tracking (current industry practice).

**What It Does:**
- Auto-creates exception entries from variances (Design/Regulatory/HIGH impact)
- Populates structured fields (ID, description, category, risk, dates, status)
- Exports to CSV matching `/process/templates/exception_log.csv`
- Allows import of existing logs to merge with AI-generated exceptions

---

## Market Research Findings (Key Quotes)

### What's Automated Today:
✅ Document generation (Relius, ASC, ftwilliam) - creating new plan docs from templates
✅ Internal consistency checks - validation logic prevents incompatible elections
✅ Batch operations - mass restatements (ASC: "1,500 plans in a day")
✅ E-signature/distribution - DocuSign integration, client portals

### What's Still Manual (Our Opportunity):
❌ **"True document-to-document reconciliation remains largely manual. It relies on the expertise of compliance professionals to interpret and compare provisions."** — Market Research, p.4

❌ Provision-by-provision reconciliation - "determining how a new document differs from the old (in substance) is manual"

❌ Exception tracking - "Excel spreadsheets or Word tables that get circulated among the conversion team"

❌ Data entry for conversions - "someone re-enters it or maps it field by field"

### Competitive Landscape:
- **PlanPort (2025)** - Only AI competitor. Does single-doc analysis (extraction/summarization), NOT doc-to-doc comparison. Reports "70-90% of the way there" with human review. Positioned as "cyborg" tool.
- **DATAIR** - Limited reconciliation within own ecosystem (doc module ↔ admin module), not cross-provider
- **No other AI-first tools identified**

### Real-World Pain Example:
> "During the recent Cycle 3 restatement, one TPA switched a client's document from a Relius volume submitter to an ASC prototype. A subtle plan provision was inadvertently dropped – Relius had automatically allowed a discretionary safe harbor contribution to include Highly Compensated Employees by default, whereas the new ASC document required checking a box to include HCEs, which the preparer missed. This oversight wasn't caught until after year-end." — Market Research, p.3

**This is the class of error REQ-022 must prevent.**

---

## Regulatory Context (From `/process`)

### The Four Controls:
1. **Control 001: Plan Qualification** - Anchor in IRC §401(a) / ERISA qualification requirements
2. **Control 002: Document Reconciliation** - Provision mapping & variance detection (⭐ MVP FOCUS)
3. **Control 003: Exception Handling** - Variance tracking to closure
4. **Control 004: Amendment & Sign-off** - Final execution, sign-off, archive

### Evidence Produced:
- Qualification Review Memo
- Plan Comparison Workbook (side-by-side provisions)
- Exception Log with approvals
- Executed Restated Plan Package (incl. Opinion Letter)

### Regulatory References:
- **IRC §401(a)** - Qualified plan requirements
- **ERISA §§101–404** - Fiduciary duties, disclosures, record retention
- **Rev. Proc. 2017-41** - Pre-Approved Plan Program (opinion letters, reliance)
- **Rev. Proc. 2021-30** - EPCRS (Employee Plans Correction System)
- **DOL Reg. §2520.104b-1** - Disclosure/recordkeeping requirements

---

## Important Terminology

**Plan Document Components:**
- **BPD** (Basic Plan Document) - IRS pre-approved template with legal language
- **Adoption Agreement** - Employer's elections/choices overlaid on BPD
- **Amendment** - Modifications to plan over time (interim or restated)
- **Opinion Letter** - IRS letter confirming pre-approved document meets §401(a) qualification
- **SPD** (Summary Plan Description) - Participant-facing summary

**Provision Types (for extraction/mapping):**
- Eligibility (age, service requirements)
- Compensation (W-2, 415 safe harbor, etc.)
- Contributions (match, profit-sharing, safe harbor, QACA/EACA)
- Vesting (schedules, cliff, graded)
- Distributions (in-service, hardship, loans)
- Top-Heavy provisions
- Coverage/ADP/ACP testing parameters

**Variance Classification:**
- **Administrative** - Wording/formatting only, no substantive change
- **Design** - Employer election changed (requires sponsor approval)
- **Regulatory** - Required by Cycle/law change (informational, not optional)

**Impact Levels:**
- **High** - Affects participant rights, contribution calculations, or qualification
- **Medium** - Operational impact but correctable via amendment
- **Low** - Administrative clarification or formatting

**TPA** - Third-Party Administrator (firm that handles plan administration, compliance, testing for employers)

**Recordkeeper** - Platform that tracks participant accounts, contributions, investments

**Cycle 3 Restatement** - IRS requires periodic updates to pre-approved plan documents (Cycle 3 is recent/current)

---

## Working with This Project

### For AI Assistants:

**When starting a new conversation:**
1. Read this file first for context
2. Check `/requirements/README.md` for current MVP scope
3. Review `/research/market_research.pdf` findings (summarized above)
4. Reference `/process/control_002_document_reconciliation.md` - this is the core workflow we're automating

**When making changes:**
1. Update this file if design decisions change
2. Keep `/requirements/functional_requirements.md` as source of truth for "what"
3. Don't propose changes to `/process` (that's the regulatory framework, not the software)
4. Always maintain human-in-the-loop philosophy (never fully autonomous)

**When adding requirements:**
1. Use REQ-XXX numbering (next available in range)
2. Map to specific control (001-004) or mark as cross-cutting
3. Include user story, acceptance criteria, and context from market research where applicable
4. Update traceability table in `/requirements/functional_requirements.md`

**When discussing architecture/design:**
1. This is LLM-first by design (semantic understanding is core capability)
2. Consider locked PDF handling (vision fallback required)
3. Target 70-90% automation (inspired by PlanPort benchmark)
4. Output must match `/process/templates/` CSV schema for compatibility

---

## Git Workflow

**Main branch:** `main`
**Commit style:** Descriptive messages with context

**Example commits from this project:**
- `cd76fdb` - "first commit"
- `3c60579` - "Restructure repo as software project with process spec"

**When committing:**
- Use conventional format with context (see existing commits)
- Include `🤖 Generated with [Claude Code](https://claude.com/claude-code)` footer
- Include `Co-Authored-By: Claude <noreply@anthropic.com>` when AI-assisted

---

## Open Questions / Future Decisions

### Technical Architecture (Next Phase):
1. **LLM Strategy:** Which model(s) for semantic mapping? (GPT-4, Claude, open-source?)
2. **Data Models:** How to represent provisions, mappings, variances in structured format?
3. **Storage:** Local-first (MVP) vs cloud? User privacy constraints?
4. **Tech Stack:** Python (likely for LLM integration) vs Node.js vs other?

### User Testing Priorities:
1. **Real documents needed:** Obtain sample Relius, ASC, ftwilliam plan documents for testing
2. **Accuracy baseline:** What % of mappings must be correct for 70-90% target?
3. **Confidence calibration:** Do users trust 90% threshold for bulk approval?

### Post-MVP Integration:
1. **Relius/ASC APIs:** Can we export directly to their platforms?
2. **Workflow tools:** Should we integrate with PensionPro (industry-standard TPA CRM)?
3. **E-signature:** DocuSign vs other providers?

---

## Resources

**Market Research:** `/research/market_research.pdf` (12 pages, sources cited)
**Process Framework:** `/process/README.md` (control flow, templates, references)
**Functional Requirements:** `/requirements/functional_requirements.md` (62 requirements)

**External References:**
- IRC §401(a) - https://www.law.cornell.edu/uscode/text/26/401
- ERISA - https://www.dol.gov/general/topic/retirement/erisa
- Rev. Proc. 2017-41 - https://www.irs.gov/pub/irs-drop/rp-17-41.pdf
- Industry forums - BenefitsLink, ASPPA, NAPA (for practitioner insights)

---

## Project History / Changelog

**2025-10-17** - Initial project setup
- Created `/process` framework (four controls, templates, references)
- Ran DeepResearch on TPA compliance tools landscape
- Drafted functional requirements (62 requirements organized by control)
- Established competitive differentiation (vs Relius/ASC/PlanPort)
- Created CLAUDE.md for cross-session context

**Previous Work:**
- Sergio had explored PDF text extraction issues in earlier project
- Learned some PDFs are locked → required vision-based approach (informed REQ-002)

---

## Contact / Ownership

**Project Owner:** Sergio DuBois (sergio.dubois@gmail.com)
**GitHub:** https://github.com/sentientsergio/compliance-gpt
**License:** MIT

---

*Last Updated: 2025-10-17*
*Next Review: After technical architecture phase*
