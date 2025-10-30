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

# Load prompts from external files
def load_prompt(filename):
    """Load prompt from prompts directory"""
    prompt_path = Path(__file__).parent.parent.parent / "prompts" / filename
    with open(prompt_path, 'r') as f:
        return f.read()

# Load extraction prompts
BPD_PROMPT = load_prompt("provision_extraction_v5.txt")  # v5: simplified, single-job, page number injection
AA_PROMPT = load_prompt("aa_extraction_v5.1.txt")  # v5.1: atomic field rule + local_ordinal + field_label


def validate_json_response(content: str, expected_page: int) -> tuple[bool, list, str]:
    """Validate JSON response has correct structure and page numbers

    Returns: (is_valid, items, error_message)
    """
    try:
        items = json.loads(content)

        # Must be a list
        if not isinstance(items, list):
            return False, [], "Response is not a JSON array"

        # Empty arrays are valid (heading-only pages)
        if len(items) == 0:
            return True, [], ""

        # Check each item has required fields and correct page number
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                return False, [], f"Item {i} is not an object"

            required_fields = ["pdf_page", "section_number", "section_title", "provision_text", "provision_type", "parent_section"]
            missing = [f for f in required_fields if f not in item]
            if missing:
                return False, [], f"Item {i} missing fields: {missing}"

            # Verify page number matches expected
            if item["pdf_page"] != expected_page:
                return False, [], f"Item {i} has wrong pdf_page: {item['pdf_page']} (expected {expected_page})"

            # Verify parent_section is null or string
            if item["parent_section"] is not None and not isinstance(item["parent_section"], str):
                return False, [], f"Item {i} has invalid parent_section type: {type(item['parent_section'])}"

        return True, items, ""

    except json.JSONDecodeError as e:
        return False, [], f"JSON parse error: {str(e)}"


def validate_bpd_v4_1_response(content: str, expected_page: int) -> tuple[bool, list, str]:
    """Validate BPD v4.1 JSON response with page_sequence and provision_classification

    Returns: (is_valid, items, error_message)
    """
    try:
        items = json.loads(content)

        # Must be a list
        if not isinstance(items, list):
            return False, [], "Response is not a JSON array"

        # Empty arrays are valid (heading-only pages or "(continued)" pages)
        if len(items) == 0:
            return True, [], ""

        # Check each item has required BPD v4.1 fields
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                return False, [], f"Item {i} is not an object"

            required_fields = ["section_number", "section_title",
                             "provision_text", "provision_type", "provision_classification"]
            missing = [f for f in required_fields if f not in item]
            if missing:
                return False, [], f"Item {i} missing fields: {missing}"

            # Verify provision_classification is valid
            if item["provision_classification"] not in ["substantive", "heading"]:
                return False, [], f"Item {i} invalid provision_classification: {item['provision_classification']}"

            # Only "substantive" should be in output (heading should be filtered by LLM)
            if item["provision_classification"] != "substantive":
                return False, [], f"Item {i} has classification '{item['provision_classification']}' but should be 'substantive'"

            # Verify provision_type is valid
            valid_types = ["definition", "operational", "regulatory"]
            if item["provision_type"] not in valid_types:
                return False, [], f"Item {i} invalid provision_type: {item['provision_type']}"

        # Add pdf_page and page_sequence based on array order (post-processing)
        for i, item in enumerate(items, 1):
            item["pdf_page"] = expected_page
            item["page_sequence"] = i  # 1-based, assigned by extraction order

        return True, items, ""

    except json.JSONDecodeError as e:
        return False, [], f"JSON parse error: {str(e)}"


