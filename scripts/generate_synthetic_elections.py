"""
Generate synthetic filled elections for source AA.

Fills the 543 unanswered elections in source_aa_elections.json with realistic
values based on the TechCorp Solutions profile from docs/synthetic_election_design.md

Usage:
    python scripts/generate_synthetic_elections.py
"""

import json
import copy
from pathlib import Path
from typing import Dict, Any, List

# TechCorp Solutions Profile
EMPLOYER_PROFILE = {
    "employer_name": "TechCorp Solutions, Inc.",
    "employer_address": "1234 Innovation Drive",
    "employer_city": "Austin",
    "employer_state": "TX",
    "employer_zip": "78701",
    "employer_ein": "12-3456789",
    "plan_name": "TechCorp Solutions 401(k) Plan",
    "plan_number": "001",
    "effective_date": "January 1, 2018",
    "plan_year_end": "December 31",
    "fiscal_year_end": "December 31",
}

# Election filling rules based on question text pattern matching
ELECTION_RULES = {
    # Employer information
    "name of adopting employer": lambda q: EMPLOYER_PROFILE["employer_name"],
    "employer name": lambda q: EMPLOYER_PROFILE["employer_name"],
    "name of employer": lambda q: EMPLOYER_PROFILE["employer_name"],
    "employer address": lambda q: EMPLOYER_PROFILE["employer_address"],
    "employer identification number": lambda q: EMPLOYER_PROFILE["employer_ein"],
    "ein": lambda q: EMPLOYER_PROFILE["employer_ein"],
    "plan name": lambda q: EMPLOYER_PROFILE["plan_name"],
    "name of plan": lambda q: EMPLOYER_PROFILE["plan_name"],
    "plan number": lambda q: EMPLOYER_PROFILE["plan_number"],
    "effective date": lambda q: EMPLOYER_PROFILE["effective_date"],
    "plan year": lambda q: EMPLOYER_PROFILE["plan_year_end"],

    # Plan type (typically option matching)
    "type of plan": "profit sharing",  # Will match option containing this text
    "401(k)": "401(k)",
    "profit sharing": "profit sharing",

    # Safe harbor
    "safe harbor": "yes",
    "basic match": "basic",

    # Auto-enrollment
    "automatic": "yes",
    "qaca": "yes",
    "auto-enrollment": "yes",

    # Eligibility
    "age requirement": "21",
    "minimum age": "21",
    "service requirement": "0",
    "months of service": "0",
    "entry date": "immediate",

    # Compensation
    "w-2": "w-2",
    "compensation": "w-2",

    # Vesting
    "vesting schedule": "6-year graded",
    "vesting": "graded",
    "6-year": "6-year",
    "safe harbor.*vesting": "100",  # Immediate vesting for safe harbor

    # Distributions
    "normal retirement age": "65",
    "in-service": "yes",
    "59": "yes",  # In-service at 59½
    "hardship": "yes",
    "loan": "yes",

    # Common yes/no patterns
    "permitted": "yes",
    "allowed": "yes",
    "will.*make": "yes",
    "elect.*make": "yes",
}


def normalize_text(text: str) -> str:
    """Normalize text for pattern matching"""
    return text.lower().strip()


def matches_pattern(question_text: str, pattern: str) -> bool:
    """Check if question text matches a pattern"""
    import re
    question_lower = normalize_text(question_text)
    pattern_lower = pattern.lower()

    # Try exact substring match first
    if pattern_lower in question_lower:
        return True

    # Try regex match for patterns like "safe harbor.*vesting"
    try:
        if re.search(pattern_lower, question_lower):
            return True
    except re.error:
        pass

    return False


def find_option_by_text(options: List[Dict[str, Any]], search_text: str) -> str | None:
    """Find option ID by searching option_text for search_text"""
    search_lower = normalize_text(search_text)

    for option in options:
        option_text_lower = normalize_text(option["option_text"])
        if search_lower in option_text_lower:
            return option["option_id"]

    return None


def fill_text_election(election: Dict[str, Any]) -> Dict[str, Any]:
    """Fill a text election with synthetic value"""
    question_text = election["question_text"]

    # Check each rule
    for pattern, value_or_func in ELECTION_RULES.items():
        if matches_pattern(question_text, pattern):
            # If it's a function, call it
            if callable(value_or_func):
                value = value_or_func(election)
            else:
                value = value_or_func

            election["status"] = "answered"
            election["value"] = value
            return election

    # Default: leave unanswered for now
    return election


