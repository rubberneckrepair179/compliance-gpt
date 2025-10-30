# AA v5 Implementation Plan

**Date:** 2025-10-30
**Based on:** Expert consultation response
**Goal:** Implement working AA extraction using provisions + form elements model

---

## Expert Recommendations Summary

### Model Decision
✅ **GPT-5-mini exclusively** for AA extraction
- AA forms are visually dense (checkboxes, nested options, handwriting)
- Mini handles layout and text readouts more reliably than nano
- Cost premium worth avoiding retry cycles

### Architecture Decision
✅ **Reuse BPD provision extractor + add form element detection**
- Stop treating AAs as Q&A
- Extract provisions hierarchically (like BPD v5)
- Add `form_elements` array when provisions have checkboxes/text fields

### Prompt Target
✅ **~550 words** (expert provided complete prompt)
- Page number injection via `{{PDF_PAGE}}`
- JSON Schema enforcement (if supported)
- Minimal examples (1 positive, 1 empty array)

### Expected Success Rate
✅ **98-99%** with mini + schema + repair retry

---

## Implementation Phases

### Phase 1: Create v5 Prompt (30 min)
**File:** `prompts/aa_extraction_v5.txt`

**Actions:**
- [x] Use expert's ~560 word prompt template
- [x] Add page number injection placeholder `{{PDF_PAGE}}`
- [x] Include minimal examples (1 provision with form elements, 1 empty array)
- [x] Define unified provision + form_elements model

**Output model:**
```json
{
  "pdf_page": 5,
  "section_number": "3.01(a)",
  "section_title": "Pre-tax elective deferrals",
  "parent_section": "3.01",
  "provision_text": "The Plan permits Participants to make pre-tax elective deferrals.",
  "provision_type": "operational",
  "status": "unanswered|answered|ambiguous|conflict",
  "form_elements": [
    {
      "element_type": "checkbox|text",
      "element_sequence": 1,
      "is_selected": true,       // for checkbox
      "text_value": null,        // for text
      "confidence": 0.98
    }
  ]
}
```

---

### Phase 2: Update Extractor for AA (1-2 hours)

**File:** `src/extraction/parallel_vision_extractor.py`

