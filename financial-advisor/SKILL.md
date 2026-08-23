---
name: financial-advisor
description: "Multi-agent financial analysis pipeline: market data → trading strategies → execution plan → risk assessment."
version: 1.0.0
author: oci1hermes
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [financial, analysis, multi-agent, pipeline, trading]
    related_skills: [obsidian]
---

# Financial Advisor Pipeline

A deterministic 6-stage multi-agent pipeline that analyzes a stock ticker and produces:
1. Market data analysis (SEC filings, news, sentiment)
2. Trading strategies (5+ tailored to user risk/period)
3. Execution plan (entry/exit/scaling/stop-loss)
4. Risk assessment (comprehensive risk + mitigation)
5. Counter-verification (devil's advocate — challenges the entire thesis)
6. Monitoring sheet (kill-switch conditions + watch indicators)

Ported from [Google ADK financial-advisor sample](https://github.com/google/adk-samples/tree/main/python/agents/financial-advisor).
Enhanced with the 3-step chain of inquiry framework (진단 → 반증 → 모니터링) from Shin Ju-il's AI investing methodology.

**See also:** `references/live-run-notes.md` — timing, token costs, and operational patterns from actual runs.

## Trigger Conditions

- User asks for stock/ticker analysis
- User wants trading strategies or financial analysis
- User says "run financial advisor" or "analyze [TICKER]"

## Required Inputs

Collect ALL inputs upfront before running the pipeline:

| Input | Type | Values | Required |
|-------|------|--------|----------|
| `ticker` | string | Stock symbol (e.g., AAPL, GOOGL) | Yes |
| `risk_tolerance` | enum | conservative, moderate, aggressive | Yes |
| `investment_period` | enum | short-term, medium-term, long-term | Yes |
| `execution_preferences` | string | Free-form (e.g., "prefer limit orders") | No (default: "no specific preferences") |

## Pipeline Steps

### Step 0: Validate Inputs

Run `scripts/validate_inputs.py` with the user's inputs. If validation fails, ask user to correct.

```
python scripts/validate_inputs.py --ticker AAPL --risk moderate --period long-term --prefs "prefer limit orders"
```

### Step 1: Data Analyst (delegate_task)

**Toolsets:** `['browser', 'web']`

**Goal:** Generate a comprehensive market analysis report for the given ticker.

**Context to pass:**
```
TASK: Market Data Analysis for {ticker}

You are a financial data analyst. Generate a comprehensive market analysis report.

PARAMETERS:
- Ticker: {ticker}
- Max data age: 7 days (prioritize recent information)
- Target: 10+ distinct sources

PROCESS:
1. Search for recent SEC filings (8-K, 10-Q, 10-K, Form 4)
2. Search for financial news, earnings, revenue data
3. Search for analyst ratings, price targets, upgrades/downgrades
4. Search for risk factors, material events, leadership changes
5. Search for market sentiment from financial news outlets

Use web_search for discovery, then web_extract or browser to get full article content.
Prioritize sources: major financial news (Reuters, Bloomberg, CNBC, MarketWatch, Yahoo Finance), official SEC.gov filings, company investor relations.

OUTPUT FORMAT (return exactly this structure):

# Market Analysis Report: {ticker}
**Report Date:** [today's date]
**Sources Consulted:** [count]

## Executive Summary
- [3-5 bullet points of critical findings]

## Recent SEC Filings & Regulatory
- [Summary of recent filings, or "No significant recent filings found"]

## News, Performance & Sentiment
### Significant News
- [Major news items]
### Stock Performance Context
- [Recent price trends, volume]
### Market Sentiment
- [Bullish/bearish/neutral + justification]

## Analyst Commentary & Outlook
- [Ratings, price targets, rationale]

## Key Risks & Opportunities
### Risks
- [Bullet list]
### Opportunities
- [Bullet list]

## Key Sources
- [Title] - [Source] - [Date] - [URL]
```

### Step 2: Trading Analyst (delegate_task)

**Toolsets:** `['web']`

**Goal:** Develop 5+ trading strategies based on market analysis.

**Context to pass:**
```
TASK: Develop Trading Strategies

You are a trading strategy analyst. Based on the market analysis below, develop at least 5 distinct trading strategies.

USER PROFILE:
- Risk Tolerance: {risk_tolerance}
- Investment Period: {investment_period}

MARKET ANALYSIS (from Data Analyst):
{data_analyst_output}

REQUIREMENTS:
- Minimum 5 distinct strategies
- Each strategy must align with the user's risk tolerance and investment period
- Cover diverse approaches (e.g., buy-and-hold, value, momentum, income, contrarian)
- Consider different market scenarios (bullish, bearish, neutral)

OUTPUT FORMAT - For each strategy provide:

## Strategy [N]: [Name]

**Description & Rationale:**
[Paragraph explaining the core idea and why it's proposed based on the market analysis]

**Alignment with User Profile:**
- Risk: [How it matches {risk_tolerance}]
- Period: [How it matches {investment_period}]

**Key Indicators to Watch:**
- [Relevant market/company indicators from the analysis]

**Entry Conditions:**
- [Specific conditions signaling entry]

**Exit Conditions / Targets:**
- [Profit targets and stop-loss conditions]

**Primary Risks:**
- [Strategy-specific risks]
```

### Step 3: Execution Analyst (delegate_task)

**Toolsets:** `[]` (pure reasoning)

**Goal:** Create detailed execution plans for the proposed strategies.

**Context to pass:**
```
TASK: Detailed Execution Plan

You are an execution strategy analyst. Create a detailed implementation plan for the trading strategies below.

USER PROFILE:
- Risk Tolerance: {risk_tolerance}
- Investment Period: {investment_period}
- Execution Preferences: {execution_preferences}

PROPOSED STRATEGIES (from Trading Analyst):
{trading_analyst_output}

REQUIRED SECTIONS:

## I. Foundational Execution Philosophy
- How risk tolerance + investment period + preferences shape execution
- Constraints and priorities

## II. Entry Execution Strategy
- Optimal entry conditions & timing
- Order types & placement (limit, market, stop-limit, conditional)
- Initial position sizing & risk allocation (fixed fractional, fixed monetary)
- Initial stop-loss methodology (ATR-based, chart-based, time-based)

## III. Holding & In-Trade Management
- Monitoring frequency and KPIs
- Dynamic stop-loss adjustments (trailing, breakeven moves)
- Handling volatility & drawdowns

## IV. Accumulation (Scaling-In) Strategy
- Conditions & rationale for adding to positions
- Sizing subsequent entries (pyramiding)
- Adjusting overall position risk

## V. Partial Sell (Profit-Taking / Scaling-Out)
- Triggers for partial profits (price targets, risk-reward multiples)
- Order types and portions to sell
- Managing remaining position

## VI. Full Exit Strategy
- Conditions for profitable exit (trend exhaustion, final target)
- Conditions for loss exit (stop-loss protocol, thesis invalidation)
- Slippage & market impact considerations
```

### Step 4: Risk Analyst (delegate_task)

**Toolsets:** `[]` (pure reasoning)

**Goal:** Comprehensive risk evaluation of the entire financial plan.

**Context to pass:**
```
TASK: Comprehensive Risk Assessment

You are a financial risk analyst. Evaluate the overall risk of the proposed financial plan.

USER PROFILE:
- Risk Tolerance: {risk_tolerance}
- Investment Period: {investment_period}
- Execution Preferences: {execution_preferences}

MARKET ANALYSIS:
{data_analyst_output}

TRADING STRATEGIES:
{trading_analyst_output}

EXECUTION PLAN:
{execution_analyst_output}

REQUIRED SECTIONS:

## Executive Summary of Risks
- Critical risks identified (3-5 bullets)
- Overall qualitative risk level: [Low | Medium | High | Very High]

## Market Risks
- Identification (directional, volatility, gap, interest rate, currency)
- Assessment (potential impact related to user risk tolerance)
- Mitigation (stop-losses, position sizing, hedging, diversification)

## Liquidity Risks
- Identification (ability to enter/exit at desired prices)
- Assessment (slippage costs, execution delays)
- Mitigation (limit orders, order splitting, peak hours trading)

## Counterparty & Platform Risks
- Identification (broker insolvency, outages, API failures, cybersecurity)
- Assessment (loss of funds, inability to manage positions)
- Mitigation (regulated brokers, 2FA, backup platforms)

## Operational & Technological Risks
- Identification (connectivity, human error, signal misinterpretation)
- Assessment (impact on execution accuracy)
- Mitigation (redundancy, checklists, alerts, trade logs)

## Strategy-Specific & Model Risks
- Identification (model decay, overfitting, whipsaws, concentration)
- Assessment (performance impact, regime sensitivity)
- Mitigation (dynamic sizing, regime filters, periodic review)

## Psychological Risks
- Identification (FOMO, revenge trading, confirmation bias, overconfidence)
- Assessment (impact on disciplined execution)
- Mitigation (trading journal, loss limits, breaks, pre-defined responses)

## Overall Alignment with User Profile
- How the total risk profile aligns with stated risk tolerance
- Significant residual risks
- Critical trade-offs user must accept
```

### Step 5: Counter-Verification Analyst (delegate_task)

**Toolsets:** `['web']`

**Goal:** Challenge the entire investment thesis — play devil's advocate.

**Context to pass:**
```
TASK: Counter-Verification — Devil's Advocate Analysis

You are a contrarian analyst. Your SOLE purpose is to CHALLENGE the investment thesis below.
Assume the analysis is WRONG and find evidence that supports the OPPOSITE conclusion.

TICKER: {ticker}
USER PROFILE:
- Risk Tolerance: {risk_tolerance}
- Investment Period: {investment_period}

CURRENT INVESTMENT THESIS:
{data_analyst_output}
{trading_analyst_output}

INSTRUCTIONS:
1. Identify the CORE ASSUMPTIONS in the thesis (bullish catalysts, growth narratives, competitive moats)
2. For EACH assumption, search for contradicting evidence using web_search
3. Look specifically for:
   - Bear cases from credible analysts
   - Insider selling patterns
   - Competitive threats not mentioned
   - Macro headwinds ignored
   - Historical precedents where similar theses failed
   - Regulatory/legal risks downplayed
4. Rate the overall thesis vulnerability

CRITICAL RULES:
- Do NOT invent data. If you can't find contradicting evidence, say so.
- Use primary sources (SEC filings, exchange data, official reports) over social media.
- Clearly separate FACTS from your INTERPRETATION.

OUTPUT FORMAT:

## Counter-Verification Report: {ticker}

### Thesis Vulnerability Score: [1-10] (10 = extremely vulnerable)

### Core Assumptions Challenged

#### Assumption 1: [statement from original thesis]
**Contradicting Evidence:**
- [Evidence with source]
**Severity:** [Low | Medium | High | Critical]

[Repeat for each core assumption]

### Bear Case Synthesis
- [Complete counter-narrative — if someone were SHORTING this stock, what would their thesis be?]

### Risks Not Adequately Covered
- [Blind spots in the original analysis]

### Confidence Assessment
- Original thesis strength after counter-verification: [Strengthened | Unchanged | Weakened | Seriously Undermined]
- Recommendation: [Proceed as planned | Reduce position size | Add hedging | Reconsider entirely]

IMPORTANT: Write your COMPLETE output to ~/financial-advisor-run/{ticker}_counter_verification.md using write_file.
```

### Step 6: Monitoring Sheet Generator (delegate_task)

**Toolsets:** `[]` (pure reasoning)

**Goal:** Create a concrete monitoring sheet with kill-switch conditions.

**Context to pass:**
```
TASK: Generate Investment Monitoring Sheet with Kill-Switch Conditions

You are a portfolio monitoring specialist. Create a CONCRETE, ACTIONABLE monitoring sheet
that the investor will use DAILY/WEEKLY to decide whether to hold, adjust, or exit.

TICKER: {ticker}
USER PROFILE:
- Risk Tolerance: {risk_tolerance}
- Investment Period: {investment_period}

FULL ANALYSIS CONTEXT:
Market Analysis: {data_analyst_output}
Trading Strategies: {trading_analyst_output}
Execution Plan: {execution_analyst_output}
Risk Assessment: {risk_analyst_output}
Counter-Verification: {counter_verification_output}

OUTPUT FORMAT:

# 📊 Monitoring Sheet: {ticker}
**Created:** [date]
**Review Frequency:** [Daily / Weekly / Monthly — based on investment_period]

## 🟢 Bullish Indicators (Hold/Add Signals)
| # | Indicator | Current Value | Target/Threshold | Source | Check Frequency |
|---|-----------|---------------|------------------|--------|-----------------|
| 1 | [e.g., Revenue growth rate] | [latest] | [> X%] | [earnings report] | Quarterly |
| 2 | ... | | | | |

## 🔴 Kill-Switch Conditions (MUST EXIT if triggered)
| # | Condition | Threshold | Current Status | Action |
|---|-----------|-----------|----------------|--------|
| 1 | [e.g., Stock drops below 200-day MA] | [specific price] | [OK / WARNING] | Sell 100% |
| 2 | [e.g., Insider selling > $X in 30 days] | [specific amount] | [OK / WARNING] | Sell 50% |
| 3 | [e.g., Debt-to-equity exceeds X] | [ratio] | [OK / WARNING] | Reassess |
| 4 | [e.g., Key competitor announces X] | [event] | [Not triggered] | Hedge |
| 5 | [e.g., Regulatory action against company] | [any SEC action] | [Not triggered] | Sell 100% |

## 🟡 Watch Items (Reassess if triggered)
| # | Item | Why It Matters | What To Do |
|---|------|---------------|------------|
| 1 | [e.g., Fed rate decision] | [impact on sector] | [adjust position size] |
| 2 | ... | | |

## 📅 Macro Calendar (Upcoming Events)
| Date | Event | Expected Impact | Action Plan |
|------|-------|-----------------|-------------|
| [date] | [e.g., Earnings report] | [High] | [Hold through / trim before] |
| [date] | [e.g., FOMC meeting] | [Medium] | [Monitor] |

## 📏 Position Management Rules
- Maximum position size: [% of portfolio]
- Scaling-in increments: [% per add]
- Stop-loss level: [price or % from entry]
- Take-profit levels: [price targets]
- Maximum drawdown tolerance: [%]

## ✅ Weekly Review Checklist
- [ ] Check all Kill-Switch conditions
- [ ] Review Bullish Indicators
- [ ] Check Macro Calendar for upcoming events
- [ ] Update Current Values in tables above
- [ ] Log any thesis changes in notes below

## 📝 Notes
[Space for investor's ongoing observations]

IMPORTANT: Write your COMPLETE output to ~/financial-advisor-run/{ticker}_monitoring_sheet.md using write_file.
```

### Step 7: Assemble & Deliver

Run `scripts/assemble_report.py` to combine all outputs into final markdown.
Then deliver to user in conversation.
Then run `scripts/save_to_vault.py` to persist in Obsidian vault.

## Input Collection

Collect ALL inputs upfront in a single exchange. Do NOT interleave input gathering between pipeline stages (the original ADK flow asks for risk/period after Stage 1 — we skip that). User's defaults are stored in memory; use them when not specified.

## Delegate Output Handling

**Critical pattern**: `delegate_task` returns only a *summary* — not the full output. For reliable assembly, instruct each delegate to write its full output to a known file path:

```
Stage 1 → ~/financial-advisor-run/{ticker}_data_analyst.md
Stage 2 → ~/financial-advisor-run/{ticker}_trading_analyst.md
Stage 3 → ~/financial-advisor-run/{ticker}_execution_analyst.md
Stage 4 → ~/financial-advisor-run/{ticker}_risk_analyst.md
Stage 5 → ~/financial-advisor-run/{ticker}_counter_verification.md
Stage 6 → ~/financial-advisor-run/{ticker}_monitoring_sheet.md
```

Then `assemble_report.py` reads from these files. If a delegate doesn't write a file (happens with web-heavy stages), reconstruct from the delegate summary — but this is lossy and should be avoided.

**Preferred delegate context footer** (add to each stage's context):
```
IMPORTANT: Write your COMPLETE output to ~/financial-advisor-run/{ticker}_[stage].md using write_file.
Return a brief summary in your final response.
```

## Pitfalls

1. **Data Analyst timeout** — Browser navigation can be slow. The sub-agent should prefer web_search + web_extract over browser navigation. Browser is available but use it as fallback for pages that block extraction.
2. **Token limits on delegates** — Each sub-agent output should be 3-8K chars. Structured output format in prompts controls length. Stages 3 & 4 (execution/risk) tend to produce longer output (15-20K) — this is fine since they're pure reasoning.
3. **Context window** — Each stage only receives the prior stage's OUTPUT, not its full tool trace. Pass the file content, not a pointer.
4. **Ticker validation** — validate_inputs.py checks format. Typos like "APPL" should be caught.
5. **Vault directory** — save_to_vault.py creates `~/obsidian-vault/Financial/` if missing.
6. **Summary reconstruction** — If a delegate didn't write to file, the summary from `delegate_task` is your only source. It may be truncated. For stages with `['browser', 'web']` toolsets, the summary is often good enough (3-5K chars). For reasoning-heavy stages, always instruct file output.
7. **Run directory cleanup** — `~/financial-advisor-run/` accumulates files across runs. The assembly script doesn't clean up; consider clearing before each new run.
