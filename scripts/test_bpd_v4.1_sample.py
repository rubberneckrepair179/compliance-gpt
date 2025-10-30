#!/usr/bin/env python3
"""
Test BPD v4.1 extraction on first 5 pages of Relius BPD

v4.1 adds extraction gate, layout rules, and provision_classification
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pymupdf
import json
import base64
from openai import OpenAI
from src.config import settings

# Load v4.1 prompt
def load_prompt(filename):
    prompt_path = Path(__file__).parent.parent / "prompts" / filename
    with open(prompt_path, 'r') as f:
        return f.read()

BPD_PROMPT_V4_1 = load_prompt("provision_extraction_v4.1.txt")

# Import validator
from src.extraction.parallel_vision_extractor import validate_bpd_v4_1_response

def extract_page(client, pdf_path, page_num):
    """Extract single page with v4.1 prompt"""
    doc = pymupdf.open(pdf_path)
    page = doc[page_num]
    pix = page.get_pixmap(dpi=150)
    img_data = pix.tobytes("png")
    img_base64 = base64.b64encode(img_data).decode('utf-8')
    doc.close()

    pdf_page_number = page_num + 1  # PDF pages are 1-indexed

    content = [
        {"type": "text", "text": BPD_PROMPT_V4_1},
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{img_base64}"}
        }
    ]

    print(f"Extracting page {pdf_page_number}...")

    response = client.chat.completions.create(
        model="gpt-5-nano",
        messages=[{"role": "user", "content": content}],
        max_completion_tokens=16000
    )

    response_text = response.choices[0].message.content.strip()

    # Validate
    is_valid, items, error = validate_bpd_v4_1_response(response_text, pdf_page_number)

    if is_valid:
        print(f"  ✓ Page {pdf_page_number}: {len(items)} provisions")
        return items, None
    else:
        print(f"  ✗ Page {pdf_page_number}: {error}")
        return [], error

def main():
    sys.stdout.reconfigure(line_buffering=True)

    print("="*80)
    print("BPD V4.1 SAMPLE TEST - First 5 Pages")
    print("="*80)
    print()
    print("Testing extraction gate + layout rules:")
    print("  - Prompt: provision_extraction_v4.1.txt")
    print("  - Model: gpt-5-nano")
    print("  - Pages: 6-10 of Relius BPD (skip TOC, test actual provisions)")
    print("  - NEW: provision_classification (substantive vs heading)")
    print("  - NEW: Extraction gate (complete sentences only)")
    print("  - NEW: Layout rules (two-column, continued sections, hyphenation)")
    print()

    source_pdf = Path("test_data/raw/relius/relius_bpd_cycle3.pdf")
    output_path = Path("test_data/extracted_vision_v4.1/relius_bpd_sample_pages6-10.json")

    client = OpenAI(api_key=settings.openai_api_key)

    all_provisions = []
    failed_pages = []

    # Extract pages 6-10 (skip TOC/title pages)
    for page_num in range(5, 10):
        provisions, error = extract_page(client, source_pdf, page_num)
        if error:
            failed_pages.append({
                "pdf_page": page_num + 1,
                "error": error
            })
        else:
            all_provisions.extend(provisions)

    print()
    print("="*80)
    print("SAMPLE TEST RESULTS")
    print("="*80)
    print(f"Total pages: 5")
    print(f"Successful: {5 - len(failed_pages)} ({(5-len(failed_pages))/5*100:.1f}%)")
    print(f"Failed: {len(failed_pages)}")
    print(f"Provisions extracted: {len(all_provisions)}")
    print()

    if all_provisions:
        # Check for page_sequence correctness
        by_page = {}
        for p in all_provisions:
            page = p.get('pdf_page')
            if page not in by_page:
                by_page[page] = []
            by_page[page].append(p)

        print("Page sequence validation:")
        for page_num in sorted(by_page.keys()):
            provs = by_page[page_num]
            sequences = [p.get('page_sequence') for p in provs]
            expected = list(range(1, len(provs) + 1))
            if sequences == expected:
                print(f"  ✓ Page {page_num}: sequences {sequences}")
            else:
                print(f"  ✗ Page {page_num}: sequences {sequences} (expected {expected})")

        print()
        print("Provision types:")
        types = {}
        for p in all_provisions:
            ptype = p.get('provision_type')
            types[ptype] = types.get(ptype, 0) + 1
        for ptype, count in sorted(types.items()):
            print(f"  {ptype}: {count}")

        print()
        print("Sample provisions:")
        for p in all_provisions[:3]:
            print(f"  Page {p['pdf_page']}, seq {p['page_sequence']}: {p['section_number']} - {p['section_title'][:50]}")
            print(f"    Type: {p['provision_type']}, Classification: {p['provision_classification']}")
            print(f"    Text: {p['provision_text'][:100]}...")
            print()

    # Save output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_data = {
        "document": str(source_pdf),
        "doc_type": "BPD",
        "model": "gpt-5-nano",
        "prompt_version": "v4.1",
        "total_pages": 5,
        "successful_pages": 5 - len(failed_pages),
        "provisions": all_provisions,
        "failed_pages": failed_pages
    }

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print("="*80)
    print(f"Output saved to: {output_path}")
    print("="*80)


if __name__ == "__main__":
    main()
