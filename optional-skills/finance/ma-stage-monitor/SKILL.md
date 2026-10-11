---
name: ma-stage-monitor
description: Detect 5/20/40 MA stage transitions for a ticker list.
version: 0.3.0
author: Seokwon Yang (sjyang18), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [finance, ma, moving-average, stage, transitions, monitor]
    related_skills: []
---

# MA Stage Monitor Skill

Monitor Kojiro-style moving-average grand-cycle stages. The book-faithful default for US stocks is adjusted daily closes with 5/20/40 EMAs; weekly 5/20/40 is optional higher-timeframe context, not a substitute for the daily signal.

## Source and Method

The primary source is [Kojiro's Moving Average Grand Cycle explanation](https://fu.minkabu.jp/column/kojiro/78). It states:

- Start with 5, 20, and 40 periods across instruments.
- On daily charts these are 5/20/40 days; on weekly charts they are 5/20/40 weeks.
- The parameters are a starting point that may be tuned, but Kojiro uses 5/20/40 across instruments.
- SMA and EMA are both valid; EMA has a slight advantage and is recommended when available.

Market nationality does not justify replacing 40 with 50. A US-style 5/20/50 chart is a separate adaptation and must not be used to validate alerts from the book-based 5/20/40 method.

## Stage Definitions

The stage is determined by MA ordering, where **s=short (5), m=medium (20), l=long (40)**:

| Stage | Code | Rank Order | Interpretation |
|-------|------|------------|----------------|
| 1 | sml | s > m > l | Bullish ordering |
| 2 | msl | m > s > l | Pullback / early consolidation |
| 3 | mls | m > l > s | Bearish transition |
| 4 | lms | l > m > s | Bearish ordering |
| 5 | lsm | l > s > m | Rebound from downtrend |
| 6 | slm | s > l > m | Bullish transition |

Ordering alone defines the stage. Do not call Stage 1 a confirmed uptrend unless all three averages are rising, or Stage 4 a confirmed downtrend unless all three are falling. The script reports `confirmation` separately as `confirmed_uptrend`, `confirmed_downtrend`, or `ordering_only`.

## When to Use

- Daily post-market stage-transition alerts for US stocks
- A stateful watchlist that suppresses duplicate alerts
- Optional weekly confirmation using the same 5/20/40 parameters
- Separate stable core holdings from a frequently edited satellite list

Do not compare daily 5/20/40 alerts against weekly or 5/20/50 charts.

## Prerequisites

- Python 3.10+
- `yfinance`, `pandas`, and `pyyaml`
- Internet access for adjusted market history

Install dependencies through `terminal(command="pip install yfinance pandas pyyaml")` in an isolated environment.

## How to Run

```bash
python scripts/check_ma_stages.py --config config.yaml
python scripts/check_ma_stages.py --tickers "MSFT,AMZN,META" --output json
python scripts/check_ma_stages.py --config config.yaml --notify-only --silent-if-none
```

For the optional higher-timeframe view, use a separate state directory so daily and weekly baselines never collide:

```bash
python scripts/check_ma_stages.py --tickers "MSFT,AMZN" --interval 1wk \
  --state-dir ~/.ma-stage-monitor-weekly
```

## Configuration

```yaml
core_tickers: [META, IVV, MSFT, AMZN, GOOGL, QQQ, SOXX, NVDA, AVGO]
satellite_tickers: [QQQM, LRCX, AEP]
interval: "1d"
ma_type: "ema"
ma_windows: [5, 20, 40]
state_dir: "~/.ma-stage-monitor"
timezone: "America/Los_Angeles"
output_format: "table"
```

Core tickers are listed first and win if a symbol is accidentally duplicated in both lists. The legacy `tickers` key remains supported. The script reads all methodology fields; changing interval, MA type, or windows creates a new silent baseline rather than emitting false transitions against incompatible saved values.

## Procedure

1. Copy `config.example.yaml` to `config.yaml`; keep long-term holdings under `core_tickers` and edit `satellite_tickers` as needed.
2. Keep `interval: "1d"`, `ma_type: "ema"`, and `ma_windows: [5, 20, 40]` for the recommended US-stock monitor.
3. Initialize with `python scripts/check_ma_stages.py --config config.yaml --notify-only --silent-if-none`; empty output confirms a silent baseline.
4. Schedule the same command after the US close. Deliver stdout verbatim; empty stdout means no transition.
5. If weekly context is desired, schedule a second run with `interval: "1wk"` and a different state directory.

## Output

JSON includes the ticker-list membership, interval, MA type, windows, MA values, one-bar slopes, stage, confirmation, previous stage, and transition flag. Table output labels each ticker as core or satellite and labels MA columns from the configured windows.

## Pitfalls

- **Wrong timeframe:** `1d` and `1wk` answer different questions; never compare their stage numbers directly.
- **Wrong parameters:** 50-period charts are common in the US but are not the source method's default.
- **Incomplete confirmation:** stage ordering does not prove the averages have the required slopes or that the 20–40 band is expanding.
- **Open bars:** schedule after market close; a live daily or weekly bar can reverse a crossover.
- **Method migration:** the first run after changing methodology silently resets each ticker's baseline.
- **Data differences:** adjusted-close policies and weekly-bar boundaries can produce small provider-to-provider crossover differences.
- **Rate limits:** keep batches reasonable and retry transient yfinance failures.
- **Duplicate membership:** a ticker present in both lists is monitored once and classified as core.

## Verification

- Confirm output says `interval: 1d`, `ma_type: ema`, and windows `[5, 20, 40]`.
- Recompute one ticker from adjusted closes and verify all three EMA values and their ordering.
- Verify Stage 1 is `confirmed_uptrend` only when all three slopes are positive.
- Re-run on the same market date and verify no duplicate transition appears.
- Change one methodology field in a scratch state directory and verify the first run creates a silent baseline.
