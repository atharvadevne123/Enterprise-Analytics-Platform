#!/usr/bin/env python3
"""Validate that all required environment variables are set.

Reads .env.example to discover required variables and checks
that each is present in the current environment.

Usage:
    python scripts/validate_env.py
    python scripts/validate_env.py --env-file .env.production
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from typing import List, Tuple


def parse_env_example(path: str = ".env.example") -> List[str]:
    """Extract variable names from an .env.example file.

    Args:
        path: Path to the .env.example file.

    Returns:
        List of variable names that have values set (non-empty) in the example.
    """
    variables: List[str] = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                match = re.match(r"^([A-Z_][A-Z0-9_]*)=(.+)$", line)
                if match:
                    variables.append(match.group(1))
    except FileNotFoundError:
        print(f"Warning: {path} not found — skipping validation.")
    return variables


def check_env_vars(variables: List[str]) -> List[Tuple[str, bool]]:
    """Check which variables are set in the current environment.

    Args:
        variables: List of variable names to check.

    Returns:
        List of (variable_name, is_set) tuples.
    """
    return [(var, var in os.environ and bool(os.environ[var])) for var in variables]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate required environment variables")
    parser.add_argument("--env-file", default=".env.example", help="Path to env example file")
    parser.add_argument("--warn-only", action="store_true", help="Warn but don't exit non-zero")
    args = parser.parse_args()

    variables = parse_env_example(args.env_file)
    if not variables:
        print("No variables to check.")
        return 0

    results = check_env_vars(variables)
    missing = [var for var, is_set in results if not is_set]
    present = [var for var, is_set in results if is_set]

    print(f"Checked {len(variables)} variables: {len(present)} set, {len(missing)} missing")

    if missing:
        print("\nMissing variables:")
        for var in missing:
            print(f"  - {var}")
        if not args.warn_only:
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
