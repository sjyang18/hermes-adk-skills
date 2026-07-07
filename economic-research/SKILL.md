---
name: economic-research
version: 1.0.0
description: Enterprise Market Intelligence Agent — regional economic modeling using free US government APIs (FRED, BLS, BEA, Census, HUD, EIA, FEC). Ported from Google ADK economic-research-agent sample.
category: research
triggers:
  - user asks about regional economic data or metro comparisons
  - user needs site-selection or relocation analysis
  - user wants labor market, housing, or utility cost data
  - user asks about FRED, BLS, Census, HUD, or economic indicators
  - user says "economic research" or "market intelligence"
---

# Economic Research Agent — Enterprise Market Intelligence

A world-class regional economic modeling agent that provides 360-degree analysis for corporate decision-makers. Queries free US government data APIs and synthesizes McKinsey-style executive briefs.

Ported from Google ADK `economic-research-agent` sample — removes GCP/Vertex AI dependency, uses Hermes-native tools.

## Architecture

```
User ↔ Coordinator (this agent)
         │
         ├─ Step 1: Classify Complexity (simple lookup vs. deep analysis)
         │
         ├─ Step 2: Data Collection (delegate_task with terminal toolset)
         │    └─ Executes API calls via scripts/api_tools.py
         │    └─ Sources: FRED, BLS, BEA, Census, HUD, EIA, FEC
         │
         ├─ Step 3: Analysis & Synthesis (delegate_task, pure reasoning)
         │    └─ Cross-source synthesis, comparative tables, executive summary
         │
         └─ Step 4: Audit & Verify (delegate_task with web toolset)
              └─ Judge agent verifies claims against live web data
              └─ Self-corrects if discrepancies found
```

## Prerequisites — API Keys (Optional)

**Keys are NOT required.** The skill works in two modes:

1. **No keys (default)** — Uses `web_search` + `browser` to scrape data directly from government websites (FRED, BLS, Census, etc.). Slightly slower but zero setup.
2. **With keys (faster/structured)** — Direct API calls return clean JSON. Free to register if you want faster, more reliable data.

| API | Key Name | Registration URL |
|-----|----------|-----------------|
| FRED (St. Louis Fed) | `FRED_API_KEY` | https://fredaccount.stlouisfed.org/login/secure/apikeys |
| BEA (Bureau of Economic Analysis) | `BEA_API_KEY` | https://apps.bea.gov/api/signup/index.cfm |
| BLS (Bureau of Labor Statistics) | `BLS_API_KEY` | https://data.bls.gov/registrationEngine/ |
| Census | `CENSUS_API_KEY` | https://api.census.gov/data/key_signup.html |
| HUD (Housing & Urban Dev) | `HUD_API_KEY` | https://www.huduser.gov/portal/dataset/fmr-api.html |
| EIA (Energy Information) | `EIA_API_KEY` | https://www.eia.gov/opendata/register.php |
| FEC (Federal Election Commission) | `FEC_API_KEY` | https://api.open.fec.gov/ |

When no key is available for a source, the agent automatically falls back to web search of that agency's public website.

## Workflow

### Step 0 — Understand the Query

Parse the user's request to identify:
- **Cities/States/Regions** being compared
- **Metrics needed** (unemployment, wages, housing, utilities, taxes, etc.)
- **Industry context** (NAICS codes if relevant)
- **Comparison type** (side-by-side, ranking, trend analysis)

### Step 1 — Classify Complexity

- **Simple** (single metric, single region): Answer directly using one API call
- **Complex** (multi-region comparison, multi-source synthesis): Full pipeline

### Step 2 — Data Collection

**If API keys are available:** Use `delegate_task` with `["terminal"]` toolset to run `scripts/api_tools.py` for structured JSON data.

**If no API keys (default):** Use `delegate_task` with `["web", "browser"]` toolset. The subagent searches government websites directly:

```
Goal: "Find the current unemployment rate for Austin, TX and Raleigh, NC from the Bureau of Labor Statistics and FRED"
Context: [ERA prompt + specific metrics needed + target regions]
Toolsets: ["web", "browser"]
```

Web fallback search targets:
- FRED data → `site:fred.stlouisfed.org {city} unemployment`
- BLS data → `site:bls.gov {state} wages occupational`
- Census → `site:data.census.gov {state} education attainment`
- HUD → `site:huduser.gov {region} fair market rent`
- EIA → `site:eia.gov {state} electricity price`

Each source returns structured data that the synthesis step can consume.

### Step 3 — Analysis & Synthesis

Use `delegate_task` (pure reasoning) with all collected data as context:

```
Goal: "Synthesize this economic data into an executive brief comparing {regions}"
Context: [ERA prompt + all API results + user's original question]
Toolsets: []
```

The synthesis must:
- Use markdown tables for side-by-side comparisons
- Cite data sources (API endpoint + series ID)
- Proactively suggest complementary datasets
- Follow the Consultative Protocol (see prompts.py)

### Step 4 — Audit & Verify (Actor-Critic)

Use `delegate_task` with `["web"]` toolset:

```
Goal: "Verify quantitative claims in this report against live web data"
Context: [Judge prompt + draft report]
Toolsets: ["web"]
```

If the judge finds discrepancies (`[REJECT]` in output):
- Re-run Step 3 with correction context
- Include judge feedback in the retry prompt

### Step 5 — Deliver & Save

1. Deliver the final report (with audit verification note) to user
2. Save to: `~/obsidian-vault/Economic/YYYY-MM-DD-{slug}.md`

## Consultative Protocol

The agent must ALWAYS:
1. **Execute tools immediately** — don't ask permission, fetch data first
2. **Proactively suggest** complementary datasets after answering
3. **Use tables** for all comparative data
4. **Cite sources** with API endpoint URLs
5. **Zero hallucination** — if data unavailable, say so explicitly
6. **Industry context** — suggest relevant NAICS codes when applicable

## Supported Capabilities

| Category | Metrics | API Source |
|----------|---------|-----------|
| Macro Economics | GDP, unemployment, building permits | FRED |
| Labor Market | Wages, labor force, union rates | BLS/FRED |
| Housing | Fair Market Rent, income limits, affordability | HUD |
| Education | Degree attainment, enrollment | Census |
| Energy | Electricity rates (residential/commercial/industrial) | EIA |
| Taxes | State corporate/income tax rates | Tax Foundation (web) |
| Trade | Regional import/export data | BEA |
| Political | Campaign finance, political stability | FEC |

## Pitfalls

1. **API rate limits**: FRED allows 120 req/min. BLS is slower. Space out calls if doing many cities.
2. **MSA codes**: Cities map to Metropolitan Statistical Areas. The FRED skill has a lookup table but falls back to search.
3. **Data freshness**: Government APIs can be 1-3 months behind. Note the "Latest Date" in results.
4. **Missing keys**: Always check for key presence before calling. Provide registration link if missing.
5. **State vs City**: Some APIs work at state level (EIA, Census), others at MSA/city level (FRED, HUD). Don't mix.
