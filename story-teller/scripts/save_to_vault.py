#!/usr/bin/env python3
"""Save assembled story to Obsidian vault.

Usage:
    python save_to_vault.py --story /path/to/story.md --title "my-story"

Saves to: ~/obsidian-vault/stories/YYYY-MM-DD-title-slug.md
"""

import argparse
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


VAULT_BASE = Path.home() / "obsidian-vault"
STORIES_DIR = VAULT_BASE / "stories"


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text[:50].rstrip('-')


def save_to_vault(story_path: str, title: str, vault_dir: str = None) -> str:
    """Save story to Obsidian vault."""
    target_dir = Path(vault_dir) if vault_dir else STORIES_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = slugify(title)
    filename = f"{date_str}-{slug}.md"
    target_path = target_dir / filename

    # Handle duplicates
    if target_path.exists():
        base = f"{date_str}-{slug}"
        i = 2
        while (target_dir / f"{base}-{i}.md").exists():
            i += 1
        filename = f"{base}-{i}.md"
        target_path = target_dir / filename

    shutil.copy2(story_path, target_path)
    return str(target_path)


def main():
    parser = argparse.ArgumentParser(description="Save story to Obsidian vault")
    parser.add_argument("--story", required=True, help="Path to story markdown")
    parser.add_argument("--title", required=True, help="Story title for filename")
    parser.add_argument("--vault-dir", help="Override vault directory (for testing)")

    args = parser.parse_args()

    if not os.path.exists(args.story):
        print(f"Error: Story file not found: {args.story}", file=sys.stderr)
        sys.exit(1)

    saved_path = save_to_vault(args.story, args.title, args.vault_dir)
    print(f"Saved to vault: {saved_path}")
    sys.exit(0)


if __name__ == "__main__":
    main()
