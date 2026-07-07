---
name: story-teller
description: "Multi-agent collaborative story writing: parallel creative/focused writers → critique → edit."
version: 1.0.0
author: oci1hermes
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [creative, writing, story, multi-agent, pipeline]
    related_skills: [financial-advisor]
---

# Story Teller Pipeline

A deterministic multi-agent collaborative story writing pipeline that takes a simple idea and produces a polished multi-chapter story using competing writer agents.

Ported from [Google ADK story_teller sample](https://github.com/google/adk-samples/tree/main/python/agents/story_teller).

## Architecture

```
User Prompt
    │
    ▼
┌─ Prompt Enhancer ─────────────────────────────┐
│  Expand simple idea → full premise             │
└────────────────────────────────────────────────┘
    │
    ▼
┌─ Chapter Loop (N iterations) ─────────────────┐
│                                                │
│  ┌─ Parallel Writers ───────────────────────┐  │
│  │  Creative Writer    Focused Writer       │  │
│  │  (wild, twists)     (logical, consistent)│  │
│  └──────────────────────────────────────────┘  │
│            │                    │               │
│            ▼                    ▼               │
│  ┌─ Critique Agent ─────────────────────────┐  │
│  │  Select best chapter, append to story    │  │
│  └──────────────────────────────────────────┘  │
│                                                │
└────────────────────────────────────────────────┘
    │
    ▼
┌─ Editor Agent ─────────────────────────────────┐
│  Polish, fix flow, add satisfying conclusion   │
└────────────────────────────────────────────────┘
    │
    ▼
Final Story → Deliver + Save to Vault
```

## Trigger Conditions

- User asks to write a story, creative fiction, narrative
- User says "tell me a story about..."
- User provides a story premise or idea

## Required Inputs

| Input | Type | Default | Required |
|-------|------|---------|----------|
| `prompt` | string | — | Yes (the story idea) |
| `n_chapters` | int | 3 | No |
| `max_words` | int | 500 | No |

## Pipeline Steps

### Step 0: Validate Inputs

Run `scripts/validate_inputs.py`:
```
python scripts/validate_inputs.py --prompt "A sci-fi mystery about..." --chapters 3 --max-words 500
```

### Step 1: Prompt Enhancer (delegate_task)

**Toolsets:** `[]` (pure reasoning)

**Goal:** Expand a simple story idea into a rich, detailed premise.

**Context to pass:**
```
TASK: Expand Story Premise

You are a Creative Writing Consultant.
Your goal is to take a simple story idea and expand it into a rich, detailed premise.
Define the setting, key characters (with names and motivations), the inciting incident, the central conflict, and the overall tone.

The premise should be detailed enough to guide multiple chapters of writing.

USER'S STORY IDEA:
{prompt}

OUTPUT: Return *only* the detailed premise text. No meta-commentary.
```

### Step 2: Chapter Loop (repeat N times)

For each chapter (1 to n_chapters):

#### Step 2a: Parallel Writers (delegate_task batch mode)

Run TWO writers in parallel using `delegate_task(tasks=[...])`:

**Creative Writer context:**
```
TASK: Write Chapter {chapter_num}

You are a Wildly Creative Author.
Write the NEXT chapter of the story.
Prioritize: Unexpected plot twists, vivid imagery, and bold narrative choices. Risk-taking is encouraged.

STORY PREMISE:
{enhanced_prompt}

STORY SO FAR:
{current_story}

CONSTRAINTS:
1. Write approximately {max_words} words for this chapter.
2. Your writing style should be easy and engaging to read. Avoid sophisticated language.
3. Start with "Chapter {chapter_num}" as a header.
4. Output ONLY the chapter text. No commentary.
```

**Focused Writer context:**
```
TASK: Write Chapter {chapter_num}

You are a Disciplined, Logical Author.
Write the NEXT chapter of the story.
Prioritize: Logical consistency, narrative flow, and adherence to established character motivations.

STORY PREMISE:
{enhanced_prompt}

STORY SO FAR:
{current_story}

CONSTRAINTS:
1. Write approximately {max_words} words for this chapter.
2. Your writing style should be easy and engaging to read. Avoid sophisticated language.
3. Start with "Chapter {chapter_num}" as a header.
4. Output ONLY the chapter text. No commentary.
```

#### Step 2b: Critique Agent (delegate_task)

**Toolsets:** `[]`

**Context to pass:**
```
TASK: Select Best Chapter

You are a Senior Story Editor.
You have two candidate drafts for Chapter {chapter_num} of a story.
Select the BEST one based on the premise and story so far.

STORY PREMISE:
{enhanced_prompt}

STORY SO FAR:
{current_story}

OPTION A (Creative Writer):
{creative_chapter}

OPTION B (Focused Writer):
{focused_chapter}

TASK:
1. Select either Option A or Option B (the one that best serves the story).
2. Output the selected chapter text ONLY (with "Chapter {chapter_num}" header).
3. Do not add commentary or meta-text.
```

After critique returns, append selected chapter to `current_story`.

### Step 3: Editor Agent (delegate_task)

**Toolsets:** `[]`

**Context to pass:**
```
TASK: Final Story Polish

You are a Fantastic Editor.
You have the completed draft of a short story. Your job is to polish it.
Fix flow issues, typos, and inconsistencies. Improve the ending if necessary. But do not make big changes.

TASKS:
1. Correct chapter numbers if needed.
2. The final chapter may not have a satisfying ending. Add a few sentences to provide a satisfying conclusion.
3. Ensure consistent tone and character voice throughout.
4. Fix any continuity errors.

COMPLETE DRAFT:
{current_story}

OUTPUT: Return *only* the final, polished story.
```

### Step 4: Assemble & Deliver

Run `scripts/assemble_story.py` to add frontmatter and metadata.
Deliver final story to user.
Run `scripts/save_to_vault.py` to persist in Obsidian vault at `obsidian-vault/stories/`.

## Pitfalls

1. **Parallel delegate_task** — Hermes batch mode runs up to 3 concurrent tasks. Two writers fit perfectly.
2. **Context growth** — Each loop iteration adds ~max_words to current_story. For 5 chapters × 500 words, that's ~2500 words of accumulated context. Keep max_words reasonable.
3. **Creative vs Focused** — The ADK version uses temperature (0.9 vs 0.2). In Hermes we can't set temperature on delegates, so we use prompt instructions to control style.
4. **Loop state** — current_story accumulates across iterations. The orchestrator (me) holds this in context between delegate calls.
