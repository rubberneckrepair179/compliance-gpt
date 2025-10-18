# System Architecture

## Overview

compliance-gpt is an **LLM-first, local-first desktop application** that automates provision-by-provision reconciliation of qualified retirement plan documents. The system ingests plan documents (PDFs/Word), extracts provisions using AI, performs semantic cross-vendor mapping, detects variances, and outputs structured comparison data for human review and approval.

**Core Design Constraint:** All processing happens locally. No plan documents or extracted data leave the user's machine (REQ-061).

---

## Requirements Addressed

- **REQ-001 to REQ-004:** Document ingestion (upload, format resilience, type identification)
- **REQ-020 to REQ-024:** Document reconciliation (provision extraction, semantic mapping, variance detection, confidence scoring)
- **REQ-050 to REQ-051:** Output (CSV export, human-in-loop review interface)
- **REQ-060:** Performance (process typical conversion in <10 minutes)
- **REQ-061:** Security & privacy (local-first, no cloud storage)

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USER INTERFACE                             │
│  (Review Interface, Document Upload, Bulk Approval, Export)         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATION LAYER                            │
│  (Workflow Management, Progress Tracking, State Management)         │
└──┬──────────────┬──────────────┬──────────────┬────────────────────┘
   │              │              │              │
   ▼              ▼              ▼              ▼
┌─────────┐  ┌─────────┐  ┌──────────┐  ┌──────────────┐
│INGESTION│  │EXTRACTION│  │RECONCIL- │  │  OUTPUT      │
│ MODULE  │  │  MODULE  │  │ IATION   │  │  MODULE      │
│         │  │          │  │  MODULE  │  │              │
└────┬────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘
     │            │             │               │
     │            │             │               │
     ▼            ▼             ▼               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          LLM SERVICE LAYER                          │
│  (Model Selection, Prompt Management, Context Chunking, Retries)   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │  LLM Provider  │
                    │ (Claude/GPT-5) │
                    └────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                       PERSISTENCE LAYER                             │
│  (Local File Storage: JSON, CSV, PDFs, Audit Logs)                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Responsibilities

### 1. User Interface (UI Layer)
**Purpose:** Human interaction, review workflow, export

**Key Features:**
- Document upload (individual files or folder selection)
- Progress indicators during processing
- Side-by-side provision comparison view
- Bulk approval for high-confidence mappings (≥90%)
- Individual review for medium-confidence (70-89%)
- CSV export and execution package generation

**Technology Considerations (TBD in Phase 3):**
- Web-based (Electron for desktop packaging?)
- Native desktop (Qt, Tkinter?)
- CLI-first with optional web UI?

**Dependencies:**
- Orchestration Layer (for workflow state)
- Output Module (for CSV generation)

---

### 2. Orchestration Layer
**Purpose:** Workflow coordination, state management, progress tracking

**Responsibilities:**
- **Workflow state machine:** Track progress through Controls 001-004
- **Task queue:** Manage asynchronous LLM calls (parallel provision extraction)
- **Progress tracking:** Real-time updates for UI (REQ-060: <10 min processing)
- **Error handling:** Retry logic, fallback strategies (e.g., vision fallback for locked PDFs)
- **Session management:** Save/restore work-in-progress (user can pause and resume)

**Key State Transitions:**
```
Document Upload → Document Classification → Provision Extraction →
Semantic Mapping → Variance Detection → Human Review →
Exception Generation → CSV Export → Sign-off Package
```

**Dependencies:**
- All modules (coordinates their execution)
- Persistence Layer (saves state)

---

### 3. Ingestion Module
**Purpose:** Load and prepare documents for analysis

**Sub-Components:**

#### 3.1 PDF Processing
- **Text extraction:** Standard PDF libraries (PyPDF2, pdfplumber, PyMuPDF)
- **Vision fallback:** When locked/encrypted, use multimodal LLM (Claude Sonnet 4.5 with vision)
- **Structure preservation:** Detect sections, headers, tables, footnotes
- **Output:** Raw text + metadata (page numbers, section hierarchy)

#### 3.2 Document Classification
- **LLM-based type detection:** Analyze first 2-3 pages to classify as BPD, Adoption Agreement, Amendment, Opinion Letter, SPD
- **Confidence scoring:** Allow user override if uncertain
- **Vendor detection:** Identify document source (Relius, ASC, ftwilliam, DATAIR) from headers/footers

#### 3.3 Batch Processing
- **Folder scanning:** Process all PDFs in directory
- **Parallel upload:** Multi-threaded file reading
- **Progress tracking:** Per-file status (uploaded, processing, completed, failed)

**Dependencies:**
- LLM Service Layer (for classification and vision fallback)
- Persistence Layer (stores raw documents and extracted text)

---

