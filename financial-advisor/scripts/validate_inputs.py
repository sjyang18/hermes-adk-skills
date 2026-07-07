#!/usr/bin/env python3
"""Validate and normalize inputs for the financial advisor pipeline.

Usage:
    python validate_inputs.py --ticker AAPL --risk moderate --period long-term [--prefs "..."]

Exit codes:
    0 = valid, prints normalized JSON to stdout
    1 = validation error, prints error message to stderr
"""

import argparse
import json
import re
import sys

VALID_RISK = {"conservative", "moderate", "aggressive"}
VALID_PERIOD = {"short-term", "medium-term", "long-term"}

# Common ticker typos
TICKER_CORRECTIONS = {
    "APPL": "AAPL",
    "GOGL": "GOOGL",
    "GOOG": "GOOGL",
    "MSFT.": "MSFT",
    "AMZN.": "AMZN",
}


def validate_ticker(ticker: str) -> tuple[bool, str, str]:
    """Validate and normalize a stock ticker symbol.
    
    Returns (is_valid, normalized_ticker, error_message)
    """
    ticker = ticker.strip().upper()
    
    # Check for common typos
    if ticker in TICKER_CORRECTIONS:
        corrected = TICKER_CORRECTIONS[ticker]
        return True, corrected, f"Corrected '{ticker}' → '{corrected}'"
    
    # Basic format: 1-5 uppercase letters, optionally followed by a dot and 1-2 letters
    if not re.match(r'^[A-Z]{1,5}(\.[A-Z]{1,2})?$', ticker):
        return False, ticker, f"Invalid ticker format: '{ticker}'. Expected 1-5 letters (e.g., AAPL, BRK.B)"
    
    return True, ticker, ""


def validate_risk(risk: str) -> tuple[bool, str, str]:
    """Validate risk tolerance."""
    risk = risk.strip().lower()
    if risk in VALID_RISK:
        return True, risk, ""
    
    # Fuzzy match
    for valid in VALID_RISK:
        if risk.startswith(valid[:3]):
            return True, valid, f"Interpreted '{risk}' as '{valid}'"
    
    return False, risk, f"Invalid risk tolerance: '{risk}'. Must be one of: {', '.join(sorted(VALID_RISK))}"


def validate_period(period: str) -> tuple[bool, str, str]:
    """Validate investment period."""
    period = period.strip().lower()
    if period in VALID_PERIOD:
        return True, period, ""
    
    # Aliases
    aliases = {
        "short": "short-term",
        "medium": "medium-term",
        "mid": "medium-term",
        "long": "long-term",
    }
    if period in aliases:
        return True, aliases[period], f"Interpreted '{period}' as '{aliases[period]}'"
    
    return False, period, f"Invalid investment period: '{period}'. Must be one of: {', '.join(sorted(VALID_PERIOD))}"


def validate_all(ticker: str, risk: str, period: str, prefs: str = "") -> dict:
    """Validate all inputs. Returns result dict.
    
    Result has 'valid' (bool), 'inputs' (normalized), 'errors' (list), 'warnings' (list).
    """
    errors = []
    warnings = []
    
    # Validate ticker
    t_valid, t_norm, t_msg = validate_ticker(ticker)
    if not t_valid:
        errors.append(t_msg)
    elif t_msg:
        warnings.append(t_msg)
    
    # Validate risk
    r_valid, r_norm, r_msg = validate_risk(risk)
    if not r_valid:
        errors.append(r_msg)
    elif r_msg:
        warnings.append(r_msg)
    
    # Validate period
    p_valid, p_norm, p_msg = validate_period(period)
    if not p_valid:
        errors.append(p_msg)
    elif p_msg:
        warnings.append(p_msg)
    
    # Normalize preferences
    prefs = prefs.strip() if prefs else "no specific preferences"
    
    return {
        "valid": len(errors) == 0,
        "inputs": {
            "ticker": t_norm,
            "risk_tolerance": r_norm,
            "investment_period": p_norm,
            "execution_preferences": prefs,
        },
        "errors": errors,
        "warnings": warnings,
    }


def main():
    parser = argparse.ArgumentParser(description="Validate financial advisor pipeline inputs")
    parser.add_argument("--ticker", required=True, help="Stock ticker symbol")
    parser.add_argument("--risk", required=True, help="Risk tolerance (conservative/moderate/aggressive)")
    parser.add_argument("--period", required=True, help="Investment period (short-term/medium-term/long-term)")
    parser.add_argument("--prefs", default="", help="Execution preferences (free-form)")
    
    args = parser.parse_args()
    result = validate_all(args.ticker, args.risk, args.period, args.prefs)
    
    if not result["valid"]:
        print(json.dumps(result, indent=2), file=sys.stderr)
        sys.exit(1)
    
    print(json.dumps(result, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
