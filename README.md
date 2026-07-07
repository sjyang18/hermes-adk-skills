# Hermes ADK Skills

Hermes-native ports of Google ADK agent samples. These are Hermes skills that replicate the multi-agent orchestration patterns from [google/adk-samples](https://github.com/google/adk-samples) without requiring GCP, Vertex AI, or the ADK framework.

## Skills

### 1. Financial Advisor (`financial-advisor/`)
**Ported from:** [google/adk-samples/python/agents/financial-advisor](https://github.com/google/adk-samples/tree/main/python/agents/financial-advisor)

4-stage sequential pipeline for stock/investment analysis:
- **Data Analyst** → Market data, SEC filings, news, sentiment (web + browser)
- **Trading Analyst** → 5+ distinct trading strategies (pure reasoning)
- **Execution Analyst** → Entry/exit/scaling/stop-loss plans (pure reasoning)
- **Risk Analyst** → Comprehensive risk assessment + mitigation (pure reasoning)

**Dependencies:** None (uses `web_search`, `browser`, `delegate_task`)

### 2. Story Teller (`story-teller/`)
**Ported from:** [google/adk-samples/python/agents/story_teller](https://github.com/google/adk-samples/tree/main/python/agents/story_teller)

Multi-agent collaborative story writing:
- Parallel creative subagents for characters, plot, setting
- Iterative drafting and revision
- Final story assembly with editorial polish

**Dependencies:** None (uses `delegate_task`)

### 3. Deep Search (`deep-search/`)
**Ported from:** [google/adk-samples/python/agents/deep-search](https://github.com/google/adk-samples/tree/main/python/agents/deep-search)

A sophisticated multi-stage iterative research agent:
- **Plan** → Creates a 5-point research plan with classified task types
- **Search** → Executes comprehensive web research with source tracking
- **Evaluate** → Quality-gates research with pass/fail grading
- **Refine** → Iteratively improves research (up to 3 loops)
- **Compose** → Produces a polished, inline-cited markdown report

**Dependencies:** None (uses Hermes built-in `web_search`, `browser`, `delegate_task`)

### 4. Economic Research (`economic-research/`)
**Ported from:** [google/adk-samples/python/agents/economic-research-agent](https://github.com/google/adk-samples/tree/main/python/agents/economic-research-agent)

Enterprise Market Intelligence Agent providing:
- Regional economic modeling (McKinsey-style executive briefs)
- Side-by-side metro/state comparisons
- Multi-source data synthesis (FRED, BLS, Census, HUD, EIA, FEC)
- Actor-Critic self-correction (Auditor Judge verifies claims)

**Dependencies:** Free US government API keys (see [prerequisites](economic-research/SKILL.md#prerequisites--api-keys))

## Usage

These skills are designed to be installed in Hermes Agent's skills directory:

```bash
# Copy to your Hermes skills directory
cp -r deep-search/ ~/.hermes/skills/research/
cp -r economic-research/ ~/.hermes/skills/research/
```

Or load directly from this repo path if Hermes has access.

## Architecture Comparison

| Concept | Google ADK | Hermes Port |
|---------|-----------|-------------|
| Agent framework | `google.adk.agents` | Hermes skill + `delegate_task` |
| Sub-agents | `LlmAgent`, `SequentialAgent`, `LoopAgent` | `delegate_task` with specialized prompts |
| Google Search | `google_search` (Gemini grounding) | `web_search` + `browser` + `web_extract` |
| Model | `gemini-2.5-pro` | Any model (Claude, GPT-4, Gemini, etc.) |
| Deployment | GCP Agent Runtime / Cloud Run | Already running via Hermes gateway |
| State management | ADK session state + `output_key` | Natural context flow between delegates |
| Loop control | `LoopAgent` + `EscalationChecker` | Prompt-driven iteration with JSON grading |

## Testing

Each skill has its own test suite:

```bash
cd financial-advisor/scripts && python3 test_pipeline.py
cd story-teller/scripts && python3 test_pipeline.py
cd deep-search/scripts && python3 test_deep_search.py
cd economic-research/scripts && python3 test_economic_research.py
```

## License

Port implementations are original work. Original ADK samples are Apache 2.0 licensed by Google LLC.
