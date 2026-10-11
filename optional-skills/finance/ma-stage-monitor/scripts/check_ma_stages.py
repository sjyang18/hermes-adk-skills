#!/usr/bin/env python3
"""Monitor Kojiro-style 5/20/40 moving-average stage transitions."""

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import yfinance as yf

DEFAULT_WINDOWS = (5, 20, 40)
DEFAULT_MA_TYPE = "ema"
DEFAULT_INTERVAL = "1d"
SOURCE_URL = "https://fu.minkabu.jp/column/kojiro/78"

STAGE_NAMES = {
    "sml": "Stage 1: Bullish ordering",
    "msl": "Stage 2: Pullback / early consolidation",
    "mls": "Stage 3: Bearish transition",
    "lms": "Stage 4: Bearish ordering",
    "lsm": "Stage 5: Rebound from downtrend",
    "slm": "Stage 6: Bullish transition",
}
STAGE_NUMBERS = {code: number for number, code in enumerate(STAGE_NAMES, 1)}


def validate_windows(windows) -> Tuple[int, int, int]:
    values = tuple(int(value) for value in windows)
    if len(values) != 3 or any(value <= 0 for value in values):
        raise ValueError("ma_windows must contain three positive integers")
    if values != tuple(sorted(values)) or len(set(values)) != 3:
        raise ValueError("ma_windows must be three distinct ascending integers")
    return values


def ma_frame(prices: pd.Series, windows: Tuple[int, int, int], ma_type: str) -> pd.DataFrame:
    """Return short, medium, and long MA series."""
    if ma_type not in {"ema", "sma"}:
        raise ValueError("ma_type must be 'ema' or 'sma'")
    output = {}
    for label, window in zip(("short", "medium", "long"), windows):
        if ma_type == "ema":
            output[label] = prices.ewm(span=window, adjust=False).mean()
        else:
            output[label] = prices.rolling(window).mean()
    return pd.DataFrame(output)


def rank_to_stage(short: float, medium: float, long: float) -> str:
    values = {"s": short, "m": medium, "l": long}
    return "".join(sorted(values, key=values.get, reverse=True))


def fetch_history(ticker: str, interval: str = DEFAULT_INTERVAL) -> pd.DataFrame:
    """Fetch adjusted close history; daily is the recommended primary interval."""
    period = "2y" if interval == "1d" else "10y"
    df = yf.download(
        ticker,
        period=period,
        interval=interval,
        progress=False,
        auto_adjust=True,
    )
    if df.empty:
        raise ValueError(f"No data for {ticker}")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    if "Close" not in df.columns:
        raise ValueError(f"No Close column for {ticker}")
    return df[["Close"]].dropna()


def get_stage_for_date(
    df: pd.DataFrame,
    target_date: pd.Timestamp,
    windows: Tuple[int, int, int] = DEFAULT_WINDOWS,
    ma_type: str = DEFAULT_MA_TYPE,
):
    """Compute stage, MA values, and one-bar slopes through target_date."""
    subset = df[df.index <= target_date]
    if len(subset) < max(windows):
        raise ValueError(
            f"Insufficient data before {target_date.date()}: "
            f"{len(subset)} bars; need {max(windows)}"
        )
    frame = ma_frame(subset["Close"], windows, ma_type)
    current = frame.iloc[-1]
    previous = frame.iloc[-2]
    values = tuple(float(current[label]) for label in ("short", "medium", "long"))
    slopes = tuple(
        float(current[label] - previous[label])
        for label in ("short", "medium", "long")
    )
    return rank_to_stage(*values), values, slopes


def trend_confirmation(stage: str, slopes: Tuple[float, float, float]) -> str:
    """Separate MA ordering from the original method's slope confirmation."""
    if stage == "sml" and all(slope > 0 for slope in slopes):
        return "confirmed_uptrend"
    if stage == "lms" and all(slope < 0 for slope in slopes):
        return "confirmed_downtrend"
    return "ordering_only"


def load_state(path: Path) -> Dict:
    if not path.exists():
        return {}
    with path.open() as handle:
        return json.load(handle)


