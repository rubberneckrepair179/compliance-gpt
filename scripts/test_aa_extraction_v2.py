#!/usr/bin/env python3
"""
Test AA extraction v2 with discriminated union model

Tests the new prompt and Pydantic models on a single AA page.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pymupdf
import json
import base64
from openai import OpenAI
from pydantic import ValidationError

from src.config import settings
from src.models.election import (
    Election, TextElection, SingleSelectElection, MultiSelectElection,
    ElectionPage, Provenance, Option, FillIn
)


def load_prompt(filename):
    """Load prompt from prompts directory"""
    prompt_path = Path(__file__).parent.parent / "prompts" / filename
    with open(prompt_path, 'r') as f:
        return f.read()


def extract_aa_page(pdf_path: Path, page_num: int):
    """Extract elections from a single AA page"""

    print(f"\n{'='*80}")
    print(f"TEST: AA Extraction v2 (Discriminated Union Model)")
    print(f"{'='*80}")
    print(f"Document: {pdf_path.name}")
    print(f"Page: {page_num + 1}")
    print(f"Model: gpt-5-nano")
    print()

    # Load prompt
    aa_prompt = load_prompt("aa_extraction_v2.txt")

    # Extract page as image
    doc = pymupdf.open(pdf_path)
    page = doc[page_num]
    pix = page.get_pixmap(dpi=150)
    img_data = pix.tobytes("png")
    img_base64 = base64.b64encode(img_data).decode('utf-8')
    doc.close()

    # Call API
    client = OpenAI(api_key=settings.openai_api_key)

    content = [
        {"type": "text", "text": aa_prompt},
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{img_base64}"}
        }
    ]

    print("Calling GPT-5-nano...")
    response = client.chat.completions.create(
        model="gpt-5-nano",
        messages=[{"role": "user", "content": content}],
        max_completion_tokens=16000
    )

    # Parse JSON response
    raw_json = response.choices[0].message.content
    print(f"\n{'='*80}")
    print("RAW JSON RESPONSE:")
    print(f"{'='*80}")
    print(raw_json)
    print()

    elections_data = json.loads(raw_json)

    # Validate with Pydantic models
    print(f"{'='*80}")
    print("PYDANTIC VALIDATION:")
    print(f"{'='*80}")

    validated_elections = []
    for i, election_data in enumerate(elections_data):
        try:
            # Determine election type from "kind" field
            kind = election_data.get("kind")

            if kind == "text":
                election = TextElection(**election_data)
            elif kind == "single_select":
                election = SingleSelectElection(**election_data)
            elif kind == "multi_select":
                election = MultiSelectElection(**election_data)
            else:
                print(f"✗ Election {i+1}: Unknown kind '{kind}'")
                continue

            validated_elections.append(election)
            print(f"✓ Election {i+1} ({kind}): {election.question_number} - {election.status}")
            print(f"  Question: {election.question_text[:60]}...")

            if kind == "text":
                print(f"  Value: {election.value if election.value else '[blank]'}")
            elif kind == "single_select":
                num_options = len(election.options)
                num_selected = 1 if election.value.option_id else 0
                print(f"  Options: {num_selected}/{num_options} selected")
            elif kind == "multi_select":
                num_options = len(election.options)
                num_selected = len(election.value.option_ids)
                print(f"  Options: {num_selected}/{num_options} selected")

        except ValidationError as e:
            print(f"✗ Election {i+1}: Validation failed")
            print(f"  Errors: {e}")

    print(f"\n{'='*80}")
    print(f"SUMMARY:")
    print(f"{'='*80}")
    print(f"Total elections extracted: {len(elections_data)}")
    print(f"Successfully validated: {len(validated_elections)}")
    print()

    # Count by kind and status
    kind_counts = {}
    status_counts = {}
    for election in validated_elections:
        kind_counts[election.kind] = kind_counts.get(election.kind, 0) + 1
        status_counts[election.status] = status_counts.get(election.status, 0) + 1

    print("By kind:")
    for kind, count in kind_counts.items():
        print(f"  {kind}: {count}")

    print("\nBy status:")
    for status, count in status_counts.items():
        print(f"  {status}: {count}")

    # Save validated output
    output_path = Path("test_data/extracted_vision/test_aa_v2_page.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_data = {
        "document": str(pdf_path),
        "page": page_num + 1,
        "model": "gpt-5-nano",
        "prompt_version": "aa_extraction_v2.txt",
        "elections": [e.model_dump() for e in validated_elections]
    }

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\nOutput saved to: {output_path}")
    print(f"{'='*80}\n")

    return validated_elections


def main():
    """Test on source AA first page"""
    sys.stdout.reconfigure(line_buffering=True)

    pdf_path = Path("test_data/raw/source/aa/source_aa.pdf")
    page_num = 1  # Page 2 (0-indexed) - skip cover page

    if not pdf_path.exists():
        print(f"ERROR: PDF not found: {pdf_path}")
        return

    try:
        elections = extract_aa_page(pdf_path, page_num)

        # Additional analysis
        print("\nDETAILED ELECTION ANALYSIS:")
        print("="*80)

        for i, election in enumerate(elections):
            print(f"\n--- Election {i+1}: {election.id} ---")
            print(f"Question: {election.question_text}")
            print(f"Kind: {election.kind}")
            print(f"Status: {election.status} (confidence: {election.confidence})")
            print(f"Section: {election.section_context}")

            if election.kind == "text":
                print(f"Value: {repr(election.value)}")
            elif election.kind == "single_select":
                print(f"Selected option: {election.value.option_id}")
                for opt in election.options:
                    marker = "☑" if opt.is_selected else "☐"
                    print(f"  {marker} {opt.label}. {opt.option_text}")
                    if opt.fill_ins:
                        for fill in opt.fill_ins:
                            print(f"      Fill-in: {fill.question_text} = {repr(fill.value)}")
            elif election.kind == "multi_select":
                print(f"Selected options: {election.value.option_ids}")
                for opt in election.options:
                    marker = "☑" if opt.is_selected else "☐"
                    print(f"  {marker} {opt.label}. {opt.option_text}")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
