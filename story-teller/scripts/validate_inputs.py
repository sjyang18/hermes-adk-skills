#!/usr/bin/env python3
"""Validate inputs for the story teller pipeline.

Usage:
    python validate_inputs.py --prompt "A story about..." [--chapters 3] [--max-words 500]

Exit codes:
    0 = valid, prints normalized JSON to stdout
    1 = validation error, prints error to stderr
"""

import argparse
import json
import sys


def validate_all(prompt: str, chapters: int, max_words: int) -> dict:
    """Validate all inputs."""
    errors = []
    warnings = []

    # Validate prompt
    prompt = prompt.strip()
    if not prompt:
        errors.append("Story prompt cannot be empty.")
    elif len(prompt) < 10:
        warnings.append(f"Prompt is very short ({len(prompt)} chars). Consider providing more detail.")

    # Validate chapters
    if chapters < 1:
        errors.append(f"Chapters must be at least 1, got {chapters}.")
    elif chapters > 10:
        warnings.append(f"High chapter count ({chapters}) will be slow. Consider 3-5.")

    # Validate max_words
    if max_words < 50:
        errors.append(f"Max words must be at least 50, got {max_words}.")
    elif max_words > 2000:
        warnings.append(f"High word count ({max_words}/chapter) may exceed context limits.")

    return {
        "valid": len(errors) == 0,
        "inputs": {
            "prompt": prompt,
            "n_chapters": chapters,
            "max_words": max_words,
        },
        "errors": errors,
        "warnings": warnings,
    }


def main():
    parser = argparse.ArgumentParser(description="Validate story teller inputs")
    parser.add_argument("--prompt", required=True, help="Story idea/premise")
    parser.add_argument("--chapters", type=int, default=3, help="Number of chapters (default: 3)")
    parser.add_argument("--max-words", type=int, default=500, help="Max words per chapter (default: 500)")

    args = parser.parse_args()
    result = validate_all(args.prompt, args.chapters, args.max_words)

    if not result["valid"]:
        print(json.dumps(result, indent=2), file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