### 4. Extraction Module
**Purpose:** Parse structured data from document text

**Sub-Components:**

#### 4.1 Provision Extraction (REQ-020)
- **LLM-powered parsing:** Use structured prompts to extract provisions by type
  - Eligibility (age, service)
  - Compensation definitions
  - Contribution formulas (match, profit-sharing, safe harbor)
  - Vesting schedules
  - Distribution rules
  - Loans, hardship, top-heavy provisions
- **Schema:** Output JSON matching `provision_model.md` (see data models)
- **Section linking:** Preserve source document section numbers and page references

#### 4.2 Metadata Extraction (REQ-010)
- **Opinion Letter parsing:** Extract Plan Name, EIN, Cycle, Opinion Date, Effective Date
- **Amendment history:** Identify amendment dates from headers/footers
- **Sponsor details:** Company name, plan year, plan type (401k, profit-sharing, etc.)

**Dependencies:**
- Ingestion Module (receives document text)
- LLM Service Layer (for extraction prompts)
- Data Models (provision schema)

---

### 5. Reconciliation Module (CORE - Control 002)
**Purpose:** Compare source and target documents, detect variances

**Sub-Components:**

#### 5.1 Semantic Mapping (REQ-021) ⭐ CRITICAL
- **Cross-vendor provision matching:** Map source provisions to target provisions using LLM semantic understanding
- **Handles different wording:** "forfeitures reduce contributions" ≈ "apply forfeitures to future obligations"
- **Handles different section numbering:** Relius "Section 4.03" ≈ ASC "Article VI, Part B"
- **Missing provision detection:** Flag provisions in source not found in target (HIGH priority)
- **New provision detection:** Flag provisions in target with no source match (MEDIUM priority)
- **Confidence scoring:** 0-100% with reasoning (see `confidence_scoring.md`)

**Key Algorithm (high-level):**
```
For each source provision:
  1. Extract semantic features (LLM embedding or structured summary)
  2. Compare against all target provisions
  3. Rank by semantic similarity
  4. Select best match if confidence ≥ threshold
  5. If no match ≥ threshold, flag as "missing"
  6. Store mapping with confidence score + reasoning
```

#### 5.2 Variance Detection (REQ-022)
- **Text diff:** For matched provisions, detect textual differences
- **Classification:** Propose Administrative / Design / Regulatory
- **Impact scoring:** High / Medium / Low based on:
  - Affects participant rights? (High)
  - Changes contribution calculations? (High)
  - Operational impact but correctable? (Medium)
  - Formatting/wording only? (Low)
- **Default value detection:** Flag when vendors use different defaults (e.g., HCE inclusion in safe harbor)

#### 5.3 Confidence Scoring (REQ-024)
- **Graduated thresholds:**
  - High (90-100%): Suggest bulk approval
  - Medium (70-89%): Require individual review
  - Low (<70%): Mark "Requires Manual Review," abstain from classification
- **Reasoning display:** Show evidence for confidence level
  - High: "Exact match - both specify '21 years & 12 months service'"
  - Medium: "Semantic match - '21 & 1 year' maps to '21 years & 12 months' with high probability"
  - Low: "Ambiguous - source mentions 'vesting schedule' but no clear target match"
- **Accuracy tracking:** Log user approvals/rejections to measure calibration

**Dependencies:**
- Extraction Module (receives provision data)
- LLM Service Layer (for semantic comparison)
- Data Models (mapping schema, variance schema)

---

### 6. Exception Management Module (Control 003)
**Purpose:** Auto-generate and track exceptions from variances

**Sub-Components:**

#### 6.1 Exception Generation (REQ-030)
- **Auto-population:** Create exception entry for:
  - Variances classified as "Design" or "Regulatory"
  - HIGH impact variances regardless of classification
- **Schema:** Populate exception log fields (ID, Description, Category, Risk, Dates, Status)
- **Import existing logs:** Merge with user's manual tracking spreadsheets

#### 6.2 Tracking Workflow (REQ-031)
- **Status management:** Open → Pending → Closed
- **Resolution tracking:** Amended / Waived / No Impact
- **Evidence linking:** Attach approval emails, e-signature confirmations
- **Pre-sign-off validation:** Block Control 004 if High-risk exceptions remain Open

**Dependencies:**
- Reconciliation Module (variance data)
- Output Module (CSV export)
- Persistence Layer (stores exceptions and evidence files)

---

### 7. Output Module
**Purpose:** Generate exports and compilation packages

**Sub-Components:**

#### 7.1 CSV Export (REQ-050)
- **Plan Comparison Workbook:** Side-by-side source/target with variances
  - Schema: `/process/templates/plan_comparison_workbook.csv`
- **Exception Log:** Structured exception tracking
  - Schema: `/process/templates/exception_log.csv`
