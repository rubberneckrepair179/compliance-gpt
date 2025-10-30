# AA v5 Hierarchy Extraction - Expert Consultation Request

**Date:** 2025-10-30
**Context:** Follow-up to initial AA v5 implementation
**Status:** Sample test revealed structural extraction errors

---

## Background

We successfully implemented AA v5 using a **provisions + form_elements** model (314-word prompt, GPT-5-mini). Initial sample test showed:
- ✅ 100% success rate (5/5 pages)
- ✅ 79 provisions extracted (was 0 with v4)
- ✅ Form elements detected (checkboxes, text fields)

However, **user review revealed critical structural errors** in how we're extracting hierarchical provisions with form elements.

---

## Problem Statement

**The LLM is lumping multiple labeled form fields into a single provision instead of extracting each as a separate provision with its own hierarchy.**

### Example 1: Text Fields (Currently WRONG)

**What we're extracting:**
```json
{
  "section_number": "1.",
  "section_title": "EMPLOYER'S NAME, ADDRESS, TELEPHONE NUMBER, TIN AND FISCAL YEAR",
  "parent_section": null,
  "provision_text": "EMPLOYER'S NAME...\n\nName: ___\nAddress: ___\nStreet: ___\nCity: ___\nState: ___\nZip: ___\nTelephone: ___\nTIN: ___\nFiscal Year: ___",
  "form_elements": [
    {"element_type": "text", "element_sequence": 1, ...},  // no label
    {"element_type": "text", "element_sequence": 2, ...},  // no label
    {"element_type": "text", "element_sequence": 3, ...},  // no label
    ... // 8 unlabeled text fields
  ]
}
```

**What it SHOULD be (user-specified correct structure):**
```
"EMPLOYER INFORMATION" (heading, no number)
└─ "1. EMPLOYER'S NAME, ADDRESS, TELEPHONE NUMBER, TIN AND FISCAL YEAR" (parent)
    ├─ Name: [text field] (child provision, section_number="1.a" or empty, parent_section="1")
    ├─ Address: [text field] (also labeled "Street" - two labels for one field!)
    ├─ City: [text field]
    ├─ State: [text field]
    ├─ Zip: [text field]
    ├─ Telephone: [text field]
    ├─ Taxpayer Identification Number (TIN): [text field]
    └─ Employer's Fiscal Year ends: [text field]
```

**Each labeled field should be extracted as:**
```json
{
  "section_number": "",  // or "1.a" if there's visible numbering
  "section_title": "Name",
  "parent_section": "1",
  "provision_text": "Name: __________",
  "form_elements": [
    {"element_type": "text", "element_sequence": 1, "field_label": "Name", ...}
  ]
}
```

### Example 2: Nested Checkboxes (User-Provided Structure)

**Actual AA structure (user transcription):**
```
"2. Type of Entity"
├─ a. [ ] Corporation
├─ b. [ ] ... (other options)
├─ d. [ ] Limited Liability Company taxed as:
│   ├─ 1. [ ] a partnership or sole proprietorship
│   ├─ 2. [ ] ... (more nested options)
│   └─ ...
├─ ...
└─ g. [ ] Other: ________ (checkbox + text field combo)
    └─ text_element (the blank for "Other")
```

**Expected extraction:**
- **Question 2 parent**: `section_number="2"`, `provision_text="Type of Entity"`, `form_elements=[]`
- **Option a**: `section_number="2.a"`, `parent_section="2"`, `provision_text="Corporation"`, `form_elements=[checkbox]`
- **Option d**: `section_number="2.d"`, `parent_section="2"`, `provision_text="Limited Liability Company taxed as:"`, `form_elements=[checkbox]`
- **Option d.1**: `section_number="2.d.1"`, `parent_section="2.d"`, `provision_text="a partnership or sole proprietorship"`, `form_elements=[checkbox]`
- **Option g**: `section_number="2.g"`, `parent_section="2"`, `provision_text="Other: ____"`, `form_elements=[checkbox, text]`

---

## Current Prompt (314 words)

