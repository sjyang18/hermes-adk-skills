---
name: deep-search
version: 1.0.0
description: Multi-stage iterative research agent — plan → search → evaluate → refine → compose cited report. Ported from Google ADK deep-search sample.
category: research
triggers:
  - user asks for deep research on a topic
  - user wants a comprehensive cited report
  - user needs multi-source investigative research
  - user says "deep search" or "research report"
---

# Deep Search — Iterative Research Pipeline

A sophisticated multi-agent research system that creates a research plan, executes iterative web searches with quality evaluation, and produces a comprehensive cited report.

## Architecture

```
User ↔ Coordinator (this agent)
         │
         ├─ Step 1: Plan Generator (delegate_task)
         │    └─ Creates 5-point research plan with [RESEARCH] and [DELIVERABLE] tasks
         │
         ├─ Step 2: User Review (interactive)
         │    └─ Present plan, accept feedback, refine
         │
         ├─ Step 3: Section Planner (delegate_task)
         │    └─ Breaks plan into 4-6 report sections
         │
         ├─ Step 4: Section Researcher (delegate_task)
         │    └─ Executes all [RESEARCH] tasks with web_search + browser
         │    └─ Synthesizes [DELIVERABLE] artifacts
         │
         ├─ Step 5: Iterative Refinement Loop (max 3 iterations)
         │    ├─ Research Evaluator (delegate_task)
         │    │    └─ Grades research pass/fail, generates follow-up queries
         │    └─ Enhanced Search (delegate_task, only if fail)
         │         └─ Executes follow-up queries, integrates new findings
         │
         └─ Step 6: Report Composer (delegate_task)
              └─ Produces final cited markdown report
```

## Workflow

### Step 0 — Collect Input

Ask the user for their research topic/question. Any topic works — technical, financial, scientific, geopolitical, etc.

### Step 1 — Generate Research Plan

Use `delegate_task` with the plan_generator prompt:

```
Goal: "Generate a research plan for: {user_topic}"
Context: [plan_generator_prompt from scripts/prompts.py]
Toolsets: ["web"]
```

The plan should contain:
- 5 action-oriented research goals prefixed with `[RESEARCH]`
- Any implied deliverables prefixed with `[DELIVERABLE][IMPLIED]`

### Step 2 — User Review (HITL)

Present the research plan to the user. Accept feedback:
- If user approves → proceed to Step 3
- If user has modifications → regenerate plan with feedback incorporated
- Modified items get `[MODIFIED]` tag, new items get `[NEW]` tag

### Step 3 — Section Planning

Use `delegate_task` to break the approved plan into a report structure:

```
Goal: "Design a report structure with 4-6 sections for this research plan: {plan}"
Context: [section_planner_prompt from scripts/prompts.py]
Toolsets: []  (pure reasoning)
```

Output: Markdown outline with section names and brief descriptions.

### Step 4 — Deep Research

Use `delegate_task` with browser + web toolsets:

```
Goal: "Execute this research plan with comprehensive web research"
Context: [section_researcher_prompt + plan + report_sections]
Toolsets: ["web", "browser"]
```

The researcher must:
1. For each `[RESEARCH]` task: generate 4-5 search queries, execute all, synthesize
2. For each `[DELIVERABLE]` task: produce the artifact using only gathered data
3. Track all sources with URLs for citation

### Step 5 — Iterative Refinement (max 3 loops)

**5a. Evaluate** — Use `delegate_task`:
```
Goal: "Evaluate research quality and completeness"
Context: [evaluator_prompt + research_findings]
Toolsets: []
```

Output JSON: `{"grade": "pass"|"fail", "comment": "...", "follow_up_queries": [...]}`

**5b. If "fail"** — Use `delegate_task`:
```
Goal: "Execute follow-up research to fill gaps"
Context: [enhanced_search_prompt + evaluation_feedback + existing_findings]
Toolsets: ["web", "browser"]
```

**5c. Loop** — Repeat 5a-5b until "pass" or max 3 iterations reached.

### Step 6 — Compose Final Report

Use `delegate_task`:
```
Goal: "Compose a polished cited report from the research findings"
Context: [report_composer_prompt + plan + findings + sources + report_sections]
Toolsets: []
```

The composer must:
- Follow the report_sections outline structure
- Cite sources inline as `[Source Title](URL)`
- No separate References section — all citations inline
- Professional, comprehensive coverage

### Step 7 — Deliver & Save

1. Deliver the full report to the user in conversation
2. Save to Obsidian vault: `~/obsidian-vault/Research/YYYY-MM-DD-{slug}.md`

Use `scripts/save_report.py` for vault saving with frontmatter.

## Pitfalls

1. **Token limits on delegates**: Research findings can get long. Instruct the researcher to be concise but comprehensive (~5K chars per section max).
2. **Search quality**: Use specific, targeted queries. Avoid vague single-word searches.
3. **Loop control**: If evaluator keeps failing after 3 iterations, accept the research as-is and note gaps in the report.
4. **Source tracking**: The researcher must explicitly note URLs for every claim. Without this, the composer cannot cite.
5. **Browser fallback**: If browser navigation fails on a site, fall back to web_search + web_extract.