- **Qualification Review Memo:** Summary of Control 001 findings
- **UTF-8 encoding:** Preserve special characters (§, ©, etc.)

#### 7.2 Execution Package (REQ-040)
- **Compile final package:** BPD, Adoption Agreement, Amendments, Opinion Letter, Comparison Workbook, Exception Log
- **Export formats:** Single PDF (merged) or ZIP archive
- **Sign-off checklist:** Generate from template (`/process/templates/signoff_checklist.md`)

**Dependencies:**
- All upstream modules (for data)
- Persistence Layer (reads intermediate JSON)

---

### 8. LLM Service Layer
**Purpose:** Centralized interface to LLM providers

**Responsibilities:**
- **Model selection:** Route tasks to appropriate model (e.g., Claude for semantic reasoning, GPT-5 for extraction)
- **Prompt management:** Centralized prompt templates with versioning
- **Context chunking:** Split long documents to fit context windows (see `llm_strategy/context_management.md`)
- **Retry logic:** Handle rate limits, transient errors
- **Cost tracking:** Log token usage per operation (for optimization)
- **Confidence extraction:** Parse LLM outputs to extract numeric confidence scores

**Key Design Decision (TBD in Phase 2):**
- Single model (Claude OR GPT-5) vs. hybrid (different models for different tasks)?
- API-based (cloud) vs. local inference (privacy but requires GPU)?

**Dependencies:**
- External: LLM provider APIs (Anthropic, OpenAI, or local model server)

---

### 9. Persistence Layer
**Purpose:** Local storage of all data

**Storage Schema:**
```
project_directory/
├── documents/
│   ├── source/               # Uploaded source documents (PDFs)
│   └── target/               # Uploaded target documents (PDFs)
│
├── extracted/
│   ├── source_provisions.json    # Structured provision data
│   ├── target_provisions.json
│   ├── metadata.json             # Opinion letter, dates, etc.
│   └── document_text/            # Raw extracted text per doc
│
├── mappings/
│   ├── provision_mappings.json   # Source→Target mappings with confidence
│   └── variances.json            # Detected variances with classification
│
├── exceptions/
│   ├── exception_log.json        # Structured exception data
│   └── evidence/                 # Attached approval documents
│
├── output/
│   ├── plan_comparison_workbook.csv
│   ├── exception_log.csv
│   ├── qualification_memo.pdf
│   └── execution_package.zip
│
├── audit_log.json                # Immutable log of all user actions (REQ-043)
└── session_state.json            # Work-in-progress (save/restore)
```

**Technology Decision:**
- **SQLite** for structured data storage (provisions, mappings, exceptions)
- Queryable, transactional, ACID compliance
- JSON used only for intermediate representation (REQ-004) and export
- Local file (no server required, maintains local-first architecture)

**Security:**
- No encryption at rest for MVP (local machine assumed secure)
- Future: Optional encryption for sensitive plan data

**Dependencies:**
- None (lowest layer)

---

## Data Flow

### Primary Workflow: Source + Target → Comparison Workbook

```
1. UPLOAD
   User uploads source document(s) + target document(s)
   → Ingestion Module validates files
   → Persistence Layer stores in documents/ folder

2. CLASSIFICATION
   → Ingestion Module detects document types (BPD, AA, etc.)
   → User confirms or overrides

3. EXTRACTION
   → Extraction Module parses provisions from source docs
   → Extraction Module parses provisions from target docs
   → Persistence Layer stores in extracted/source_provisions.json and target_provisions.json

4. RECONCILIATION
   → Reconciliation Module maps source provisions → target provisions (semantic matching)
   → Reconciliation Module detects variances (text diff + classification)
   → Reconciliation Module scores confidence (0-100% per mapping)
   → Persistence Layer stores in mappings/provision_mappings.json and variances.json

5. REVIEW
   → UI displays mappings prioritized by confidence (low first)
   → User approves/rejects/overrides mappings
   → Audit log records all user actions

6. EXCEPTION GENERATION
   → Exception Management Module creates exceptions from Design/Regulatory/HIGH variances
   → Persistence Layer stores in exceptions/exception_log.json

7. EXPORT
   → Output Module generates plan_comparison_workbook.csv
   → Output Module generates exception_log.csv
   → User downloads CSV files for external workflow (email, PensionPro, etc.)

8. SIGN-OFF (Future - Control 004)
   → Output Module compiles execution package
   → Pre-sign-off validation checks for open exceptions
   → Final package exported as PDF or ZIP
```

---

## Non-Functional Characteristics

### Performance (REQ-060)
- **Target:** Process typical conversion (2 source + 2 target docs, ~100 provisions) in 10-15 minutes
- **Rationale:** Manual process takes 4-8 hours, so 10-15 minutes represents 95%+ time savings
- **User expectation management:** Progress indicators show real-time status, managing perception
- **Bottlenecks:**
  - LLM API latency (2-5 seconds per call)
  - Vision fallback for locked PDFs (slower than text extraction)