def validate_aa_response(content: str, expected_page: int) -> tuple[bool, list, str]:
    """Validate AA JSON response with form_elements array

    Returns: (is_valid, items, error_message)
    """
    try:
        items = json.loads(content)

        # Must be a list
        if not isinstance(items, list):
            return False, [], "Response is not a JSON array"

        # Empty arrays are valid (instruction-only pages)
        if len(items) == 0:
            return True, [], ""

        # Check each item has required AA fields
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                return False, [], f"Item {i} is not an object"

            required_fields = ["pdf_page", "section_number", "section_title", "parent_section",
                             "local_ordinal", "field_label", "provision_text", "provision_type", "status", "form_elements"]
            missing = [f for f in required_fields if f not in item]
            if missing:
                return False, [], f"Item {i} missing fields: {missing}"

            # Verify local_ordinal is integer >= 0
            if not isinstance(item["local_ordinal"], int) or item["local_ordinal"] < 0:
                return False, [], f"Item {i} local_ordinal must be integer >= 0"

            # Verify field_label is null or string
            if item["field_label"] is not None and not isinstance(item["field_label"], str):
                return False, [], f"Item {i} field_label must be null or string"

            # Verify page number matches expected
            if item["pdf_page"] != expected_page:
                return False, [], f"Item {i} has wrong pdf_page: {item['pdf_page']} (expected {expected_page})"

            # Verify parent_section is null or string
            if item["parent_section"] is not None and not isinstance(item["parent_section"], str):
                return False, [], f"Item {i} has invalid parent_section type: {type(item['parent_section'])}"

            # Verify status is valid enum value
            # Note: "unknown" added for provisions without form elements (informational text)
            valid_statuses = ["unanswered", "answered", "ambiguous", "conflict", "unknown"]
            if item["status"] not in valid_statuses:
                return False, [], f"Item {i} has invalid status: {item['status']}"

            # Verify form_elements is a list
            if not isinstance(item["form_elements"], list):
                return False, [], f"Item {i} form_elements must be an array"

            # Validate each form element
            for j, elem in enumerate(item["form_elements"]):
                if not isinstance(elem, dict):
                    return False, [], f"Item {i} form_element {j} is not an object"

                elem_required = ["element_type", "element_sequence", "confidence"]
                elem_missing = [f for f in elem_required if f not in elem]
                if elem_missing:
                    return False, [], f"Item {i} form_element {j} missing fields: {elem_missing}"

                # Verify element_type is valid
                if elem["element_type"] not in ["checkbox", "text"]:
                    return False, [], f"Item {i} form_element {j} invalid element_type: {elem['element_type']}"

                # Verify element_sequence is positive integer
                if not isinstance(elem["element_sequence"], int) or elem["element_sequence"] < 1:
                    return False, [], f"Item {i} form_element {j} element_sequence must be positive integer"

                # Verify confidence is 0.0-1.0
                if not isinstance(elem["confidence"], (int, float)) or not (0.0 <= elem["confidence"] <= 1.0):
                    return False, [], f"Item {i} form_element {j} confidence must be 0.0-1.0"

        return True, items, ""

    except json.JSONDecodeError as e:
        return False, [], f"JSON parse error: {str(e)}"