def fill_single_select_election(election: Dict[str, Any]) -> Dict[str, Any]:
    """Fill a single_select election with synthetic choice"""
    question_text = election["question_text"]
    options = election["options"]

    # Check each rule
    for pattern, search_text in ELECTION_RULES.items():
        if matches_pattern(question_text, pattern):
            # Skip if it's a callable (text-only rule)
            if callable(search_text):
                continue

            # Find matching option
            option_id = find_option_by_text(options, search_text)
            if option_id:
                election["status"] = "answered"
                # Initialize value if null
                if not election["value"]:
                    election["value"] = {}
                election["value"]["option_id"] = option_id

                # Update is_selected flags
                for opt in election["options"]:
                    opt["is_selected"] = (opt["option_id"] == option_id)

                return election

    # Default: select first option if it's a yes/no question
    if len(options) == 2:
        first_option_text = normalize_text(options[0]["option_text"])
        if first_option_text in ["yes", "y"]:
            election["status"] = "answered"
            # Initialize value if null
            if not election["value"]:
                election["value"] = {}
            election["value"]["option_id"] = options[0]["option_id"]
            options[0]["is_selected"] = True
            return election

    # Otherwise leave unanswered
    return election


def fill_multi_select_election(election: Dict[str, Any]) -> Dict[str, Any]:
    """Fill a multi_select election with synthetic choices"""
    question_text = election["question_text"]
    options = election["options"]

    # For multi-select, check if any rule patterns match
    # and select ALL matching options
    selected_ids = []

    for pattern, search_text in ELECTION_RULES.items():
        if matches_pattern(question_text, pattern):
            if callable(search_text):
                continue

            option_id = find_option_by_text(options, search_text)
            if option_id and option_id not in selected_ids:
                selected_ids.append(option_id)

    if selected_ids:
        election["status"] = "answered"
        # Initialize value if null
        if not election["value"]:
            election["value"] = {}
        election["value"]["option_ids"] = selected_ids

        # Update is_selected flags
        for opt in election["options"]:
            opt["is_selected"] = (opt["option_id"] in selected_ids)

    # Otherwise leave unanswered
    return election


def fill_election(election: Dict[str, Any]) -> Dict[str, Any]:
    """Fill an election based on its kind"""
    election = copy.deepcopy(election)

    kind = election["kind"]
    if kind == "text":
        return fill_text_election(election)
    elif kind == "single_select":
        return fill_single_select_election(election)
    elif kind == "multi_select":
        return fill_multi_select_election(election)
    else:
        return election


def generate_synthetic_elections(
    input_path: Path,
    output_path: Path
) -> Dict[str, Any]:
    """
    Generate synthetic filled elections from unanswered template.

    Args:
        input_path: Path to source_aa_elections.json
        output_path: Path to output filled elections

    Returns:
        Statistics about filled elections
    """
    # Load unanswered elections
    with open(input_path, 'r') as f:
        data = json.load(f)

    # Fill elections
    filled_aas = []
    stats = {
        "total": len(data["aas"]),
        "filled": 0,
        "unanswered": 0,
        "by_kind": {
            "text": {"total": 0, "filled": 0},
            "single_select": {"total": 0, "filled": 0},
            "multi_select": {"total": 0, "filled": 0}
        }
    }

    for election in data["aas"]:
        filled = fill_election(election)
        filled_aas.append(filled)

        kind = filled["kind"]
        stats["by_kind"][kind]["total"] += 1

        if filled["status"] == "answered":
            stats["filled"] += 1
            stats["by_kind"][kind]["filled"] += 1
        else:
            stats["unanswered"] += 1

    # Create output data
    output_data = {
        "document": "test_data/raw/source/aa/source_aa.pdf",
        "doc_type": "AA",
        "model": "synthetic_v1",
        "profile": "TechCorp Solutions, Inc.",
        "total_pages": data["total_pages"],
        "total_elections": stats["total"],
        "filled_elections": stats["filled"],
        "unanswered_elections": stats["unanswered"],
        "aas": filled_aas
    }

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    return stats


def main():
    """Main entry point"""
    project_root = Path(__file__).parent.parent
    input_path = project_root / "test_data/extracted_vision/source_aa_elections.json"
    output_path = project_root / "test_data/synthetic/source_aa_filled.json"

    print("Generating synthetic filled elections...")
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    print()

    stats = generate_synthetic_elections(input_path, output_path)

    print("✅ Synthetic elections generated")
    print()
    print("Statistics:")
    print(f"  Total elections: {stats['total']}")
    print(f"  Filled: {stats['filled']} ({stats['filled']/stats['total']*100:.1f}%)")
    print(f"  Unanswered: {stats['unanswered']} ({stats['unanswered']/stats['total']*100:.1f}%)")
    print()
    print("By kind:")
    for kind, kind_stats in stats["by_kind"].items():
        total = kind_stats["total"]
        filled = kind_stats["filled"]
        pct = filled / total * 100 if total > 0 else 0
        print(f"  {kind}: {filled}/{total} ({pct:.1f}%)")


if __name__ == "__main__":
    main()
