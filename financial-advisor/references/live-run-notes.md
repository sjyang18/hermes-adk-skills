# Financial Advisor Pipeline — Live Run Notes

## First Live Run: GOOGL (2026-07-05)

### Timing & Token Profile

| Stage | Duration | Input Tokens | Output Tokens | Notes |
|-------|----------|--------------|---------------|-------|
| Data Analyst | 2m 44s | 216K | 6K | 15 web_searches + 2 web_extracts |
| Trading Analyst | 1m 16s | 2.7K | 3.7K | Pure reasoning, no tools called |
| Execution Analyst | 2m 19s | 38K | 6.9K | Wrote to file (20K output) |
| Risk Analyst | 2m 21s | 60K | 6.3K | Loaded skill_view + wrote file (21K) |
| **Total pipeline** | **~9 min** | ~317K | ~23K | + assembly <1s |

### Observations

1. **Data Analyst toolset**: Used only `web_search` and `web_extract` (not `browser`). The `['browser', 'web']` toolset still works but web tools were sufficient. Browser availability is insurance for paywalled/JS-heavy sites.

2. **Trading Analyst was tool-free**: Despite being given `['web']` toolset, it made zero tool calls. All reasoning from the market analysis context. Could reduce to `[]` toolset to save input tokens (fewer tool schemas = less prompt overhead).

3. **Execution Analyst wrote to file**: Produced `/home/ubuntu/googl_execution_plan.md` (20,121 bytes, 454 lines). This is the preferred pattern — full output preserved.

4. **Risk Analyst wrote to file**: Produced `/home/ubuntu/googl_risk_assessment.md` (20,936 bytes, 367 lines). Also loaded the financial-advisor skill via skill_view for context.

5. **Data Analyst did NOT write to file**: Output came only via delegate_task summary. Had to reconstruct from summary text for assembly. This is the lossy path — future runs should instruct file output.

6. **Trading Analyst did NOT write to file**: Same issue. Summary was sufficient (complete strategies in summary) but file would be safer.

### Assembly Path

The `assemble_report.py --stdin` path worked perfectly with JSON input. Final report: 53,568 chars, 1,149 lines. Saved to `~/obsidian-vault/Financial/2026-07-05-GOOGL.md`.

### User Interaction Pattern

User provided all inputs in one message: "moderate, medium-term, prefer limit orders. Set these as default."
- Defaults saved to user memory
- Pipeline ran without further interaction
- This is the preferred UX — not the ADK-style interleaved prompting

### Cost Estimate (Claude Opus via Copilot)

~340K input + 23K output tokens. At Anthropic direct pricing (~$15/M in, $75/M out):
- Input: ~$5.10
- Output: ~$1.73
- **Total: ~$6.83 per full pipeline run**

Via Copilot: included in subscription (no marginal cost).

### Improvement Ideas for v1.1

1. Instruct ALL delegates to write output to `~/financial-advisor-run/` directory
2. Add `--run-dir` param to assemble_report.py to read from convention-based paths
3. Consider reducing Trading Analyst toolset to `[]` (saves ~2K tokens on tool schemas)
4. Add `--ticker` to assemble_report.py so it can auto-discover files by convention
5. Consider parallel execution of Stages 3 & 4 (they don't depend on each other's output — Risk Analyst uses Stage 2 output directly)