def process_page_batch(client, model, pdf_path, page_start, page_end, doc_type, retry_with_mini=False):
    """Process a batch of pages (up to 5) in one API call with validation and retry"""
    doc = pymupdf.open(pdf_path)

    all_batch_items = []
    failed_pages = []

    # Process each page individually (batch_size=1 for reliability)
    for page_num in range(page_start, min(page_end, len(doc))):
        pdf_page_number = page_num + 1  # PDF pages are 1-indexed

        # Get prompt template and inject page number
        if doc_type == "BPD":
            prompt = BPD_PROMPT.replace("{{PDF_PAGE}}", str(pdf_page_number))
        else:  # AA
            prompt = AA_PROMPT.replace("{{PDF_PAGE}}", str(pdf_page_number))

        # Build content with page image
        page = doc[page_num]
        pix = page.get_pixmap(dpi=150)
        img_data = pix.tobytes("png")
        img_base64 = base64.b64encode(img_data).decode('utf-8')

        content = [
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{img_base64}"}
            }
        ]

        # Try extraction with validation and retry logic
        max_attempts = 3
        # Force mini for AA (complex forms), use nano for BPD (templates)
        if doc_type == "AA":
            current_model = "gpt-5-mini"
        else:
            current_model = "gpt-5-mini" if retry_with_mini else model

        for attempt in range(max_attempts):
            try:
                response = client.chat.completions.create(
                    model=current_model,
                    messages=[{"role": "user", "content": content}],
                    max_completion_tokens=16000
                    # Note: gpt-5-nano doesn't support temperature parameter (only default 1.0)
                )

                response_text = response.choices[0].message.content.strip()

                # Validate JSON with appropriate validator
                if doc_type == "AA":
                    is_valid, items, error = validate_aa_response(response_text, pdf_page_number)
                else:
                    is_valid, items, error = validate_json_response(response_text, pdf_page_number)

                if is_valid:
                    all_batch_items.extend(items)
                    break  # Success

                else:
                    # Attempt 1: Try repair prompt
                    if attempt == 0:
                        repair_content = [
                            {"type": "text", "text": "Output valid JSON only. Remove any text before/after the array. Do not change content."},
                            {"type": "text", "text": f"Previous response:\n{response_text}"}
                        ]
                        content = repair_content
                        continue

                    # Attempt 2: Try with GPT-5-mini if we're using nano and haven't escalated yet
                    elif attempt == 1 and doc_type != "AA" and not retry_with_mini:
                        current_model = "gpt-5-mini"
                        # Reset to original content with page image
                        content = [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{img_base64}"}
                            }
                        ]
                        continue

                    # Attempt 3: Failed all retries
                    else:
                        failed_pages.append({
                            "pdf_page": pdf_page_number,
                            "error": error,
                            "model": current_model,
                            "raw_response": response_text[:500]  # First 500 chars for debugging
                        })
                        break

            except Exception as e:
                if attempt == max_attempts - 1:
                    failed_pages.append({
                        "pdf_page": pdf_page_number,
                        "error": str(e),
                        "model": current_model
                    })
                    break

    doc.close()

    return {
        "success": len(failed_pages) == 0,
        "page_range": f"{page_start+1}-{page_end}",
        "items": all_batch_items,
        "count": len(all_batch_items),
        "failed_pages": failed_pages
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

    # Determine model based on doc_type
    client = OpenAI(api_key=settings.openai_api_key)
    model = "gpt-5-nano"  # Default for BPD
    actual_model = "gpt-5-mini" if doc_type == "AA" else model

    print(f"Model: {actual_model}")
    print(f"Batch size: {batch_size} pages/request")
    print(f"Workers: {max_workers}")
    print()

    # Create page batches
    batches = []
    for start in range(0, total_pages, batch_size):
        batches.append((start, start + batch_size))

    print(f"Processing {len(batches)} batches...")
    start_time = time.time()

    all_items = []
    all_failed_pages = []
    completed = 0

    # Process batches in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_page_batch, client, model, pdf_path,
                           start, end, doc_type, False): (start, end)
            for start, end in batches
        }

        for future in as_completed(futures):
            result = future.result()
            completed += 1

            all_items.extend(result["items"])
            all_failed_pages.extend(result.get("failed_pages", []))

            if result["success"]:
                print(f"✓ Batch {result['page_range']}: {result['count']} items ({completed}/{len(batches)} batches)")
            else:
                failed_count = len(result.get("failed_pages", []))
                print(f"⚠ Batch {result['page_range']}: {result['count']} items, {failed_count} pages failed ({completed}/{len(batches)} batches)")

    elapsed = time.time() - start_time

    # Calculate success metrics
    successful_pages = total_pages - len(all_failed_pages)
    success_rate = (successful_pages / total_pages * 100) if total_pages > 0 else 0

    # Sort provisions by page number, then section number for easier review
    all_items_sorted = sorted(all_items, key=lambda x: (x.get("pdf_page", 0), x.get("section_number", "")))

    # Determine output field name based on doc_type
    if doc_type == "BPD":
        items_key = "bpds"
    else:  # AA
        items_key = "aas"

    # Determine actual model used (mini for AA, nano for BPD)
    actual_model = "gpt-5-mini" if doc_type == "AA" else model

    # Save results
    output_data = {
        "document": str(pdf_path),
        "doc_type": doc_type,
        "model": actual_model,
        "total_pages": total_pages,
        "successful_pages": successful_pages,
        "failed_pages_count": len(all_failed_pages),
        "success_rate_percent": round(success_rate, 1),
        "extraction_time_seconds": round(elapsed, 2),
        "pages_per_second": round(total_pages / elapsed, 2),
        items_key: all_items_sorted,
        "failed_pages": all_failed_pages
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\n{'='*80}")
    print(f"COMPLETED: {len(all_items)} items from {successful_pages}/{total_pages} pages ({success_rate:.1f}% success)")
    if len(all_failed_pages) > 0:
        print(f"⚠ FAILED PAGES: {[p['pdf_page'] for p in all_failed_pages]}")
    print(f"Time: {elapsed:.1f}s ({total_pages/elapsed:.2f} pages/sec)")
    print(f"Output: {output_path}")
    print(f"Note: Provisions automatically sorted by page + section number")
    print(f"{'='*80}\n")

    return output_data


def main():
    """Extract all 4 documents in parallel"""
    sys.stdout.reconfigure(line_buffering=True)

    print("PARALLEL VISION EXTRACTION - ALL DOCUMENTS")
    print("="*80)
    print()

    documents = [
        ("test_data/raw/relius/relius_bpd_cycle3.pdf", "BPD", "test_data/extracted_vision_v4/source_bpd_provisions.json"),
        ("test_data/raw/relius/relius_aa_cycle3.pdf", "AA", "test_data/extracted_vision_v4/source_aa_elections.json"),
        ("test_data/raw/ascensus/ascensus_bpd.pdf", "BPD", "test_data/extracted_vision_v4/target_bpd_provisions.json"),
        ("test_data/raw/ascensus/ascensus_aa_profit_sharing.pdf", "AA", "test_data/extracted_vision_v4/target_aa_elections.json"),
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
