# `/design` — Technical Design Documentation

This folder contains the **technical architecture and implementation design** for compliance-gpt, defining **how** we build the system specified in `/requirements`.

---

## Design Philosophy

**Hybrid Approach: Anchored Top-Down with Bottom-Up Validation**

We use a phased design strategy that balances architectural planning with early validation of critical unknowns:

1. **Phase 1: ANCHOR (Top-Down)** - Define system boundaries, data models, constraints
2. **Phase 2: VALIDATE THE CORE (Bottom-Up POC)** - Prove REQ-021 semantic mapping feasibility
3. **Phase 3: FILL IN THE MIDDLE (Top-Down)** - Design supporting modules informed by POC learnings
4. **Phase 4: COMPLETE & INTEGRATE (Top-Down)** - Finish remaining modules, UI/UX, testing

**Rationale:** Semantic provision mapping (REQ-021) is novel, unproven, and THE core differentiator. We validate it early (Phase 2 POC) before investing in full system design. This de-risks the entire project.

---

## Design Principles

1. **Human-in-the-Loop Always** - AI proposes, human approves. Never fully autonomous.
2. **Local-First (MVP)** - No cloud storage of plan documents (REQ-061 privacy requirement)
3. **CSV Compatibility** - Output must match `/process/templates/` schema for existing workflow integration
4. **Graduated Confidence** - 90% / 70% / low thresholds guide user review prioritization
5. **LLM-First Architecture** - Semantic understanding is core capability, not bolt-on feature
6. **Fail Gracefully** - When uncertain (low confidence), abstain and flag for manual review

---

## Folder Structure

```
/design/
├── README.md                          # This file - design overview and index
│
├── architecture/
│   ├── system_architecture.md         # Component diagram, data flow, constraints
│   ├── deployment_model.md            # Installation, runtime, local-first strategy
│   └── technology_stack.md            # Languages, frameworks, libraries + rationale
│
├── data_models/
│   ├── document_model.md              # Document JSON schema (REQ-004)
│   ├── provision_model.md             # Provision structure & taxonomy
│   ├── mapping_model.md               # Source→Target mappings with confidence
│   └── variance_model.md              # Variance types, classifications, impact levels
│
├── modules/
│   ├── ingestion/
│   │   ├── pdf_processing.md         # Text extraction + vision fallback (REQ-002)
│   │   ├── document_classification.md # Document type detection (REQ-003)
│   │   └── batch_processing.md       # Folder upload, progress tracking (REQ-001)
│   │
│   ├── extraction/
│   │   ├── provision_extraction.md   # LLM prompting for provision parsing (REQ-020)
│   │   └── metadata_extraction.md    # Opinion letter, dates, plan details (REQ-010)
│   │
│   ├── reconciliation/               # CORE MODULE (Control 002)
│   │   ├── semantic_mapping.md       # Cross-vendor provision matching (REQ-021)
│   │   ├── variance_detection.md     # Diff + classification (REQ-022)
│   │   └── confidence_scoring.md     # Scoring model & thresholds (REQ-024)
│   │
│   ├── exception_management/
│   │   ├── exception_generation.md   # Auto-population from variances (REQ-030)
│   │   └── tracking_workflow.md      # Status management, evidence linking (REQ-031)
│   │
│   └── output/
│       ├── csv_export.md             # Template mapping & formatting (REQ-050)
│       └── ui_components.md          # Review interface, bulk approval UX (REQ-051)
│
├── llm_strategy/
│   ├── model_selection.md            # Claude vs GPT-5 vs open-source evaluation
│   ├── prompt_engineering.md         # Prompt templates & few-shot examples
│   ├── context_management.md         # Chunking strategy for long documents
│   └── evaluation_framework.md       # Accuracy benchmarks, test methodology
│
├── security_privacy/
│   ├── data_handling.md              # Local storage, encryption, deletion (REQ-061)
│   └── audit_logging.md              # Immutable log design (REQ-043)
│
└── testing_validation/
    ├── test_strategy.md              # Unit, integration, end-to-end approach
    ├── accuracy_validation.md        # How to measure 70-90% automation target
    └── sample_documents.md           # Acquiring test corpus (Relius/ASC/ftwilliam)
```

---

## Current Status

### Phase 1: ANCHOR (Complete)
- ✅ Design structure created
- ✅ System architecture defined
- ✅ Core data models specified (provision, mapping, variance, crosswalk)
- ✅ LLM strategy research completed
- ✅ Model selection documented

### Phase 2: VALIDATE THE CORE (In Progress)
- ✅ LLM model selection research (GPT-5 vision + GPT-4.1 semantic)
- ✅ Acquire sample plan documents for testing (4 documents: source/target BPD+AA)
- ✅ Build semantic mapping POC (hybrid embeddings + LLM)
- ✅ BPD crosswalk generated (15 1:1 matches, 27% match rate on templates)
- 🔄 Vision extraction running (GPT-5 vision for BPDs + AAs)
- ⬜ Build AA crosswalk
- ⬜ Measure POC accuracy against 70% threshold

### Phase 3: FILL IN THE MIDDLE (Future)
- ⬜ Design supporting modules (ingestion, extraction, output)
- ⬜ Refine architecture based on POC learnings
- ⬜ Define deployment model

### Phase 4: COMPLETE & INTEGRATE (Future)
- ⬜ Design remaining modules (exception mgmt, sign-off)
- ⬜ UI/UX design
- ⬜ Testing strategy & validation plan

---

## Design Decision Log