- **Optimizations:**
  - Parallel LLM calls (batch provision extraction)
  - Caching (reuse extractions if document unchanged)
  - Detailed progress tracking ("Processing provision 45 of 100...")

### Security & Privacy (REQ-061)
- **Local-first:** All data stays on user's machine
- **No telemetry:** No usage tracking, no analytics sent to external servers
- **User-controlled deletion:** Delete project → all data removed
- **Future consideration:** Optional encryption at rest for compliance teams with strict security policies

### Extensibility (REQ-062)
- **Provision types:** Configuration-driven (add new types without code changes)
- **Document vendors:** Pluggable vendor detection rules
- **LLM models:** Abstraction layer allows swapping models
- **Output formats:** Template-based CSV generation (easy to modify schemas)

### Reliability
- **Error handling:** Graceful degradation (if LLM fails, allow manual provision entry)
- **Audit trail:** Immutable log for debugging and compliance
- **Idempotency:** Re-running analysis produces same results (deterministic prompts)

---

## Technology Stack (Preliminary - TBD Phase 3)

**Language:**
- Python (strong LLM library ecosystem: LangChain, LlamaIndex, pydantic)
- Alternative: Node.js (if JavaScript UI preferred for Electron)

**LLM Frameworks:**
- LangChain (established, well-documented)
- LlamaIndex (better for RAG if needed)
- Direct API calls (simpler, less abstraction)

**PDF Processing:**
- PyPDF2 or pdfplumber (text extraction)
- PyMuPDF (faster, better table support)
- Claude Sonnet 4.5 with vision (fallback for locked PDFs)

**UI (Phased Approach):**
- **POC:** CLI-first (Rich library for terminal UI, fastest to build)
- **MVP:** Web UI (React + FastAPI backend, modern UX)
- **Production:** Desktop packaging (Electron or Tauri for offline deployment)

**Storage:**
- SQLite (primary structured data store)
- JSON for intermediate representation and export

**Deployment (Phased):**
- **POC/MVP:** pip installable package (simplest for development)
- **Production:** Docker container (reproducible deployment for customer sites)
- **Future:** Standalone executable for non-technical users (PyInstaller)

---

## Design Constraints

1. **Local-First:** No cloud storage of plan documents (privacy requirement)
2. **CSV Output:** Must match `/process/templates/` schemas (existing workflow integration)
3. **Human-in-Loop:** Never auto-approve changes, always require user review
4. **Graduated Confidence:** 90% / 70% / low thresholds guide review prioritization
5. **Performance:** <10 minute processing for typical conversion (manage user expectations)
6. **Extensibility:** Configuration-driven provision types (avoid hardcoding)

---

## Open Questions (To Be Resolved in Phase 2-3)

### Critical (Blocking Phase 2 POC):
1. **Which LLM model(s)?** Claude Sonnet vs GPT-5 vs hybrid for semantic mapping?
2. **How to score confidence?** Log probabilities, self-evaluation, embedding similarity?
3. **Context window strategy?** How to handle 100-page documents?

### Important (Blocking Phase 2 POC):
4. **Vision model research:** Which model is best for document interpretation with tables/formatting?
   - Recent models may outperform Claude Sonnet 4.5 or GPT-5 vision for structured documents
   - Need benchmark comparison on plan documents with complex tables
5. **Tech stack?** Python + LangChain vs direct API calls?

### Important (Phase 3):
6. **Web UI framework?** React + FastAPI, Next.js, or other?
7. **Vector DB?** FAISS (in-memory) vs Milvus (persistent) for embeddings?

### Nice-to-Have (Phase 4):
8. **Offline mode?** Local LLM inference (requires GPU) or API-only?
9. **Desktop packaging?** Electron, Tauri, or native builds?

---

## Next Steps

1. **Define data models** (provision, mapping, variance schemas) → enables POC
2. **Research LLM strategy** (model comparison, prompt patterns) → informs POC
3. **Build Phase 2 POC** (semantic mapping validation) → validates core assumption
4. **Refine architecture** based on POC learnings (context strategy, performance, costs)

---

## References

- **Requirements:** [/requirements/functional_requirements.md](../../requirements/functional_requirements.md)
- **Process Framework:** [/process/README.md](../../process/README.md)
- **Market Research:** [/research/market_research.pdf](../../research/market_research.pdf)
- **Data Models:** [/design/data_models/](../data_models/)
- **LLM Strategy:** [/design/llm_strategy/](../llm_strategy/)

---

*Last Updated: 2025-10-17*
*Status: Phase 1 Draft - Pending POC Validation*
