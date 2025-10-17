# Functional Requirements — compliance-gpt MVP

## Overview

compliance-gpt is an **AI-assisted plan document compliance tool** that automates the **manual reconciliation bottleneck** identified in market research: semantic provision mapping, variance detection, and exception tracking during qualified retirement plan conversions and IRS Cycle restatements.

**The Gap We Fill:**
Existing TPA platforms (FIS Relius, ASC, ftwilliam) automate **document generation** but not **document comparison**. Teams today perform provision-by-provision reconciliation manually using Word redlines and Excel spreadsheets. This doesn't scale, requires extreme specialized knowledge, and is error-prone under deadline pressure.

**MVP Scope:**
- Batch document ingestion (PDF upload or folder processing) with locked-PDF resilience
- **Semantic provision mapping** across different vendor document formats (e.g., Relius → ASC)
- **AI-powered variance detection** with classification (Administrative/Design/Regulatory)
- **Confidence scoring** (70-90% automation target, inspired by PlanPort) with human-in-the-loop approval
- Structured output to CSV templates (matching `/process/templates/`)

**Out of Scope (MVP):**
- Integration with existing TPA/compliance platforms (Relius API, ASC DGEM export)
- Real-time collaboration features (multi-user editing)
- Automated approval workflows (email/e-signature integration)
- Amendment language drafting (detection only, not generation)

**Competitive Differentiation:**
| Feature | Existing Tools (Relius/ASC/ftwilliam) | PlanPort (2025 AI tool) | compliance-gpt MVP |
|---------|--------------------------------------|------------------------|-------------------|
| Document generation | ✅ Core capability | ❌ Not applicable | ❌ Out of scope |
| Single-doc analysis | ❌ Manual review | ✅ AI extraction | ✅ AI extraction |
| **Doc-to-doc comparison** | ❌ Manual | ❌ Not offered | ✅ **Core focus** |
| **Cross-vendor mapping** | ❌ Manual | ❌ Single doc only | ✅ **Semantic matching** |
| Variance classification | ❌ Human expert | ❌ Not offered | ✅ AI + human approval |
| Exception tracking | ⚠️ Basic (within-platform) | ❌ Not offered | ✅ Auto-populated CSV |
| Confidence scoring | ❌ Not applicable | ⚠️ Mentioned (70-90%) | ✅ Graduated (90/70/low) |
| Batch processing | ✅ Mass restatements | ❌ Unknown | ✅ Folder upload |
| Locked PDF handling | ⚠️ Assumes editable | ❌ Unknown | ✅ Vision fallback |

**Key Insight:** We are the only tool focused on automating the manual reconciliation workflow that ALL compliance teams perform, regardless of which generation platform they use.

---

## Document Ingestion Requirements

### REQ-001: Document Upload
**User Story:** As a compliance analyst, I need to upload plan documents so the system can analyze them.

**Acceptance Criteria:**
- System SHALL accept individual PDF uploads via web interface
- System SHALL accept batch uploads by pointing to a local folder
- System SHALL support both text-extractable and locked/encrypted PDFs
- System SHALL display upload progress and success/failure status per file

### REQ-002: Document Format Resilience
**User Story:** As a compliance analyst, I need the system to handle various document formats so I'm not blocked by locked PDFs.

**Acceptance Criteria:**
- System SHALL extract text from PDFs using standard APIs when possible
- System SHALL fall back to vision-based extraction (OCR/multimodal LLM) when text extraction fails
- System SHALL accept Word documents (.doc, .docx) as input
- System SHALL accept image files (PNG, JPG) for scanned documents
- System SHALL preserve document structure (sections, headers, tables, footnotes) regardless of extraction method

### REQ-003: Document Type Identification
**User Story:** As a compliance analyst, I need the system to identify document types so provisions are mapped correctly.

**Acceptance Criteria:**
- System SHALL detect document types from content analysis: Basic Plan Document (BPD), Adoption Agreement (AA), Amendment, Opinion Letter, Summary Plan Description
- System SHALL allow user to manually tag/correct document type if auto-detection is uncertain
- System SHALL flag when expected document types are missing (e.g., no Opinion Letter found)