```
SYSTEM ROLE:
You extract provisions and any embedded form elements from a single Adoption Agreement page.

OUTPUT
{
  "pdf_page": {{PDF_PAGE}},
  "section_number": "string",
  "section_title": "string",
  "parent_section": "string|null",
  "provision_text": "string",
  "provision_type": "definition|operational|regulatory|unknown",
  "status": "unanswered|answered|ambiguous|conflict",
  "form_elements": [
    {
      "element_type": "checkbox|text",
      "element_sequence": 1,
      "is_selected": true,
      "text_value": "string|null",
      "confidence": 0.0-1.0
    }
  ]
}

RULES
- JSON array only. No preface or trailing text.
- Extract provisions that carry actual rules or definitions. Skip page headers/footers, TOC lines, and stand-alone headings with no following sentences.
- If the page has instructions only and no provisions or form elements, return [].
- If a provision contains form elements (checkboxes, radios, lines/blanks), include that provision even when unanswered. Set status="unanswered" and:
  • For checkboxes: include elements with is_selected true/false as seen.
  • For text blanks: include a text element with text_value (string) or null.
- Heuristics:
  • Definitions often include "means".
  • Operational provisions prescribe actions ("shall/must/may"), schedules, or formulas.
  • Regulatory provisions cite statutes/regs (e.g., §401(a)(9)).
  If uncertain, use "unknown".
- Hierarchy:
  • Use visible numbering for section_number (e.g., "3.01(a)"); parent_section is the immediate ancestor like "3.01".
  • When numbering absent, set section_number="" and parent_section=null.

EXAMPLES

Page with checkbox question and multiple options:
[
  {
    "pdf_page": 5,
    "section_number": "3.01",
    "section_title": "Pre-tax elective deferrals",
    "parent_section": null,
    "provision_text": "The Plan permits pre-tax elective deferrals under Code §401(k):",
    "provision_type": "operational",
    "status": "unanswered",
    "form_elements": []
  },
  {
    "pdf_page": 5,
    "section_number": "3.01(a)",
    "section_title": "All eligible employees",
    "parent_section": "3.01",
    "provision_text": "☐ All eligible employees may make elective deferrals",
    "provision_type": "operational",
    "status": "unanswered",
    "form_elements": [
      {"element_type": "checkbox", "element_sequence": 1, "is_selected": false, "text_value": null, "confidence": 0.95}
    ]
  },
  {
    "pdf_page": 5,
    "section_number": "3.01(b)",
    "section_title": "Specified employees only",
    "parent_section": "3.01",
    "provision_text": "☐ Only employees meeting the following criteria: ___________",
    "provision_type": "operational",
    "status": "unanswered",
    "form_elements": [
      {"element_type": "checkbox", "element_sequence": 1, "is_selected": false, "text_value": null, "confidence": 0.95},
      {"element_type": "text", "element_sequence": 2, "is_selected": null, "text_value": null, "confidence": 0.90}
    ]
  }
]

Page with fill-in-the-blank form (employer information):
[
  {
    "pdf_page": 2,
    "section_number": "1.02",
    "section_title": "Plan Name",
    "parent_section": "1",
    "provision_text": "Plan Name: _______________________________",
    "provision_type": "operational",
    "status": "unanswered",
    "form_elements": [
      {"element_type": "text", "element_sequence": 1, "is_selected": null, "text_value": null, "confidence": 0.92}
    ]
  }
]
```

---

## Specific Questions for Expert

### 1. Hierarchy Extraction Strategy

**Question:** How do we instruct the LLM to extract each labeled form field as a separate provision instead of grouping them?

**Current behavior:** All 8 text fields under Question 1 are lumped into one provision with 8 unlabeled form_elements.

**Desired behavior:** Each labeled field (Name, Address, City, State, Zip, Telephone, TIN, Fiscal Year) should be its own provision with one form_element.

**Options we're considering:**
- A. Add explicit instruction: "Each labeled form field (Name: ___, Address: ___, etc.) is a separate provision"
- B. Add negative example showing the wrong grouping behavior
- C. Change the data model to support "field_label" in form_elements (so we can keep grouping but label each element)
- D. Something else?

### 2. Section Numbering for Unlabeled Fields

**Question:** When form fields have labels (Name, Address, City) but NO visible numbering (a, b, c), what should section_number be?