**Actions:**
- [ ] Add AA-specific validation function (similar to BPD's `validate_json_response`)
- [ ] Support `form_elements` array in validation
- [ ] Ensure model selection: **GPT-5-mini for AA** (not nano)
- [ ] Add page number injection for AA prompt (like BPD v5)

**Validation checks:**
```python
def validate_aa_response(content: str, expected_page: int) -> tuple[bool, list, str]:
    """Validate AA JSON response

    Returns: (is_valid, items, error_message)
    """
    try:
        items = json.loads(content)

        # Must be array
        if not isinstance(items, list):
            return False, [], "Response is not a JSON array"

        # Empty arrays valid (instruction pages)
        if len(items) == 0:
            return True, [], ""

        # Check each provision
        for i, item in enumerate(items):
            required = ["pdf_page", "section_number", "section_title", "parent_section",
                       "provision_text", "provision_type", "status", "form_elements"]
            missing = [f for f in required if f not in item]
            if missing:
                return False, [], f"Item {i} missing fields: {missing}"

            # Verify page number
            if item["pdf_page"] != expected_page:
                return False, [], f"Item {i} wrong pdf_page: {item['pdf_page']} (expected {expected_page})"

            # Verify provision_type enum
            if item["provision_type"] not in ["definition", "operational", "regulatory", "unknown"]:
                return False, [], f"Item {i} invalid provision_type: {item['provision_type']}"

            # Verify status enum
            if item["status"] not in ["unanswered", "answered", "ambiguous", "conflict"]:
                return False, [], f"Item {i} invalid status: {item['status']}"

            # Verify form_elements structure
            if not isinstance(item["form_elements"], list):
                return False, [], f"Item {i} form_elements is not array"

            for j, elem in enumerate(item["form_elements"]):
                elem_required = ["element_type", "element_sequence", "is_selected", "text_value", "confidence"]
                elem_missing = [f for f in elem_required if f not in elem]
                if elem_missing:
                    return False, [], f"Item {i}, element {j} missing: {elem_missing}"

                if elem["element_type"] not in ["checkbox", "text"]:
                    return False, [], f"Item {i}, element {j} invalid type: {elem['element_type']}"

        return True, items, ""

    except json.JSONDecodeError as e:
        return False, [], f"JSON parse error: {str(e)}"
```

**Model selection:**
```python
# In parallel_vision_extractor.py, update to use mini for AA
if doc_type == "AA":
    model = "gpt-5-mini"  # AA requires mini for visual complexity
else:
    model = "gpt-5-nano"  # BPD works well with nano
```

---

### Phase 3: Create AA Extraction Script (15 min)

**File:** `scripts/extract_relius_aa_v5.py`

```python
#!/usr/bin/env python3
"""
Extract Relius AA using v5 prompt (provisions + form elements model)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extraction.parallel_vision_extractor import extract_document_parallel

def main():
    """Extract Relius AA with v5 prompt"""
    sys.stdout.reconfigure(line_buffering=True)

    print("="*80)
    print("V5 AA EXTRACTION - RELIUS")
    print("="*80)
    print()
    print("Configuration:")
    print("  - Prompt: aa_extraction_v5.txt")
    print("  - Model: GPT-5-mini (required for AA visual complexity)")
    print("  - Architecture: Provisions + form elements (unified with BPD)")
    print("  - Workers: 16 (parallel)")
    print("  - Batch size: 1 page/request")
    print("  - Retry logic: mini + repair (no nano fallback)")
    print()

    extract_document_parallel(
        pdf_path=Path("test_data/raw/relius/relius_aa_cycle3.pdf"),
        doc_type="AA",
        output_path=Path("test_data/extracted_vision_v5/relius_aa_provisions.json"),
        batch_size=1,
        max_workers=16
    )

    print()
    print("="*80)
    print("Success criteria:")
    print("  - 98%+ success rate")
    print("  - Provisions extracted with hierarchy (section_number + parent_section)")
    print("  - Form elements captured (checkboxes + text fields)")
    print("  - 100% have pdf_page field")
    print("="*80)

if __name__ == "__main__":
    main()
```

**Similar script:** `scripts/extract_ascensus_aa_v5.py`

---

### Phase 4: Test on Sample Pages (30 min)

**Create test script:** `scripts/test_aa_v5_sample.py`

```python
#!/usr/bin/env python3
"""Test AA v5 on first 5 pages of Relius AA"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pymupdf
import json
import base64
from openai import OpenAI
from src.config import settings
from src.extraction.parallel_vision_extractor import load_prompt
# Import new validate_aa_response when created
import time

def test_aa_v5_sample():
    """Test v5 on 5 pages"""
    client = OpenAI(api_key=settings.openai_api_key)
    doc = pymupdf.open("test_data/raw/relius/relius_aa_cycle3.pdf")
    prompt_template = load_prompt("aa_extraction_v5.txt")

    all_provisions = []

    for page_num in range(5):  # First 5 pages
        pdf_page = page_num + 1
        print(f"Processing page {pdf_page}...", end=" ", flush=True)

        # Inject page number
        prompt = prompt_template.replace("{{PDF_PAGE}}", str(pdf_page))

        # Get page image
        page = doc[page_num]
        pix = page.get_pixmap(dpi=150)
        img_data = pix.tobytes("png")
        img_base64 = base64.b64encode(img_data).decode('utf-8')

        content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}}
        ]

        # Call mini
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[{"role": "user", "content": content}],
            max_completion_tokens=16000
        )

        response_text = response.choices[0].message.content.strip()

        try:
            items = json.loads(response_text)
            all_provisions.extend(items)
            print(f"✓ {len(items)} provisions")
        except Exception as e:
            print(f"✗ {str(e)}")

    doc.close()

    # Show results
    print(f"\n{'='*80}")
    print(f"Total provisions: {len(all_provisions)}")
    print("\nSample provision with form elements:")
    for prov in all_provisions:
        if prov.get("form_elements") and len(prov["form_elements"]) > 0:
            print(json.dumps(prov, indent=2))
            break
    print(f"{'='*80}")

if __name__ == "__main__":
    test_aa_v5_sample()
```

**Run:** `python scripts/test_aa_v5_sample.py`

**Validate:**
- Provisions extracted (not 0!)
- Hierarchy present (section_number, parent_section)
- Form elements captured
- Page numbers correct

---

### Phase 5: Full Extraction (1 hour processing time)

**Run:**
```bash
python scripts/extract_relius_aa_v5.py
python scripts/extract_ascensus_aa_v5.py
```

**Expected results:**
- 98-99% success rate
- Relius: ~1,000-1,500 provisions (with form elements)
- Ascensus: ~2,000-3,000 provisions

---

### Phase 6: Validate & Update PIPELINE.md (30 min)

**Actions:**
- [ ] Verify outputs have correct structure
- [ ] Check sample provisions for quality
- [ ] Validate hierarchy (parent_section links)
- [ ] Check form elements captured correctly
- [ ] Update PIPELINE.md Section 1.2 with accurate v5 details

---

## Optional: JSON Schema Enforcement

**If we want to add structured outputs (per expert recommendation):**

**Create schema file:** `schemas/aa_provision_schema.json`

```json
{
  "type": "array",
  "items": {
    "type": "object",
    "required": ["pdf_page", "section_number", "section_title", "parent_section", "provision_text", "provision_type", "status", "form_elements"],
    "additionalProperties": false,
    "properties": {
      "pdf_page": {"type": "integer"},
      "section_number": {"type": "string"},
      "section_title": {"type": "string"},
      "parent_section": {"type": ["string", "null"]},
      "provision_text": {"type": "string"},
      "provision_type": {
        "type": "string",
        "enum": ["definition", "operational", "regulatory", "unknown"]
      },
      "status": {
        "type": "string",
        "enum": ["unanswered", "answered", "ambiguous", "conflict"]
      },
      "form_elements": {
        "type": "array",
        "items": {
          "type": "object",
          "required": ["element_type", "element_sequence", "is_selected", "text_value", "confidence"],
          "additionalProperties": false,
          "properties": {
            "element_type": {"type": "string", "enum": ["checkbox", "text"]},
            "element_sequence": {"type": "integer", "minimum": 1},
            "is_selected": {"type": ["boolean", "null"]},
            "text_value": {"type": ["string", "null"]},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1}
          }
        }
      }
    }
  }
}
```

**Use in API call:**
```python
response = client.chat.completions.create(
    model="gpt-5-mini",
    messages=[{"role": "user", "content": content}],
    max_completion_tokens=16000,
    response_format={
        "type": "json_schema",
        "json_schema": {
            "strict": True,
            "schema": schema
        }
    }
)
```

**Defer this to Phase 7** (post-MVP optimization from tech debt doc)

---

## Timeline Estimate

| Phase | Time | Status |
|-------|------|--------|
| 1. Create v5 prompt | 30 min | ⬜ Not started |
| 2. Update extractor | 1-2 hours | ⬜ Not started |
| 3. Create scripts | 15 min | ⬜ Not started |
| 4. Test sample | 30 min | ⬜ Not started |
| 5. Full extraction | 1 hour (processing) | ⬜ Not started |
| 6. Validate & docs | 30 min | ⬜ Not started |
| **Total** | **3-4 hours** | |

**Processing time:** ~20 minutes for both AA documents (45 + 104 pages)

---

## Success Criteria

**Must achieve:**
- ✅ 98%+ success rate (expert promised 98-99%)
- ✅ Provisions extracted (not 0 like v4!)
- ✅ Hierarchy captured (section_number + parent_section like BPD)
- ✅ Form elements detected (checkboxes + text fields)
- ✅ Page numbers on all provisions
- ✅ Handles blank templates (status=unanswered)
- ✅ Handles completed forms (status=answered, values captured)

**Nice to have:**
- Confidence scoring working
- Ambiguous/conflict detection working
- <15 min total processing time

---

## Key Differences from v4

| Aspect | v4 (FAILED) | v5 (EXPERT) |
|--------|-------------|-------------|
| **Concept** | "Election questions" | Provisions + form elements |
| **Model** | nano | mini |
| **Word count** | 1,649 | ~550 |
| **Page injection** | None | {{PDF_PAGE}} |
| **Data model** | Discriminated unions | Unified provisions |
| **Hierarchy** | question_number only | section_number + parent_section |
| **Success** | 0 elections | 98-99% expected |

---

## Next Steps

1. Review this plan with Sergio
2. Confirm approach aligns with understanding
3. Begin Phase 1 (create v5 prompt)
4. Execute phases sequentially
5. Test and validate
6. Update PIPELINE.md

**Question for Sergio:** Ready to proceed with Phase 1 (create v5 prompt)?
