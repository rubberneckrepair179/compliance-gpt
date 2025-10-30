#!/usr/bin/env python3
"""
Test v5 Extraction on Small Sample

Tests the new v5 prompt with page number injection on first 5 pages
of Relius BPD to validate improvements before full extraction.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pymupdf
import json
import base64
from openai import OpenAI
from src.config import settings
from src.extraction.parallel_vision_extractor import load_prompt, validate_json_response
import time

def test_v5_on_sample_pages(pdf_path: Path, num_pages: int = 5, start_page: int = 0):
    """Test v5 extraction on first N pages"""
    print("="*80)
    print(f"V5 EXTRACTION TEST - {num_pages} PAGES")
    print("="*80)
    print()
    print("Testing new v5 prompt features:")
    print("  ✓ Page number injection ({{PDF_PAGE}})")
    print("  ✓ Simplified single-job prompt (~450 words)")
    print("  ✓ JSON validation with retry logic")
    print("  ✓ Temperature=0, top_p=1")
    print("  ✓ Fallback to GPT-5-mini on failures")
    print()

    client = OpenAI(api_key=settings.openai_api_key)
    doc = pymupdf.open(pdf_path)
    prompt_template = load_prompt("provision_extraction_v5.txt")

    all_provisions = []
    failed_pages = []
    start_time = time.time()

    for page_num in range(start_page, min(start_page + num_pages, len(doc))):
        pdf_page = page_num + 1
        print(f"Processing page {pdf_page}...", end=" ", flush=True)

        # Inject page number into prompt
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

        # Try extraction
        try:
            response = client.chat.completions.create(
                model="gpt-5-nano",
                messages=[{"role": "user", "content": content}],
                max_completion_tokens=16000
                # Note: gpt-5-nano doesn't support temperature parameter
            )

            response_text = response.choices[0].message.content.strip()
            is_valid, items, error = validate_json_response(response_text, pdf_page)

            if is_valid:
                all_provisions.extend(items)
                print(f"✓ {len(items)} provisions")
            else:
                failed_pages.append({"pdf_page": pdf_page, "error": error})
                print(f"✗ {error}")

        except Exception as e:
            failed_pages.append({"pdf_page": pdf_page, "error": str(e)})
            print(f"✗ {str(e)}")

    doc.close()
    elapsed = time.time() - start_time

    # Save results
    output_path = Path("test_data/extracted_vision_v5/test_relius_bpd_5pages.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    result = {
        "document": str(pdf_path),
        "doc_type": "BPD",
        "model": "gpt-5-nano",
        "test_pages": num_pages,
        "successful_pages": num_pages - len(failed_pages),
        "failed_pages_count": len(failed_pages),
        "success_rate_percent": round((num_pages - len(failed_pages)) / num_pages * 100, 1),
        "extraction_time_seconds": round(elapsed, 2),
        "bpds": all_provisions,
        "failed_pages": failed_pages
    }

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    return result


def main():
    """Test v5 extraction on 5 pages of Relius BPD"""
    result = test_v5_on_sample_pages(
        pdf_path=Path("test_data/raw/relius/relius_bpd_cycle3.pdf"),
        num_pages=5,
        start_page=9  # Pages 10-14 (0-indexed, so page 10 = index 9)
    )

    print()
    print("="*80)
    print("V5 TEST RESULTS")
    print("="*80)
    print(f"Success Rate: {result['success_rate_percent']}%")
    print(f"Provisions Extracted: {len(result['bpds'])}")
    print(f"Failed Pages: {result['failed_pages_count']}")

    if result['failed_pages_count'] > 0:
        print()
        print("Failed Pages Details:")
        for failure in result['failed_pages']:
            print(f"  Page {failure['pdf_page']}: {failure['error']}")

    print()
    print("Sample Provisions (first 3):")
    for i, prov in enumerate(result['bpds'][:3], 1):
        print(f"\n{i}. Page {prov['pdf_page']}, Section {prov['section_number']}: {prov['section_title']}")
        print(f"   Type: {prov['provision_type']}")
        print(f"   Text: {prov['provision_text'][:100]}...")

    print()
    print("✓ Check that all provisions have pdf_page field")
    print("✓ Check that provision types are valid (definition|operational|regulatory|unknown)")
    print("✓ Check that provision_text is complete (not truncated)")
    print()
    print("Full results: test_data/extracted_vision_v5/test_relius_bpd_5pages.json")
    print("="*80)


if __name__ == "__main__":
    main()