### REQ-004: Intermediate Representation
**User Story:** As a developer/analyst, I need structured data from documents so I can validate and reprocess if needed.

**Acceptance Criteria:**
- System SHALL produce JSON representation of extracted provisions with schema: `{section_id, provision_type, text, source_document, page_number, confidence_score}`
- System SHALL maintain source document lineage for each extracted provision
- System SHALL allow export of intermediate JSON for auditing or reprocessing

---

## Control 001: Plan Qualification

### REQ-010: Opinion Letter Extraction
**User Story:** As a compliance analyst, I need key metadata extracted from Opinion Letters so I can verify reliance.

**Acceptance Criteria:**
- System SHALL extract: Plan Name, Sponsor EIN, Cycle (e.g., "Cycle 3"), Opinion Letter Date, Effective Date(s)
- System SHALL flag if Opinion Letter is missing or expired
- System SHALL display extracted metadata for user confirmation

### REQ-011: Document Lineage Verification
**User Story:** As a compliance analyst, I need to verify the amendment history so I know the plan is current.

**Acceptance Criteria:**
- System SHALL identify all amendments by effective date from document headers/footers
- System SHALL detect gaps in amendment timeline (e.g., missing interim amendments)
- System SHALL flag if source document cycle does not match target cycle expectations

### REQ-012: Qualification Checklist Generation
**User Story:** As a compliance manager, I need a qualification review checklist so I can evidence this control.

**Acceptance Criteria:**
- System SHALL generate a Plan Qualification Review Memo summarizing: Document lineage, Opinion Letter status, Cycle alignment, Identified qualification rules (ADP/ACP, coverage, vesting, distributions)
- System SHALL flag high-risk items (missing Opinion Letter, expired reliance)
- System SHALL export checklist as PDF or Markdown for inclusion in audit package

---

## Control 002: Document Reconciliation

### REQ-020: Provision Extraction
**User Story:** As a compliance analyst, I need provisions extracted from source and target documents so I can compare them.

**Acceptance Criteria:**
- System SHALL extract provisions by type: Eligibility, Compensation, Contributions (match, profit-sharing, safe harbor), Vesting, Distributions, Loans, Hardship, Top-Heavy, Coverage, QACA/EACA
- System SHALL handle multi-part provisions (e.g., eligibility = age + service)
- System SHALL extract provision text with section references (e.g., "Section 2.01")

### REQ-021: Semantic Provision Mapping (CRITICAL - Core Differentiator)
**User Story:** As a compliance analyst, I need the system to match provisions across documents from different vendors so I don't have to manually align 100 sections and interpret different wording.

**Context:** Market research confirms this is the #1 manual bottleneck. Different document providers (Relius, ASC, ftwilliam, DATAIR) use different templates, section numbering, and phrasing for identical concepts. Example: "forfeitures will be used to reduce employer contributions" (Relius) vs "the Plan Administrator may apply forfeitures to future contribution obligations" (ASC) must be recognized as semantically equivalent.

**Acceptance Criteria:**
- System SHALL match provisions **semantically** using LLM understanding (not just section number or keyword matching)
- System SHALL handle cross-vendor document comparisons (e.g., Relius BPD → ASC prototype)
- System SHALL recognize equivalent provisions despite different wording, section placement, or formatting
- System SHALL assign confidence score (0-100%) to each mapping with reasoning (e.g., "High confidence: Both define 21 & 1 year eligibility" vs "Low confidence: Ambiguous section reference")
- System SHALL flag provisions present in source but missing in target (potential omissions)
- System SHALL flag provisions in target that have no source equivalent (new elections or additions)
- System SHALL allow user to approve, reject, or manually override mappings
- System SHALL learn from user corrections to improve future mappings (if feasible in MVP, otherwise post-MVP)

### REQ-022: Variance Detection and Classification
**User Story:** As a compliance analyst, I need variances classified so I know which require sponsor approval vs. regulatory updates.

