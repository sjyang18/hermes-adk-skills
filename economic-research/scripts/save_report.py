#!/usr/bin/env python3
"""
Economic Research Agent — Save report to Obsidian vault with frontmatter.
"""

import argparse
import os
import re
import sys
from datetime import datetime


def slugify(text: str, max_len: int = 50) -> str:
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[\s_]+', '-', slug).strip('-')
    return slug[:max_len]


def save_report(topic: str, report_content: str, regions: list[str] = None, vault_dir: str = None) -> str:
    if vault_dir is None:
        vault_dir = os.path.expanduser("~/obsidian-vault/Economic")

    os.makedirs(vault_dir, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    slug = slugify(topic)
    filename = f"{date_str}-{slug}.md"
    filepath = os.path.join(vault_dir, filename)

    regions_str = ", ".join(regions) if regions else "N/A"
    frontmatter = f"""---
type: economic-research
topic: "{topic}"
regions: [{regions_str}]
date: {date_str}
tags: [economic, market-intelligence, auto-generated]
---

"""
    with open(filepath, 'w') as f:
        f.write(frontmatter + report_content)

    return filepath


def main():
    parser = argparse.ArgumentParser(description="Save economic research report to Obsidian vault")
    parser.add_argument('--topic', required=True)
    parser.add_argument('--report', required=True, help='Path to report markdown file')
    parser.add_argument('--regions', type=str, default="", help='Comma-separated regions')
    parser.add_argument('--vault-dir', default=None)

    args = parser.parse_args()

    if not os.path.exists(args.report):
        print(f"ERROR: Report file not found: {args.report}", file=sys.stderr)
        sys.exit(1)

    with open(args.report, 'r') as f:
        report_content = f.read()

    regions = [r.strip() for r in args.regions.split(",") if r.strip()] if args.regions else []
    filepath = save_report(args.topic, report_content, regions, args.vault_dir)
    print(f"Saved: {filepath}")


if __name__ == "__main__":
    main()