| Date | Decision | Rationale | Impact |
|------|----------|-----------|--------|
| 2025-10-17 | Hybrid design approach (anchor + POC) | De-risk REQ-021 semantic mapping before full architecture investment | Validates core capability early |
| 2025-10-17 | Phase 2 POC before module design | REQ-021 is novel/unproven, need empirical validation | May inform architecture changes |
| 2025-10-17 | SQLite for structured storage | Queryable, transactional, local-first compliant | Primary data store for provisions/mappings |
| 2025-10-17 | 10-15 minute processing acceptable | Manual process takes 4-8 hours, 95%+ time savings | Performance target relaxed from <10 min |
| 2025-10-17 | CLI-first UI for POC | Fastest to build, validates workflow before investing in GUI | Web UI deferred to MVP phase |
| 2025-10-17 | Docker for production deployment | Reproducible deployment for customer sites | pip install for POC/MVP, Docker for production |
| 2025-10-17 | Vision model research needed | Recent models may excel at table/format interpretation | Research task added to Phase 2 prep |
| 2025-10-19 | Switch to GPT-5 vision extraction | Vision models handle form layouts, checkboxes, nested options better than text parsing | All document extraction now vision-based |
| 2025-10-19 | GPT-5 model confirmed available | User preference: "newer better more than 'safer'" - GPT-5 (gpt-5-2025-08-07) works with max_completion_tokens=16000 | Primary vision model for POC |
| 2025-10-19 | BPD+AA crosswalk architecture | Both source and target are BPD+AA pairs, not standalone docs - need separate BPD and AA crosswalks | Dual crosswalk generation (provisions + elections) |
| 2025-10-19 | Vision over text parsing for AAs | Adoption Agreements have complex nested options (d.1, d.2, d.3) - vision extraction captures structure better | AA extraction uses GPT-5 vision exclusively |

*(Additional decisions will be logged here as design progresses)*

---

## Key Design Questions (To Be Resolved)

### Critical (Phase 1-2):
1. **LLM Model:** Claude Sonnet 4.5, GPT-5, open-source, or hybrid?
2. **Context Strategy:** How to handle 100-page documents exceeding context windows?
3. **Confidence Calibration:** What method generates reliable 0-100% scores?
4. **Data Model:** What fields define a "provision" for semantic comparison?

### Important (Phase 3):
5. **Tech Stack:** Python + LangChain? Node.js? Other?
6. **PDF Vision Fallback:** Claude Sonnet 4.5 vision, GPT-5 Vision, or OCR library?
7. **Storage:** SQLite, JSON files, or other local database?
8. **UI Framework:** Web (Electron?), native desktop, or CLI-first?

### Nice-to-Have (Phase 4):
9. **Deployment:** Installer package, Docker container, or pip install?
10. **Extensibility:** Plugin architecture for custom provision types?

---

## Requirements Traceability

Each design document maps back to specific requirements from `/requirements/functional_requirements.md`:

| Design Doc | Primary Requirements | Control |
|------------|---------------------|---------|
| `reconciliation/semantic_mapping.md` | REQ-021 (semantic provision mapping) | Control 002 |
| `reconciliation/variance_detection.md` | REQ-022 (variance detection & classification) | Control 002 |
| `reconciliation/confidence_scoring.md` | REQ-024 (confidence scoring & abstention) | Control 002 |
| `ingestion/pdf_processing.md` | REQ-002 (format resilience, locked PDFs) | Ingestion |
| `data_models/provision_model.md` | REQ-004 (intermediate JSON representation) | Ingestion |
| `output/csv_export.md` | REQ-050 (CSV template output) | Output |

*(Full traceability matrix will be maintained as design progresses)*

---

## Design Templates

To maintain consistency, each design document should follow this structure:

```markdown
# [Module/Component Name]

## Overview
Brief description of what this component does and why it exists.

## Requirements Addressed
- REQ-XXX: [Requirement description]
- REQ-YYY: [Requirement description]

## Design Decisions

### Decision 1: [Title]
**Context:** Why this decision is needed
**Options Considered:**
1. Option A - pros/cons
2. Option B - pros/cons

**Selected:** Option X
**Rationale:** Why this choice
**Implications:** What this means for other components

## Data Structures / Interfaces
Schemas, APIs, or contracts this component exposes/consumes

## Dependencies
- Internal: Other modules this depends on
- External: Libraries, APIs, services

## Open Questions
Unresolved issues that need research or decisions

## References
- Links to requirements
- External documentation
- Related design docs
```

---

## Next Steps

1. **Complete Phase 1 anchor docs:**
   - System architecture (component diagram, data flow)
   - Provision data model (JSON schema)
   - Mapping data model (with confidence scoring)

2. **Research for Phase 2 POC:**
   - LLM model comparison (Claude vs GPT-4 for legal document analysis)
   - Prompt engineering patterns for semantic matching
   - Acquire sample plan documents (anonymized Relius/ASC/ftwilliam docs)

3. **Build Phase 2 POC:**
   - Simple script: 2 provisions in → mapping + confidence out
   - Test on 20-30 provision pairs
   - Measure accuracy: % of mappings human expert would agree with

4. **Decision point:**
   - If accuracy ≥70%: Proceed to Phase 3 (module design)
   - If accuracy 50-70%: Iterate on prompting/model selection
   - If accuracy <50%: Reassess approach (fine-tuning? RAG? hybrid rules+LLM?)

---

## Resources

**Process Framework:** `/process/README.md` (what we're automating)
**Functional Requirements:** `/requirements/functional_requirements.md` (what we're building)
**Market Research:** `/research/market_research.pdf` (competitive landscape, pain points)
**Project Context:** `/CLAUDE.md` (cross-session AI assistant context)

---

*Last Updated: 2025-10-17*
*Current Phase: Phase 1 (Anchor)*
