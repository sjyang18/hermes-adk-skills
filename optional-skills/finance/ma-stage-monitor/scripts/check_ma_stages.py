#!/usr/bin/env python3
"""
MA Stage Monitor - Generic, agent-agnostic 5/20/40 MA stage transition detector.

Stage rank mapping (s=5-day, m=20-day, l=40-day):
  Stage 1 sml: s > m > l  (5 > 20 > 40)
  Stage 2 msl: m > s > l  (20 > 5 > 40)
  Stage 3 mls: m > l > s  (20 > 40 > 5)
  Stage 4 lms: l > m > s  (40 > 20 > 5)
  Stage 5 lsm: l > s > m  (40 > 5 > 20)
  Stage 6 slm: s > l > m  (5 > 40 > 20)

Usage:
  python check_ma_stages.py --tickers MSFT,AMZN,META --state-dir ~/.ma-stage-monitor
  python check_ma_stages.py --config config.yaml
"""

import os
import json
import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import pandas as pd
import yfinance as yf


STAGE_RANKS = {
    "sml": (5, 20, 40),   # 5 > 20 > 40
    "msl": (20, 5, 40),   # 20 > 5 > 40
    "mls": (20, 40, 5),   # 20 > 40 > 5
    "lms": (40, 20, 5),   # 40 > 20 > 5
    "lsm": (40, 5, 20),   # 40 > 5 > 20
    "slm": (5, 40, 20),   # 5 > 40 > 20
}

STAGE_NAMES = {
    "sml": "Stage 1: Strong Uptrend (5>20>40)",
    "msl": "Stage 2: Pullback / Early Consolidation (20>5>40)",
    "mls": "Stage 3: Base Build / Mid-term Flattening (20>40>5)",
    "lms": "Stage 4: Downtrend / Bear Alignment (40>20>5)",
    "lsm": "Stage 5: Rebound from Downtrend (40>5>20)",
    "slm": "Stage 6: Down to Up Trend Transition (5>40>20)",
}

STAGE_NUMBERS = {
    "sml": 1,
    "msl": 2,
    "mls": 3,
    "lms": 4,
    "lsm": 5,
    "slm": 6,
}


def compute_mas(prices: pd.Series, windows: Tuple[int, int, int]) -> Tuple[float, float, float]:
    """Compute 5, 20, 40 SMAs from price series."""
    ma5 = prices.rolling(windows[0]).mean().iloc[-1]
    ma20 = prices.rolling(windows[1]).mean().iloc[-1]
    ma40 = prices.rolling(windows[2]).mean().iloc[-1]
    return float(ma5), float(ma20), float(ma40)


def rank_to_stage(ma5: float, ma20: float, ma40: float) -> str:
    """Map three MA values to stage code based on rank ordering."""
    vals = {"s": ma5, "m": ma20, "l": ma40}
    ranked = sorted(vals.keys(), key=lambda k: vals[k], reverse=True)
    code = "".join(ranked)
    return code if code in STAGE_RANKS else "unknown"


def fetch_history(ticker: str, period: str = "6mo") -> pd.DataFrame:
    """Fetch daily OHLCV from yfinance."""
    df = yf.download(ticker, period=period, interval="1d", progress=False, auto_adjust=True)
    if df.empty:
        raise ValueError(f"No data for {ticker}")
    # yfinance returns MultiIndex columns when single ticker; normalize to simple columns
    if isinstance(df.columns, pd.MultiIndex):
        # Drop ticker level if present
        try:
            df.columns = df.columns.get_level_values(0)
        except Exception:
            df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    # Ensure we have Close column
    if "Close" not in df.columns:
        # Try first numeric column
        num_cols = df.select_dtypes(include="number").columns.tolist()
        if not num_cols:
            raise ValueError(f"No numeric Close column for {ticker}")
        df = df.rename(columns={num_cols[0]: "Close"})
    df = df[["Close"]].dropna()
    return df


def get_stage_for_date(df: pd.DataFrame, target_date: pd.Timestamp) -> Tuple[str, Tuple[float, float, float]]:
    """Compute stage as of a specific date (using data up to that date)."""
    subset = df[df.index <= target_date]
    if len(subset) < 40:
        raise ValueError(f"Insufficient data before {target_date.date()}: {len(subset)} bars")
    ma5, ma20, ma40 = compute_mas(subset["Close"], (5, 20, 40))
    stage = rank_to_stage(ma5, ma20, ma40)
    return stage, (ma5, ma20, ma40)


def load_state(state_path: Path) -> Dict:
    if state_path.exists():
        with open(state_path) as f:
            return json.load(f)
    return {}


def save_state(state_path: Path, state: Dict):
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, "w") as f:
        json.dump(state, f, indent=2)


