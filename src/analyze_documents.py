#!/usr/bin/env python3
"""
Document Analysis Script
Analyzes PDFs in test_data/raw to classify them as Source/Target and BPD/AA
Avoids loading full content into context - extracts metadata only
"""

import os
import sys
from pathlib import Path
import pymupdf  # PyMuPDF for PDF handling
import json

def analyze_pdf_metadata(pdf_path: Path) -> dict:
    """Extract metadata and first few pages to classify document"""
    try:
        doc = pymupdf.open(pdf_path)

        # Basic metadata
        metadata = {
            "filename": pdf_path.name,
            "file_size_mb": round(pdf_path.stat().st_size / (1024 * 1024), 2),
            "page_count": len(doc),
            "title": doc.metadata.get("title", ""),
            "author": doc.metadata.get("author", ""),
            "subject": doc.metadata.get("subject", ""),
        }

        # Extract first page text (usually contains document type/title)
        if len(doc) > 0:
            first_page_text = doc[0].get_text()
            metadata["first_page_preview"] = first_page_text[:1000]  # First 1000 chars

            # Look for key identifiers
            text_lower = first_page_text.lower()

            # Check for BPD indicators
            is_bpd = any([
                "basic plan document" in text_lower,
                "bpd" in text_lower and "adoption" not in text_lower[:500],
            ])

            # Check for AA indicators
            is_aa = any([
                "adoption agreement" in text_lower,
                "employer information" in text_lower and "elect" in text_lower,
            ])

            # Check for version/cycle
            has_cycle_3 = "cycle 3" in text_lower or "cycle3" in text_lower
            has_cycle_1 = "cycle 1" in text_lower or "cycle1" in text_lower

            # Check for "blank" template vs filled
            is_blank = "blank" in pdf_path.name.lower() or (
                text_lower.count("___") > 20 or  # Many blank fill-ins
                text_lower.count("[ ]") > 20     # Many unchecked boxes
            )

            metadata["classification"] = {
                "is_bpd": is_bpd,
                "is_aa": is_aa,
                "has_cycle_3": has_cycle_3,
                "has_cycle_1": has_cycle_1,
                "is_blank_template": is_blank,
            }

        doc.close()
        return metadata

    except Exception as e:
        return {
            "filename": pdf_path.name,
            "error": str(e)
        }

def classify_documents(raw_dir: Path):
    """Analyze all PDFs and propose source/target classification"""

    pdf_files = list(raw_dir.glob("*.pdf"))

    if not pdf_files:
        print("No PDF files found in test_data/raw/")
        return

    print(f"Found {len(pdf_files)} PDF files\n")
    print("=" * 80)

    analyses = []
    for pdf_path in sorted(pdf_files):
        print(f"\nAnalyzing: {pdf_path.name}")
        print("-" * 80)

        metadata = analyze_pdf_metadata(pdf_path)
        analyses.append(metadata)

        # Print summary
        print(f"Size: {metadata.get('file_size_mb', 'unknown')} MB")
        print(f"Pages: {metadata.get('page_count', 'unknown')}")

        if "classification" in metadata:
            cls = metadata["classification"]
            print(f"\nClassification:")
            print(f"  BPD: {'YES' if cls['is_bpd'] else 'no'}")
            print(f"  AA: {'YES' if cls['is_aa'] else 'no'}")
            print(f"  Cycle 3: {'YES' if cls['has_cycle_3'] else 'no'}")
            print(f"  Cycle 1: {'YES' if cls['has_cycle_1'] else 'no'}")
            print(f"  Blank Template: {'YES' if cls['is_blank_template'] else 'no'}")

            # Show preview snippet
            preview = metadata.get("first_page_preview", "")
            if preview:
                print(f"\nFirst Page Preview (truncated):")
                print(preview[:300] + "..." if len(preview) > 300 else preview)

        if "error" in metadata:
            print(f"ERROR: {metadata['error']}")

    print("\n" + "=" * 80)
    print("\nPROPOSED CLASSIFICATION:")
    print("=" * 80)

    # Propose source/target based on analysis
    for analysis in analyses:
        filename = analysis["filename"]
        if "classification" not in analysis:
            print(f"\n{filename}: ERROR - Could not classify")
            continue

        cls = analysis["classification"]

        # Determine role
        if cls["is_bpd"] and cls["has_cycle_1"]:
            role = "SOURCE BPD (Cycle 1 / BPD 01)"
        elif cls["is_bpd"] and cls["has_cycle_3"]:
            role = "TARGET BPD (Cycle 3 / BPD 05)"
        elif cls["is_aa"] and cls["is_blank_template"]:
            role = "TARGET AA TEMPLATE (blank Cycle 3)"
        elif cls["is_aa"]:
            role = "SOURCE AA RECORD (filled elections)"
        elif "401(k) Profit Sharing" in filename:
            role = "SOURCE COMPLETE DOCUMENT (BPD+AA merged?)"
        else:
            role = "UNKNOWN - needs manual review"

        print(f"\n{filename}:")
        print(f"  → {role}")

    # Save analysis to JSON
    output_path = Path("test_data/document_analysis.json")
    with open(output_path, "w") as f:
        json.dump(analyses, f, indent=2)

    print(f"\n\nFull analysis saved to: {output_path}")

if __name__ == "__main__":
    raw_dir = Path("test_data/raw")

    if not raw_dir.exists():
        print(f"Error: {raw_dir} does not exist")
        sys.exit(1)

    classify_documents(raw_dir)
