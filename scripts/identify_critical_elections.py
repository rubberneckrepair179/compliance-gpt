"""
Identify critical elections that are referenced by BPD provisions.

Analyzes BPD provisions to find which AA elections are actually used,
then creates a focused list of critical elections to fill.
"""

import json
import re
from pathlib import Path
from typing import Set, Dict, List
from collections import defaultdict

# Critical election topics based on BPD analysis
CRITICAL_TOPICS = {
    # Core plan design
    "plan_identification": [
        "name of adopting employer",
        "employer name",
        "employer identification",
        "ein",
        "plan name",
        "plan number",
        "effective date",
        "plan year"
    ],

    # Plan type
    "plan_type": [
        "type of plan",
        "401(k)",
        "profit sharing",
        "money purchase"
    ],

    # Eligibility
    "eligibility": [
        "age requirement",
        "minimum age",
        "service requirement",
        "months of service",
        "entry date",
        "excluded employees",
        "leased employee"
    ],

    # Compensation
    "compensation": [
        "compensation.*definition",
        "w-2",
        "415 safe harbor"
    ],

    # Contributions
    "contributions": [
        "matching contribution",
        "profit sharing",
        "safe harbor",
        "qaca",
        "automatic enrollment",
        "default.*deferral",
        "catch-up"
    ],

    # Vesting
    "vesting": [
        "vesting schedule",
        "vesting computation",
        "cliff",
        "graded"
    ],

    # Distributions
    "distributions": [
        "normal retirement age",
        "early retirement",
        "in-service",
        "hardship",
        "loan"
    ],

    # Testing and compliance
    "testing": [
        "top-heavy",
        "adp test",
        "acp test"
    ]
}


def find_critical_elections(
    aa_elections_path: Path,
    output_path: Path
) -> Dict[str, any]:
    """
    Identify critical elections that need to be filled.

    Returns dict with critical election IDs organized by topic.
    """
    # Load all elections
    with open(aa_elections_path, 'r') as f:
        data = json.load(f)

    elections = data["aas"]

    # Find elections matching critical topics
    critical_by_topic = defaultdict(list)
    critical_ids = set()

    for election in elections:
        question_text = election["question_text"].lower()
        election_id = election["id"]

        for topic, patterns in CRITICAL_TOPICS.items():
            for pattern in patterns:
                if re.search(pattern.lower(), question_text):
                    critical_by_topic[topic].append({
                        "id": election_id,
                        "question_number": election["question_number"],
                        "question_text": election["question_text"],
                        "kind": election["kind"],
                        "status": election["status"]
                    })
                    critical_ids.add(election_id)
                    break  # Only add to first matching topic

    # Calculate statistics
    stats = {
        "total_elections": len(elections),
        "critical_elections": len(critical_ids),
        "by_topic": {
            topic: len(elections_list)
            for topic, elections_list in critical_by_topic.items()
        }
    }

    # Save results
    output_data = {
        "stats": stats,
        "critical_by_topic": dict(critical_by_topic),
        "critical_ids": sorted(list(critical_ids))
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    return output_data


def main():
    """Main entry point"""
    project_root = Path(__file__).parent.parent
    aa_path = project_root / "test_data/extracted_vision/source_aa_elections.json"
    output_path = project_root / "test_data/synthetic/critical_elections.json"

    print("Identifying critical elections...")
    print(f"Input: {aa_path}")
    print(f"Output: {output_path}")
    print()

    result = find_critical_elections(aa_path, output_path)

    print("✅ Critical elections identified")
    print()
    print(f"Total elections: {result['stats']['total_elections']}")
    print(f"Critical elections: {result['stats']['critical_elections']} "
          f"({result['stats']['critical_elections']/result['stats']['total_elections']*100:.1f}%)")
    print()
    print("By topic:")
    for topic, count in result['stats']['by_topic'].items():
        print(f"  {topic}: {count}")


if __name__ == "__main__":
    main()