**Context:** Real-world example from research - A TPA switching from Relius to ASC prototype inadvertently dropped a provision: Relius auto-included HCEs in discretionary safe harbor contributions by default, but ASC required checking a box (which was missed). This wasn't caught until after year-end, causing operational errors. This class of error is what variance detection must prevent.

**Acceptance Criteria:**
- System SHALL detect text differences between matched provisions
- System SHALL detect **missing provisions** (present in source, absent in target) as HIGH priority variance
- System SHALL detect **new provisions** (absent in source, present in target) as MEDIUM priority variance requiring confirmation
- System SHALL detect **default value changes** (e.g., vendor A defaults to X, vendor B defaults to Y) and flag explicitly
- System SHALL propose variance classification:
  - **Administrative** (wording/formatting only, no substantive change)
  - **Design** (employer election changed - requires sponsor approval)
  - **Regulatory** (required by Cycle/law change - informational, not optional)
- System SHALL assign impact level (High/Medium/Low) with justification:
  - High: Affects participant rights, contribution calculations, or qualification
  - Medium: Operational impact but correctable via amendment
  - Low: Administrative clarification or formatting
- System SHALL flag "None" (identical provisions) as low-priority review

### REQ-023: Comparison Workbook Generation
**User Story:** As a compliance analyst, I need a comparison workbook so I can review and share findings with legal/sponsor.

**Acceptance Criteria:**
- System SHALL generate CSV matching `/process/templates/plan_comparison_workbook.csv` schema
- System SHALL populate: Section, Provision Type, Source Text, Target Text, Variance Type, Impact, Owner (blank), Due Date (blank), Notes/Recommended Action, Disposition (default: "Pending"), Evidence Link (blank)
- System SHALL allow export to Excel with formatting (color-coded by variance type)
- System SHALL preserve intermediate JSON for regeneration if needed

### REQ-024: Confidence Scoring and Abstention
**User Story:** As a compliance analyst, I need to know when AI is uncertain so I can prioritize manual review.

**Context:** PlanPort (leading AI competitor) reports getting "70-90% of the way there" with human review for final validation. We adopt a similar graduated confidence model.

**Acceptance Criteria:**
- System SHALL score each mapping and classification with confidence (0-100%)
- System SHALL use graduated confidence thresholds:
  - **High (90-100%)**: Suggest bulk approval option for analyst efficiency
  - **Medium (70-89%)**: Require individual review and explicit approval
  - **Low (<70%)**: Mark "Requires Manual Review" and abstain from proposing classification
- System SHALL prioritize low-confidence items at top of review queue
- System SHALL display reasoning for confidence level with specific evidence:
  - High: "Exact match: Both documents specify '21 years & 12 months service' in eligibility section"
  - Medium: "Semantic match: 'Age 21 + 1 year' maps to '21 & 12 months' with high probability"
  - Low: "Ambiguous: Source mentions 'vesting schedule' but no matching target section found"
- System SHALL track accuracy over time (% of high-confidence mappings accepted vs rejected by users)

---

## Control 003: Exception Handling

### REQ-030: Exception Log Auto-Population
**User Story:** As a compliance analyst, I need exceptions auto-created from variances so I don't manually re-key findings.

**Context:** Market research shows exception tracking today is "Excel spreadsheets or Word tables that get circulated among the conversion team." Firms without specialized software rely on ad-hoc tracking. This requirement replaces manual exception entry.

**Acceptance Criteria:**
- System SHALL create exception log entry for each variance marked "Design" or "Regulatory" (not "Administrative" unless user explicitly flags)
- System SHALL create exception log entry for each HIGH impact variance regardless of classification
- System SHALL populate: ID (auto-increment), Description (variance summary from comparison workbook), Category (from variance type), Risk (H/M/L from variance impact), Owner (blank for user assignment), Opened On (current date), Due Date (blank for user assignment), Status (default: "Open"), Resolution (blank), Evidence Link (blank)
- System SHALL export to CSV matching `/process/templates/exception_log.csv` schema
- System SHALL allow import of existing exception logs (for teams already tracking manually) to merge with AI-generated exceptions

### REQ-031: Exception Tracking
**User Story:** As a compliance manager, I need to track exception status so I know progress to closure.

