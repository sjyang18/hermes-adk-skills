#!/usr/bin/env python3
"""
Deep Search — Save research report to Obsidian vault with frontmatter.
Usage: python save_report.py --topic "Topic" --report /path/to/report.md
"""

import argparse
import os
import re
import sys
from datetime import datetime


def slugify(text: str, max_len: int = 50) -> str:
    """Convert text to a filesystem-safe slug."""
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[\s_]+', '-', slug).strip('-')
    return slug[:max_len]


def save_report(topic: str, report_content: str, vault_dir: str = None) -> str:
    """Save report to Obsidian vault with YAML frontmatter."""
    if vault_dir is None:
        vault_dir = os.path.expanduser("~/obsidian-vault/Research")

    os.makedirs(vault_dir, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    slug = slugify(topic)
    filename = f"{date_str}-{slug}.md"
    filepath = os.path.join(vault_dir, filename)

    frontmatter = f"""---
type: deep-search-report
topic: "{topic}"
date: {date_str}
tags: [research, deep-search, auto-generated]
---

"""

    full_content = frontmatter + report_content

    with open(filepath, 'w') as f:
        f.write(full_content)

    return filepath


def main():
    parser = argparse.ArgumentParser(description="Save deep-search report to Obsidian vault")
    parser.add_argument('--topic', required=True, help='Research topic')
    parser.add_argument('--report', required=True, help='Path to report markdown file')
    parser.add_argument('--vault-dir', default=None, help='Vault directory (default: ~/obsidian-vault/Research)')

    args = parser.parse_args()

    if not os.path.exists(args.report):
        print(f"ERROR: Report file not found: {args.report}", file=sys.stderr)
        sys.exit(1)

    with open(args.report, 'r') as f:
        report_content = f.read()

    filepath = save_report(args.topic, report_content, args.vault_dir)
    print(f"Saved: {filepath}")


if __name__ == "__main__":
    main()
