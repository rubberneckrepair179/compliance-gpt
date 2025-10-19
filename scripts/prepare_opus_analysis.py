"""
Prepare Document Analysis for Opus 4.1

Generates a report summarizing what we extracted and what we're confused about.
User can provide this + the 4 PDFs to Opus for validation.
"""

import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def load_json(filepath: Path):
    """Load JSON file."""
    with open(filepath, "r") as f:
        return json.load(f)


def main():
    """Generate Opus analysis preparation report."""

    console.print("\n[cyan bold]Document Analysis Preparation for Opus 4.1[/cyan bold]\n")

    # Load our extractions
    source_provs = load_json(Path("test_data/processed/pair_a_source_bpd_operational_provisions.json"))
    target_provs = load_json(Path("test_data/processed/pair_a_target_bpd_operational_provisions.json"))

    # Create summary report
    report = []
    report.append("="*80)
    report.append("DOCUMENT ANALYSIS REQUEST FOR OPUS 4.1")
    report.append("="*80)
    report.append("")
    report.append("CONTEXT:")
    report.append("I'm building an AI tool to compare retirement plan documents during conversions.")
    report.append("I have 4 documents that I categorized as follows:")
    report.append("")
    report.append("  • Document 1: pair_a_source_bpd.pdf (81 pages)")
    report.append("    Assumed: Basic Plan Document (BPD) - SOURCE/OLD document")
    report.append("")
    report.append("  • Document 2: pair_a_target_bpd.pdf (98 pages)")
    report.append("    Assumed: Basic Plan Document (BPD) - TARGET/NEW document")
    report.append("")
    report.append("  • Document 3: pair_b_source_adoption.pdf")
    report.append("    Assumed: Adoption Agreement - SOURCE/OLD")
    report.append("")
    report.append("  • Document 4: pair_b_target_adoption_locked.pdf")
    report.append("    Assumed: Adoption Agreement - TARGET/NEW (password-protected)")
    report.append("")
    report.append("="*80)
    report.append("PROBLEM:")
    report.append("="*80)
    report.append("")
    report.append("My semantic mapping algorithm found 0% matches between Documents 1 and 2.")
    report.append("Even when checking ALL possible pairings, the LLM said 'no match' with 100%")
    report.append("confidence. This makes me suspect I misunderstood the document structure.")
    report.append("")
    report.append("="*80)
    report.append("WHAT I EXTRACTED FROM DOCUMENT 1 (pair_a_source_bpd.pdf):")
    report.append("="*80)
    report.append("")

    for i, prov in enumerate(source_provs, 1):
        report.append(f"{i}. Section {prov['section_reference']}: {prov['section_title']}")
        report.append(f"   Type: {prov['provision_type']}")
        report.append(f"   Text: {prov['provision_text'][:200]}...")
        report.append("")

    report.append("="*80)
    report.append("WHAT I EXTRACTED FROM DOCUMENT 2 (pair_a_target_bpd.pdf):")
    report.append("="*80)
    report.append("")

    for i, prov in enumerate(target_provs, 1):
        report.append(f"{i}. Section {prov['section_reference']}: {prov['section_title']}")
        report.append(f"   Type: {prov['provision_type']}")
        report.append(f"   Text: {prov['provision_text'][:200]}...")
        report.append("")

    report.append("="*80)
    report.append("QUESTIONS FOR OPUS:")
    report.append("="*80)
    report.append("")
    report.append("1. DOCUMENT IDENTIFICATION:")
    report.append("   - Did I correctly identify these as BPD documents?")
    report.append("   - Are they from the same vendor or different vendors?")
    report.append("   - Should Document 1 and Document 2 be compared directly, or do they")
    report.append("     require companion Adoption Agreements to be meaningful?")
    report.append("")
    report.append("2. STRUCTURE ANALYSIS:")
    report.append("   For Document 1:")
    report.append("   - Are the eligibility/vesting provisions self-contained with specific")
    report.append("     values, or do they reference an Adoption Agreement?")
    report.append("   - What pages contain the OPERATIONAL eligibility provisions?")
    report.append("   - What pages contain the OPERATIONAL vesting provisions?")
    report.append("")
    report.append("   For Document 2:")
    report.append("   - Same questions as Document 1")
    report.append("   - Why do many provisions say 'as elected in the Adoption Agreement'?")
    report.append("   - Is this a template/prototype document that REQUIRES an Adoption")
    report.append("     Agreement to specify actual plan terms?")
    report.append("")
    report.append("3. SEMANTIC EQUIVALENCE TEST:")
    report.append("   Compare these specific pairs and tell me if they're semantically")
    report.append("   equivalent (same meaning/purpose):")
    report.append("")
    report.append("   a) Doc1 Section 2.01 (Eligibility to Participate)")
    report.append("      vs")
    report.append("      Doc2 Section 3.1 (CONDITIONS OF ELIGIBILITY)")
    report.append("")
    report.append("      Should these match? Why or why not?")
    report.append("")
    report.append("   b) Doc1 Section 4.02 (100 Percent Vesting of Certain Contributions)")
    report.append("      vs")
    report.append("      Doc2 Section 13.5 (VESTING REQUIREMENTS)")
    report.append("")
    report.append("      Should these match? Why or why not?")
    report.append("")
    report.append("4. MISSING MATCHES:")
    report.append("   For each of the 5 provisions I extracted from Document 1, please")
    report.append("   identify the BEST matching provision in Document 2 (if any exists).")
    report.append("   Include the section number and explain why it's a match.")
    report.append("")
    report.append("5. EXTRACTION VALIDATION:")
    report.append("   - Did I extract the right provisions (operational, not definitional)?")
    report.append("   - Are there better/clearer provisions I should have extracted?")
    report.append("   - Did I miss obvious matches because I extracted from the wrong sections?")
    report.append("")
    report.append("6. COMPARISON STRATEGY:")
    report.append("   Given the structure of these documents, what's the correct way to")
    report.append("   compare them for a plan conversion project?")
    report.append("   - BPD to BPD directly?")
    report.append("   - BPD + Adoption Agreement (combined) to BPD + Adoption Agreement?")
    report.append("   - Something else?")
    report.append("")
    report.append("="*80)
    report.append("ADDITIONAL CONTEXT:")
    report.append("="*80)
    report.append("")
    report.append("My algorithm uses:")
    report.append("1. OpenAI text-embedding-3-small to create vector embeddings (cosine similarity)")
    report.append("2. GPT-4.1 to verify semantic equivalence of top candidates")
    report.append("3. Only provision_text is embedded (no metadata like section numbers)")
    report.append("")
    report.append("Expected outcome: 70-90% of provisions should match (with some variances)")
    report.append("Actual outcome: 0% matches, even when checking all 25 possible pairings")
    report.append("")
    report.append("This suggests either:")
    report.append("- I misidentified the documents (wrong pairing)")
    report.append("- I'm comparing incompatible document types (BPD vs Adoption Agreement)")
    report.append("- The documents genuinely have no semantic overlap (unlikely)")
    report.append("- My LLM is too strict in its matching criteria")
    report.append("")
    report.append("="*80)

    # Output to both console and file
    full_report = "\n".join(report)

    console.print(full_report)

    # Save to file
    output_path = Path("test_data/processed/opus_analysis_request.txt")
    with open(output_path, "w") as f:
        f.write(full_report)

    console.print(f"\n[green]✓ Report saved to:[/green] {output_path}")
    console.print("\n[cyan]Next steps:[/cyan]")
    console.print("1. Copy the 4 PDF files to provide to Opus")
    console.print("2. Copy the questions from opus_analysis_request.txt")
    console.print("3. Ask Opus to analyze all 4 documents and answer the questions")
    console.print("4. Bring back Opus's findings to validate our approach\n")


if __name__ == "__main__":
    main()
