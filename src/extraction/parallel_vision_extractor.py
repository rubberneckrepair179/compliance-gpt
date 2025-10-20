#!/usr/bin/env python3
"""
Parallel Vision Extractor with Batching
Implements GPT-5's suggestions: parallel workers + batch pages per request
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pymupdf
import json
import base64
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import time

from src.config import settings

# Stricter prompts - JSON only, no explanations
BPD_PROMPT = """Extract provisions from this retirement plan Basic Plan Document page.

For EACH provision, extract:
- section_number: Section reference (e.g., "1.1", "Article IV")
- section_title: Section heading or defined term
- provision_text: THE COMPLETE LEGAL TEXT of the provision including all paragraphs, sub-sections (a), (b), (1), (2), etc. PRESERVE ALL LANGUAGE EXACTLY.
- provision_type: definition, eligibility, contribution, vesting, distribution, loan, administrative, or other

Return ONLY a JSON array. No explanatory text before or after.

Example:
[{
  "section_number": "3.2",
  "section_title": "Employer Matching Contributions",
  "provision_text": "The Employer shall make matching contributions equal to 100% of the first 3% of compensation deferred as elective deferrals, plus 50% of the next 2% of compensation deferred. Matching contributions shall be made for each payroll period and shall be allocated to Participants who made elective deferrals during such period.",
  "provision_type": "contribution"
}]"""

AA_PROMPT = """Extract election questions/options from this Adoption Agreement page as JSON array ONLY.

[{
  "question_number": "1",
  "question_text": "...",
  "election_type": "checkbox|fill_in|radio|multi_select",
  "section_context": "...",
  "options": [{
    "label": "a",
    "text": "...",
    "value": null|"checked"|"text",
    "sub_options": [...]
  }]
}]

NO explanatory text. JSON array only."""


def process_page_batch(client, model, pdf_path, page_start, page_end, doc_type):
    """Process a batch of pages (up to 5) in one API call"""
    doc = pymupdf.open(pdf_path)

    # Build content with multiple images
    content = [
        {"type": "text", "text": BPD_PROMPT if doc_type == "BPD" else AA_PROMPT}
    ]

    for page_num in range(page_start, min(page_end, len(doc))):
        page = doc[page_num]
        pix = page.get_pixmap(dpi=150)
        img_data = pix.tobytes("png")
        img_base64 = base64.b64encode(img_data).decode('utf-8')

        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{img_base64}"}
        })

    doc.close()

    # Call API with batched images
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": content}],
            max_completion_tokens=16000
        )

        items = json.loads(response.choices[0].message.content)
        return {
            "success": True,
            "page_range": f"{page_start+1}-{page_end}",
            "items": items,
            "count": len(items)
        }
    except Exception as e:
        return {
            "success": False,
            "page_range": f"{page_start+1}-{page_end}",
            "error": str(e)
        }


def extract_document_parallel(pdf_path: Path, doc_type: str, output_path: Path,
                               batch_size=5, max_workers=8):
    """Extract document using parallel workers with batching"""

    print(f"\n{'='*80}")
    print(f"PARALLEL VISION EXTRACTION: {pdf_path.name} ({doc_type})")
    print(f"{'='*80}")

    doc = pymupdf.open(pdf_path)
    total_pages = len(doc)
    doc.close()

    print(f"Total pages: {total_pages}")
    print(f"Model: gpt-5-nano")
    print(f"Batch size: {batch_size} pages/request")
    print(f"Workers: {max_workers}")
    print()

    client = OpenAI(api_key=settings.openai_api_key)
    model = "gpt-5-nano"  # Force gpt-5-nano (most thorough for vision extraction)

    # Create page batches
    batches = []
    for start in range(0, total_pages, batch_size):
        batches.append((start, start + batch_size))

    print(f"Processing {len(batches)} batches...")
    start_time = time.time()

    all_items = []
    completed = 0

    # Process batches in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_page_batch, client, model, pdf_path,
                           start, end, doc_type): (start, end)
            for start, end in batches
        }

        for future in as_completed(futures):
            result = future.result()
            completed += 1

            if result["success"]:
                all_items.extend(result["items"])
                print(f"✓ Batch {result['page_range']}: {result['count']} items ({completed}/{len(batches)} batches)")
            else:
                print(f"✗ Batch {result['page_range']}: {result['error']}")

    elapsed = time.time() - start_time

    # Save results
    output_data = {
        "document": str(pdf_path),
        "doc_type": doc_type,
        "model": model,
        "total_pages": total_pages,
        "extraction_time_seconds": round(elapsed, 2),
        "pages_per_second": round(total_pages / elapsed, 2),
        doc_type.lower() + "s": all_items
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\n{'='*80}")
    print(f"COMPLETED: {len(all_items)} items from {total_pages} pages")
    print(f"Time: {elapsed:.1f}s ({total_pages/elapsed:.2f} pages/sec)")
    print(f"Output: {output_path}")
    print(f"{'='*80}\n")

    return output_data


def main():
    """Extract all 4 documents in parallel"""
    sys.stdout.reconfigure(line_buffering=True)

    print("PARALLEL VISION EXTRACTION - ALL DOCUMENTS")
    print("="*80)
    print()

    documents = [
        ("test_data/raw/source/bpd/source_bpd_01.pdf", "BPD", "test_data/extracted_vision/source_bpd_01_provisions.json"),
        ("test_data/raw/source/aa/source_aa.pdf", "AA", "test_data/extracted_vision/source_aa_elections.json"),
        ("test_data/raw/target/bpd/target_bpd_05.pdf", "BPD", "test_data/extracted_vision/target_bpd_05_provisions.json"),
        ("test_data/raw/target/aa/target_aa.pdf", "AA", "test_data/extracted_vision/target_aa_elections.json"),
    ]

    total_start = time.time()

    for pdf_path, doc_type, output_path in documents:
        extract_document_parallel(
            pdf_path=Path(pdf_path),
            doc_type=doc_type,
            output_path=Path(output_path),
            batch_size=1,  # 1 page per request (batching caused too many failures)
            max_workers=16  # More workers to compensate for smaller batches
        )

    total_elapsed = time.time() - total_start
    print(f"\nTOTAL TIME: {total_elapsed/60:.1f} minutes")


if __name__ == "__main__":
    main()
