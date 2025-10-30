#!/usr/bin/env python3
"""
Analyze AA v5.1 extraction for orphans and page-spanning provisions
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from collections import defaultdict

def main():
    # Load v5.1 extraction
    with open("test_data/extracted_vision_v5.1/relius_aa_provisions.json") as f:
        data = json.load(f)

    provisions = data.get('aas', [])

    print("="*80)
    print("AA V5.1 ORPHAN & PAGE-SPANNING ANALYSIS")
    print("="*80)
    print()

    # Group provisions by parent_section to find orphans
    children_by_parent = defaultdict(list)
    all_section_numbers = set()
    provisions_by_page = defaultdict(list)

    for p in provisions:
        section_num = p.get('section_number', '')
        parent = p.get('parent_section')
        page = p.get('pdf_page')

        if section_num:
            all_section_numbers.add(section_num)

        if parent:
            children_by_parent[parent].append({
                'pdf_page': page,
                'section_number': section_num,
                'section_title': p.get('section_title', '')[:50],
                'local_ordinal': p.get('local_ordinal')
            })

        provisions_by_page[page].append(p)

    # Find orphans - children whose parent_section doesn't exist as a section_number
    orphans = []
    for parent, children in children_by_parent.items():
        if parent not in all_section_numbers:
            orphans.append({
                'missing_parent': parent,
                'children_count': len(children),
                'children': children
            })

    print(f"Total provisions: {len(provisions)}")
    print(f"Unique section_numbers: {len(all_section_numbers)}")
    print(f"Unique parent_sections referenced: {len(children_by_parent)}")
    print()

    print("="*80)
    print(f"ORPHANS: {len(orphans)}")
    print("="*80)
    if orphans:
        print()
        for orphan in orphans[:10]:  # Show first 10
            print(f"Missing parent: '{orphan['missing_parent']}'")
            print(f"Children count: {orphan['children_count']}")
            print(f"Sample children:")
            for child in orphan['children'][:5]:
                print(f"  - Page {child['pdf_page']}: section_number='{child['section_number']}' ordinal={child['local_ordinal']}")
                print(f"    title='{child['section_title']}'")
            print()
    else:
        print("✓ No orphans found!")

    print()
    print("="*80)
    print("PAGE-SPANNING ANALYSIS")
    print("="*80)
    print()

    # Check for provisions that might span pages
    # Heuristic: Look for parents on page N with no children on page N
    page_spanning = []
    for page_num, page_provisions in sorted(provisions_by_page.items()):
        # Find parents on this page
        parents_on_page = [p for p in page_provisions if p.get('section_number') and not p.get('parent_section')]

        for parent in parents_on_page:
            parent_section = parent.get('section_number')

            # Find children of this parent
            children = children_by_parent.get(parent_section, [])

            if children:
                # Check if any children are on different pages
                child_pages = set(c['pdf_page'] for c in children)
                if page_num not in child_pages:
                    # Parent on page N but NO children on page N - likely page-spanning
                    page_spanning.append({
                        'parent_page': page_num,
                        'parent_section': parent_section,
                        'parent_title': parent.get('section_title', '')[:50],
                        'child_pages': sorted(child_pages),
                        'children_count': len(children)
                    })

    print(f"Potential page-spanning provisions: {len(page_spanning)}")
    if page_spanning:
        print()
        for span in page_spanning[:10]:
            print(f"Parent '{span['parent_section']}' on page {span['parent_page']}")
            print(f"  Title: {span['parent_title']}")
            print(f"  Children ({span['children_count']}) on pages: {span['child_pages']}")
            print()
    else:
        print("✓ No obvious page-spanning issues detected")

    print()
    print("="*80)
    print("FRAGMENTATION RECOMMENDATION")
    print("="*80)
    print()

    if orphans or page_spanning:
        print("⚠ RECOMMENDATION: Implement defragmentation post-processing")
        print()
        print("Issues detected:")
        if orphans:
            print(f"  - {len(orphans)} orphaned parent references")
        if page_spanning:
            print(f"  - {len(page_spanning)} provisions with parent on different page than children")
        print()
        print("Defragmentation strategy:")
        print("  1. For orphans: Search adjacent pages for missing parent")
        print("  2. For page-spanning: Merge parent text from previous page if incomplete")
        print("  3. Add 'is_fragment' flag during extraction")
        print("  4. Create defrag script to merge fragments based on section_number continuity")
    else:
        print("✓ No defragmentation needed - clean extraction!")


if __name__ == "__main__":
    main()