def run_check(tickers: List[str], state_dir: Path, notify_only: bool = False) -> List[Dict]:
    """Main check: returns list of transition dicts."""
    state_file = state_dir / "state.json"
    state = load_state(state_file)
    transitions = []

    for ticker in tickers:
        try:
            df = fetch_history(ticker)
            dates = df.index[-2:]  # last two trading days
            if len(dates) < 2:
                continue

            today = dates[-1]

            # Compute the latest stage, then compare it with persisted state.
            # A new ticker is initialized silently. Re-running on the same
            # trading date never sends a duplicate notification.
            stage_today, (ma5_t, ma20_t, ma40_t) = get_stage_for_date(df, today)
            latest_date = today.strftime("%Y-%m-%d")
            previous = state.get(ticker)
            previous_stage = previous.get("stage") if previous else None
            previous_date = previous.get("date") if previous else None
            has_new_bar = previous_date != latest_date
            transition = bool(
                previous_stage
                and has_new_bar
                and stage_today != previous_stage
            )

            result = {
                "ticker": ticker,
                "date": latest_date,
                "stage": stage_today,
                "stage_number": STAGE_NUMBERS.get(stage_today),
                "stage_name": STAGE_NAMES.get(stage_today, "Unknown"),
                "ma5": round(ma5_t, 2),
                "ma20": round(ma20_t, 2),
                "ma40": round(ma40_t, 2),
                "prev_stage": previous_stage,
                "prev_stage_number": STAGE_NUMBERS.get(previous_stage),
                "transition": transition,
            }

            # Always advance state, including silent baselines and unchanged stages.
            state[ticker] = {
                "stage": stage_today,
                "date": latest_date,
                "ma5": round(ma5_t, 2),
                "ma20": round(ma20_t, 2),
                "ma40": round(ma40_t, 2),
            }

            if not notify_only or transition:
                transitions.append(result)

        except Exception as e:
            transitions.append({
                "ticker": ticker,
                "error": str(e),
            })

    save_state(state_file, state)
    return transitions


def main():
    parser = argparse.ArgumentParser(description="MA Stage Monitor - 5/20/40 stage transitions")
    parser.add_argument("--tickers", help="Comma-separated tickers")
    parser.add_argument("--ticker-file", help="Path to file with tickers (one per line or comma-separated)")
    parser.add_argument("--config", help="Path to YAML config file")
    parser.add_argument("--state-dir", default=os.path.expanduser("~/.ma-stage-monitor"),
                        help="Directory for state file (default: ~/.ma-stage-monitor)")
    parser.add_argument("--output", choices=["json", "table", "csv"], default="table",
                        help="Output format")
    parser.add_argument("--notify-only", action="store_true",
                        help="Only output tickers with a new persisted-state transition")
    parser.add_argument("--silent-if-none", action="store_true",
                        help="Produce no stdout when there are no transitions or errors")
    args = parser.parse_args()

    # Load tickers
    tickers = []
    if args.config:
        import yaml
        with open(args.config) as f:
            cfg = yaml.safe_load(f)
        tickers = cfg.get("tickers", [])
    if args.tickers:
        tickers.extend([t.strip().upper() for t in args.tickers.split(",")])
    if args.ticker_file:
        with open(args.ticker_file) as f:
            content = f.read().replace("\n", ",")
            tickers.extend([t.strip().upper() for t in content.split(",") if t.strip()])

    # Deduplicate preserving order
    seen = set()
    tickers = [t for t in tickers if not (t in seen or seen.add(t))]

    if not tickers:
        print("Error: No tickers provided. Use --tickers, --ticker-file, or --config", file=sys.stderr)
        sys.exit(1)

    state_dir = Path(args.state_dir).expanduser()
    results = run_check(tickers, state_dir, notify_only=args.notify_only)

    if args.silent_if_none and not results:
        return

    # Output
    if args.output == "json":
        print(json.dumps(results, indent=2))
    elif args.output == "csv":
        import csv
        if results:
            writer = csv.DictWriter(sys.stdout, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    else:
        # Table format
        print(f"\n{'Ticker':<8} {'Date':<12} {'Stage':<6} {'Name':<30} {'MA5':>8} {'MA20':>8} {'MA40':>8} {'Prev':<6} {'Trans':<6} {'Change'}")
        print("-" * 130)
        for r in results:
            if "error" in r:
                print(f"{r['ticker']:<8} {'ERROR':<12} {'-':<6} {r['error']:<30}")
            else:
                trans = "✓" if r["transition"] else ""
                if r["transition"]:
                    stage_change = f"S{r['prev_stage_number']}->S{r['stage_number']}"
                else:
                    stage_change = ""
                previous_code = r["prev_stage"] or "-"
                print(f"{r['ticker']:<8} {r['date']:<12} {r['stage']:<6} {r['stage_name']:<30} "
                      f"{r['ma5']:>8.2f} {r['ma20']:>8.2f} {r['ma40']:>8.2f} {previous_code:<6} {trans} {stage_change}")


if __name__ == "__main__":
    main()