**Acceptance Criteria:**
- System SHALL allow user to update Status (Open/Pending/Closed), Resolution (Amended/Waived/No Impact), Resolution Date, Reviewer Sign-off
- System SHALL flag overdue exceptions (based on Due Date)
- System SHALL prevent Control 004 (Sign-off) from proceeding if any High-risk exceptions are Open

### REQ-032: Exception Evidence Linking
**User Story:** As a compliance analyst, I need to attach approval evidence so audits are defensible.

**Acceptance Criteria:**
- System SHALL allow file upload (email PDF, e-signature confirmation) per exception
- System SHALL store evidence with immutable timestamp and user attribution
- System SHALL link evidence files in Exception Log "Evidence Link" column

---

## Control 004: Amendment & Sign-off

### REQ-040: Execution Package Compilation
**User Story:** As a compliance manager, I need the execution package assembled so I can route for signatures.

**Acceptance Criteria:**
- System SHALL compile package containing: Final BPD, Final Adoption Agreement, Amendments (if any), Opinion Letter, Comparison Workbook (summary), Exception Log (closed items only)
- System SHALL verify all documents are present (flag if missing)
- System SHALL export as single PDF or ZIP archive

### REQ-041: Pre-Sign-off Validation
**User Story:** As a compliance manager, I need the system to block sign-off if there are open issues so qualification is preserved.

**Acceptance Criteria:**
- System SHALL verify all exceptions are Closed before allowing sign-off
- System SHALL verify no High-risk regulatory exceptions remain Open
- System SHALL verify Opinion Letter is present and valid
- System SHALL display sign-off checklist matching `/process/templates/signoff_checklist.md`

### REQ-042: Compliance Review Memo Generation
**User Story:** As a legal reviewer, I need a summary memo so I can certify the work without re-reading 200 pages.

**Acceptance Criteria:**
- System SHALL generate Compliance Review Memo summarizing: Total provisions reviewed, Variances found (count by type), Exceptions raised and resolved, High-impact changes requiring sponsor attention, Regulatory updates applied
- System SHALL export memo as PDF or Markdown
- System SHALL include AI confidence summary (% auto-mapped vs. manual review)

### REQ-043: Audit Trail and Version Control
**User Story:** As a compliance manager, I need an immutable audit trail so regulators can see the process was followed.

**Acceptance Criteria:**
- System SHALL log all user actions: Document uploads, Mapping approvals/overrides, Variance classifications, Exception status changes, Sign-off completions
- System SHALL timestamp and attribute each action to a user
- System SHALL prevent editing or deletion of audit log
- System SHALL export audit log as CSV or JSON

---

## Output and Export Requirements

### REQ-050: CSV Template Output
**User Story:** As a compliance analyst, I need output in the standard CSV format so it integrates with existing workflows.

**Acceptance Criteria:**
- System SHALL export Plan Comparison Workbook to CSV matching `/process/templates/plan_comparison_workbook.csv` schema
- System SHALL export Exception Log to CSV matching `/process/templates/exception_log.csv` schema
- System SHALL preserve UTF-8 encoding for special characters (section symbols, etc.)

### REQ-051: Human-in-the-Loop Review Interface
**User Story:** As a compliance analyst, I need a review interface so I can approve/reject AI outputs efficiently.

**Acceptance Criteria:**
- System SHALL display side-by-side view of source vs. target provisions
- System SHALL highlight differences with color coding
- System SHALL allow bulk approval of high-confidence mappings (>90%)
- System SHALL require explicit approval for medium-confidence (70-90%) and manual review for low-confidence (<70%)
- System SHALL allow comments/notes per provision for collaboration

---

## Non-Functional Requirements

### REQ-060: Performance
- System SHALL process a typical plan conversion (2 source docs + 2 target docs, ~100 provisions) in under 10 minutes
- System SHALL provide progress indicators during long-running operations

### REQ-061: Security and Privacy
- System SHALL not store plan documents or extracted data outside user's local environment (MVP: local-first architecture)
- System SHALL allow deletion of all project data on user request