def save_state(path: Path, state: Dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        json.dump(state, handle, indent=2)


def run_check(
    tickers: List[str],
    state_dir: Path,
    notify_only: bool = False,
    windows: Tuple[int, int, int] = DEFAULT_WINDOWS,
    ma_type: str = DEFAULT_MA_TYPE,
    interval: str = DEFAULT_INTERVAL,
) -> List[Dict]:
    windows = validate_windows(windows)
    ma_type = ma_type.lower()
    methodology = f"{interval}:{ma_type}:{','.join(map(str, windows))}"
    state_file = state_dir / "state.json"
    state = load_state(state_file)
    results = []

    for ticker in tickers:
        try:
            df = fetch_history(ticker, interval)
            if len(df.index) < 2:
                continue
            latest = df.index[-1]
            stage, values, slopes = get_stage_for_date(
                df, latest, windows=windows, ma_type=ma_type
            )
            latest_date = latest.strftime("%Y-%m-%d")
            previous = state.get(ticker)
            same_methodology = bool(
                previous and previous.get("methodology") == methodology
            )
            previous_stage = previous.get("stage") if same_methodology else None
            previous_date = previous.get("date") if same_methodology else None
            transition = bool(
                previous_stage
                and previous_date != latest_date
                and previous_stage != stage
            )
            value_map = {
                str(window): round(value, 2)
                for window, value in zip(windows, values)
            }
            slope_map = {
                str(window): round(slope, 4)
                for window, slope in zip(windows, slopes)
            }
            result = {
                "ticker": ticker,
                "date": latest_date,
                "stage": stage,
                "stage_number": STAGE_NUMBERS[stage],
                "stage_name": STAGE_NAMES[stage],
                "confirmation": trend_confirmation(stage, slopes),
                "interval": interval,
                "ma_type": ma_type,
                "ma_windows": list(windows),
                "ma_values": value_map,
                "ma_slopes": slope_map,
                "prev_stage": previous_stage,
                "prev_stage_number": STAGE_NUMBERS.get(previous_stage),
                "transition": transition,
            }
            state[ticker] = {
                "stage": stage,
                "date": latest_date,
                "methodology": methodology,
                "ma_values": value_map,
                "ma_slopes": slope_map,
                "confirmation": result["confirmation"],
            }
            if not notify_only or transition:
                results.append(result)
        except Exception as exc:
            results.append({"ticker": ticker, "error": str(exc)})

    save_state(state_file, state)
    return results


def parse_args():
    parser = argparse.ArgumentParser(
        description="Kojiro-style 5/20/40 MA stage transitions"
    )
    parser.add_argument("--tickers", help="Comma-separated tickers")
    parser.add_argument("--ticker-file", help="One ticker per line or comma-separated")
    parser.add_argument("--config", help="YAML config path")
    parser.add_argument("--state-dir", help="State directory")
    parser.add_argument("--interval", help="yfinance interval; recommended: 1d")
    parser.add_argument("--ma-type", choices=["ema", "sma"], help="Default: ema")
    parser.add_argument("--output", choices=["json", "table", "csv"])
    parser.add_argument("--notify-only", action="store_true")
    parser.add_argument("--silent-if-none", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    cfg = {}
    if args.config:
        import yaml
        with open(args.config) as handle:
            cfg = yaml.safe_load(handle) or {}

    tickers = [str(ticker).upper() for ticker in cfg.get("tickers", [])]
    if args.tickers:
        tickers.extend(t.strip().upper() for t in args.tickers.split(",") if t.strip())
    if args.ticker_file:
        with open(args.ticker_file) as handle:
            content = handle.read().replace("\n", ",")
        tickers.extend(t.strip().upper() for t in content.split(",") if t.strip())
    tickers = list(dict.fromkeys(tickers))
    if not tickers:
        print("Error: no tickers provided", file=sys.stderr)
        return 1

    windows = validate_windows(cfg.get("ma_windows", DEFAULT_WINDOWS))
    ma_type = args.ma_type or cfg.get("ma_type", DEFAULT_MA_TYPE)
    interval = args.interval or cfg.get("interval", DEFAULT_INTERVAL)
    state_dir = Path(
        args.state_dir or cfg.get("state_dir", "~/.ma-stage-monitor")
    ).expanduser()
    output = args.output or cfg.get("output_format", "table")

    results = run_check(
        tickers,
        state_dir,
        notify_only=args.notify_only,
        windows=windows,
        ma_type=ma_type,
        interval=interval,
    )
    if args.silent_if_none and not results:
        return 0
    if output == "json":
        print(json.dumps(results, indent=2))
    elif output == "csv":
        if results:
            writer = csv.DictWriter(sys.stdout, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    else:
        labels = [f"MA{window}" for window in windows]
        print(
            f"\n{'Ticker':<8} {'Date':<12} {'Stage':<6} "
            f"{labels[0]:>9} {labels[1]:>9} {labels[2]:>9} "
            f"{'Confirm':<20} {'Prev':<6} Change"
        )
        print("-" * 100)
        for result in results:
            if "error" in result:
                print(f"{result['ticker']:<8} ERROR: {result['error']}")
                continue
            values = result["ma_values"]
            change = (
                f"S{result['prev_stage_number']}->S{result['stage_number']}"
                if result["transition"] else ""
            )
            print(
                f"{result['ticker']:<8} {result['date']:<12} {result['stage']:<6} "
                f"{values[str(windows[0])]:>9.2f} "
                f"{values[str(windows[1])]:>9.2f} "
                f"{values[str(windows[2])]:>9.2f} "
                f"{result['confirmation']:<20} "
                f"{result['prev_stage'] or '-':<6} {change}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
