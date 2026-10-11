---
name: ma-stage-monitor
description: Detect 5/20/40 MA stage transitions for a ticker list.
version: 0.1.0
author: Seokwon Yang (sjyang18), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [finance, ma, moving-average, stage, transitions, monitor]
    related_skills: []
---

# MA Stage Monitor Skill

Generic, agent-agnostic 5/20/40 simple-moving-average stage transition detector.

## Stage Definitions

Uses the rank convention where **s=5-day MA, m=20-day MA, l=40-day MA** and stage codes reflect descending rank order:

| Stage | Code | Rank Order | Interpretation |
|-------|------|------------|----------------|
| 1 | sml | s > m > l | Strong Uptrend / Trend confirmed — 5 > 20 > 40 |
| 2 | msl | m > s > l | Pullback / Early Consolidation — 20 > 5 > 40 |
| 3 | mls | m > l > s | Base Build / Mid-term Flattening — 20 > 40 > 5 |
| 4 | lms | l > m > s | Downtrend / Bear Alignment — 40 > 20 > 5 |
| 5 | lsm | l > s > m | Rebound from Downtrend — 40 > 5 > 20 |
| 6 | slm | s > l > m | Down to Up Trend Transition — 5 > 40 > 20 |

## When to Use

- You have a list of tickers and want daily post-market stage transition alerts
- You want a stateless or stateful (saved state) design that works on any agent platform (Hermes, Muse, Gemini, plain cron)
- You prefer computing transitions by re-evaluating yesterday vs today from market data, optionally caching state to save API calls

## Prerequisites

- Python 3.10+
- `pip install yfinance pandas pyyaml`
- Internet access for yfinance data

## How to Run

### Standalone (any platform)

```bash
# From config file
python scripts/check_ma_stages.py --config config.yaml

# Direct ticker list
python scripts/check_ma_stages.py --tickers "MSFT,AMZN,META,AVGO,GOOGL,SOXX,QQQM,LRCX"

# From ticker file (one per line or comma-separated)
python scripts/check_ma_stages.py --ticker-file tickers.txt

# Output as JSON for piping
python scripts/check_ma_stages.py --config config.yaml --output json
```

### With Hermes (optional cron integration)

If running in Hermes, you can schedule it via cron:

```bash
# Create a daily job at 17:30 PT weekdays
cronjob_manage action=create prompt="Run MA stage monitor daily after market close" \
  schedule="30 17 * * 1-5" timezone="America/Los_Angeles" \
  command="python /path/to/check_ma_stages.py --config /path/to/config.yaml --output json"
```

The script writes `state.json` to the configured `state_dir` (~/.ma-stage-monitor by default) to cache yesterday's stage and avoid redundant API calls on same-day re-runs.

## Config File (config.yaml)

```yaml
tickers:
  - MSFT
  - AMZN
  - META
  - AVGO
  - GOOGL
  - SOXX
  - QQQM
  - LRCX

ma_windows: [5, 20, 40]
state_dir: "~/.ma-stage-monitor"
timezone: "America/Los_Angeles"
output_format: "table"
```

## Output

Table format (default):

``` 
Ticker   Date         Stage  Name                              MA5     MA20     MA40   Prev   Trans
MSFT     2025-01-15   mls    Stage 3: Base Build / Mid-term Flattening (20>40>5)  420.15  410.20   395.10 msl    ✓
AMZN     2025-01-15   sml    Stage 1: Strong Uptrend (5>20>40) 180.50  175.30   170.10 sml
```

JSON format includes full details for programmatic consumption.

## Procedure

1. Copy `config.example.yaml` to `config.yaml` and edit tickers
2. Install deps: `pip install yfinance pandas pyyaml`
3. Run: `python scripts/check_ma_stages.py --config config.yaml`
4. (Optional) Schedule via your platform's cron/task scheduler

## Pitfalls

- yfinance rate limits: keep ticker list reasonable (<50), script handles retries
- Non-trading days: script uses last two available trading dates automatically
- State file is per-user/directory; multiple agents pointing to same state_dir will share cache
- Insufficient history (<40 bars) for new IPOs will error — filter tickers accordingly

## Verification

- Run manually and confirm output shows expected stage codes
- Check `~/.ma-stage-monitor/state.json` updates after each run
- On a known transition day, verify `transition: true` appears for that ticker