**Options:**
- A. Empty string (`section_number=""`) for all, rely on `section_title` for identity
- B. Synthesize numbering (`section_number="1.a"`, `"1.b"`, etc.) based on visual sequence
- C. Use label as section_number (`section_number="Name"`, `"Address"`)
- D. Something else?

**Tradeoff:** Empty strings make comparison harder (can't match by section_number), but synthesized numbering might conflict with actual AA numbering elsewhere.

### 3. Nested Checkbox Hierarchy

**Question:** For nested checkboxes like:
```
d. [ ] Limited Liability Company taxed as:
   1. [ ] a partnership or sole proprietorship
   2. [ ] a corporation
```

Should we extract:
- A. Two provisions: "d" (parent with checkbox) + "d.1" (child with checkbox)
- B. Three provisions: "d" (parent, no checkbox) + "d checkbox" + "d.1" (child with checkbox)
- C. One provision "d" with two form_elements (one for parent checkbox, one for child)?

**User expectation:** Each numbered/lettered option is a separate provision with its own checkbox.

### 4. Combined Checkbox + Text Field

**Question:** For options like:
```
g. [ ] Other: __________
```

Should we extract:
- A. One provision "g" with two form_elements (checkbox + text)
- B. Two provisions: "g" (checkbox) + "g.text" (text field)

**Current prompt example shows option A (two form_elements in one provision).** Is this correct?

### 5. Field Labels in form_elements

**Question:** Should form_elements include a `field_label` attribute?

**Current schema:**
```json
{"element_type": "text", "element_sequence": 1, "text_value": null, "confidence": 0.95}
```

**Proposed enhanced schema:**
```json
{"element_type": "text", "element_sequence": 1, "field_label": "Taxpayer Identification Number (TIN)", "text_value": null, "confidence": 0.95}
```

**Tradeoff:** More semantic information per element, but increases prompt complexity. Alternatively, if each labeled field is its own provision, the `section_title` already captures the label.

### 6. Prompt Length Budget

**Current:** 314 words (5x reduction from v4's 1,649 words)
**Expert previous recommendation:** ~550 words
**Question:** How much can we add to fix hierarchy extraction without sacrificing reliability?

**Options:**
- A. Add 1-2 more examples (checkbox hierarchy, nested options) - might push to 450-500 words
- B. Add explicit rules about field-level extraction - might push to 400 words
- C. Keep it minimal, rely on examples only

---

## What We Need

1. **Prompt revision recommendations** that achieve correct hierarchical extraction
2. **Guidance on section_number strategy** for unlabeled fields (empty vs synthesized vs label-as-number)
3. **Validation** that our data model (section_number + parent_section + form_elements) is sufficient, or if we need schema changes
4. **Expected success rate** with revised prompt (we achieved 100% on 5 pages with v5, but wrong structure)

---

## Additional Context

### Document Metadata Issue
**Minor bug discovered:** The `"document"` field in JSON output currently shows the output file path instead of source PDF path.

**Current:** `"document": "test_data/extracted_vision_v5/relius_aa_sample_5pages.json"`
**Should be:** `"document": "test_data/raw/relius/relius_aa_cycle3.pdf"`

This is a simple Python fix (already in extractor code, just need to verify it's using pdf_path not output_path).

---

## Success Criteria

**We'll consider this resolved when:**
1. Each labeled form field (Name, Address, City, etc.) extracts as a separate provision
2. Nested checkbox options (2.a, 2.d, 2.d.1) extract with correct parent_section hierarchy
3. Combined checkbox+text options (g. [ ] Other: ___) extract correctly
4. Sample test on 5 pages shows correct structure (user approval required)
5. Success rate remains ≥98% (as originally recommended)

---

## Files for Reference

- **Current prompt:** `/prompts/aa_extraction_v5.txt` (314 words)
- **Sample output:** `/test_data/extracted_vision_v5/relius_aa_sample_5pages.json`
- **Extractor code:** `/src/extraction/parallel_vision_extractor.py`
- **Previous consultation:** `/docs/AA_EXTRACTION_CONSULTATION_2025-10-30.md` (led to v5)

---

**Thank you for your continued guidance on this challenging prompt engineering problem!**