### REQ-062: Extensibility
- System SHALL support addition of new provision types without code changes (configuration-driven)
- System SHALL allow customization of confidence thresholds per deployment

---

## Future Enhancements (Post-MVP)

- Integration with TPA platforms (FIS Relius, ASC, etc.) for document import/export
- Real-time collaboration (multiple analysts working on same conversion)
- Automated approval routing (email/e-signature workflow integration)
- AI-generated amendment language drafting (not just detection)
- Historical plan version comparison (multi-cycle analysis)
- Regulatory update alerts (IRS/DOL guidance changes)

---

## Requirements Traceability

| Requirement | Control | Priority | MVP |
|-------------|---------|----------|-----|
| REQ-001 to REQ-004 | Ingestion | High | ✓ |
| REQ-010 to REQ-012 | Control 001 | High | ✓ |
| REQ-020 to REQ-024 | Control 002 | High | ✓ |
| REQ-030 to REQ-032 | Control 003 | Medium | ✓ |
| REQ-040 to REQ-043 | Control 004 | Medium | ✓ |
| REQ-050 to REQ-051 | Output/UI | High | ✓ |
| REQ-060 to REQ-062 | Non-Functional | Medium | ✓ |

---

## Market Research Findings (Resolved)

Based on analysis of existing TPA platforms and workflows (see `/research/market_research.pdf`):

### What's Already Automated by Existing Tools:
- **Document generation** (FIS Relius, ASC DGEM, Wolters Kluwer ftwilliam) - creating new plan docs from IRS-approved templates
- **Internal consistency checks** - validation logic prevents incompatible elections (e.g., Safe Harbor auto-includes required vesting)
- **Batch operations** - mass restatements (ASC: "1,500 plans in a day")
- **Version control** - within single platform (not cross-provider)
- **E-signature/distribution** - DocuSign integration, client portals
- **Project tracking** - workflow tools like PensionPro for status/deadlines

### What Remains Manual (compliance-gpt Opportunity):
- ✅ **Provision-by-provision reconciliation** - "determining how a new document differs from the old (in substance) is manual"
- ✅ **Semantic provision matching** - no tools understand "forfeitures reduce contributions" ≈ "apply forfeitures to future obligations"
- ✅ **Cross-provider comparison** - when converting Relius → ASC, no automatic mapping exists
- ✅ **Variance classification** - human must categorize as Administrative/Design/Regulatory
- ✅ **Exception tracking** - "Excel spreadsheets or Word tables" (not specialized tools)
- ✅ **Data entry for conversions** - "someone re-enters it or maps it field by field"

### Key Industry Quote:
> "True document-to-document reconciliation remains largely manual. It relies on the expertise of compliance professionals to interpret and compare provisions." — Market Research, p.4

### Competitive Landscape:
- **PlanPort (2025)** - First AI tool for plan document analysis (single-doc, not comparison)
  - Uses LLM to extract provisions and flag issues
  - Claims "70-90% of the way there" with human review
  - Positioned as "cyborg" tool (AI assists, human decides)
  - Focus: document interpretation, not doc-to-doc reconciliation
- **DATAIR** - Limited reconciliation within own ecosystem (doc module ↔ admin module)
- **No other AI-first tools identified**

### Target User Validation:
Teams with "just spreadsheets and legacy archives of PDFs" represent the **majority workflow**:
- Smaller TPAs without Relius/ASC subscriptions
- Even teams WITH those tools still reconcile manually (tools don't compare across providers)
- Pain points: "sheer volume," "labor-intensive," "extreme specialized knowledge required"
- Bottleneck: Human review doesn't scale to hundreds of plans under deadline pressure

### Implications for MVP:
1. **Strong differentiation** - Only AI tool focused on doc-to-doc comparison
2. **Validated pain** - Manual reconciliation is universal, even in well-tooled shops
3. **Human-in-loop model validated** - PlanPort's 70-90% + review mirrors our approach
4. **Locked PDF prevalence confirmed** - "known issue" requiring OCR/vision fallback
5. **No provision taxonomy standard** - Each vendor uses different section numbering/wording (strengthens case for semantic matching)
