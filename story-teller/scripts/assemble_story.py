#!/usr/bin/env python3
"""Assemble the final story with frontmatter and metadata.

Usage:
    echo '{"prompt":"...","story":"...","n_chapters":3,"max_words":500}' | python assemble_story.py --stdin --output story.md
    python assemble_story.py --prompt "..." --story-file /path/to/story.txt --output story.md
"""

import argparse
import json
import sys
from datetime import datetime, timezone


def assemble_story(
    prompt: str,
    story: str,
    n_chapters: int,
    max_words: int,
) -> str:
    """Assemble final story markdown with frontmatter."""

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%Y-%m-%d %H:%M UTC")

    # Generate a title from the first line or premise
    title_line = prompt.split(".")[0].strip()[:80]

    frontmatter = f"""---
type: story
title: "{title_line}"
date: {date_str}
chapters: {n_chapters}
max_words_per_chapter: {max_words}
generated_by: oci1hermes/story-teller
tags:
  - story
  - creative
  - fiction
---"""

    report = f"""{frontmatter}

# {title_line}

> **Generated:** {time_str} | **Chapters:** {n_chapters} | **~{max_words} words/chapter**

**Original Premise:** {prompt}

---

{story.strip()}

---

## Generation Metadata

| Parameter | Value |
|-----------|-------|
| Prompt | {prompt[:100]}{"..." if len(prompt) > 100 else ""} |
| Chapters | {n_chapters} |
| Max Words/Chapter | {max_words} |
| Generated | {time_str} |
| Pipeline | story-teller v1.0.0 |
| Agent | oci1hermes |
"""

    return report


def main():
    parser = argparse.ArgumentParser(description="Assemble story with metadata")
    parser.add_argument("--stdin", action="store_true", help="Read JSON from stdin")
    parser.add_argument("--prompt", help="Original story prompt")
    parser.add_argument("--story-file", help="Path to story text file")
    parser.add_argument("--chapters", type=int, default=3)
    parser.add_argument("--max-words", type=int, default=500)
    parser.add_argument("--output", required=True, help="Output file path")

    args = parser.parse_args()

    if args.stdin:
        data = json.load(sys.stdin)
        prompt = data["prompt"]
        story = data["story"]
        n_chapters = data.get("n_chapters", 3)
        max_words = data.get("max_words", 500)
    else:
        prompt = args.prompt
        with open(args.story_file) as f:
            story = f.read()
        n_chapters = args.chapters
        max_words = args.max_words

    result = assemble_story(prompt, story, n_chapters, max_words)

    with open(args.output, "w") as f:
        f.write(result)

    print(f"Story assembled: {args.output} ({len(result)} chars)")
    sys.exit(0)


if __name__ == "__main__":
    main()
