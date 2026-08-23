#!/usr/bin/env python3
"""Assemble the final financial advisor report from 6 sub-agent outputs.

Usage:
    python assemble_report.py --ticker AAPL --risk moderate --period long-term \
        --data-analyst /path/to/data.md \
        --trading-analyst /path/to/trading.md \
        --execution-analyst /path/to/execution.md \
        --risk-analyst /path/to/risk.md \
        --counter-verification /path/to/counter.md \
        --monitoring-sheet /path/to/monitoring.md \
        --output /path/to/final_report.md

Or pipe JSON via stdin:
    echo '{"ticker":"AAPL",...,"counter_verification":"...","monitoring_sheet":"..."}' | python assemble_report.py --stdin --output report.md
"""

import argparse
import json
import sys
from datetime import datetime, timezone


DISCLAIMER = """⚠️ **Not financial advice.** This is AI-generated analysis for informational purposes only. 
It does not constitute financial advice, investment recommendations, or offers to buy or sell securities. 
Financial markets are subject to risks, and past performance is not indicative of future results. 
Consult a qualified financial advisor before making investment decisions."""


def assemble_report(
    ticker: str,
    risk_tolerance: str,
    investment_period: str,
    execution_preferences: str,
    data_analyst_output: str,
    trading_analyst_output: str,
    execution_analyst_output: str,
    risk_analyst_output: str,
    counter_verification_output: str = "",
    monitoring_sheet_output: str = "",
) -> str:
    """Assemble the final markdown report from all 6 sub-agent outputs."""
    
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%Y-%m-%d %H:%M UTC")
    
    # YAML frontmatter for Obsidian
    frontmatter = f"""---
type: financial-analysis
ticker: {ticker}
date: {date_str}
risk_tolerance: {risk_tolerance}
investment_period: {investment_period}
execution_preferences: "{execution_preferences}"
generated_by: oci1hermes/financial-advisor
tags:
  - financial
  - trading
  - analysis
  - {ticker.lower()}
---"""

    # Build optional sections
    counter_section = ""
    if counter_verification_output.strip():
        counter_section = f"""
---

## 5. Counter-Verification (Devil's Advocate)

{counter_verification_output.strip()}
"""

    monitoring_section = ""
    if monitoring_sheet_output.strip():
        monitoring_section = f"""
---

## 6. Monitoring Sheet & Kill-Switch Conditions

{monitoring_sheet_output.strip()}
"""

    # Main report
    report = f"""{frontmatter}

# Financial Analysis: {ticker}

> **Generated:** {time_str} | **Risk:** {risk_tolerance} | **Horizon:** {investment_period}

{DISCLAIMER}

---

## 1. Market Data Analysis

{data_analyst_output.strip()}

---

## 2. Trading Strategies

{trading_analyst_output.strip()}

---

## 3. Execution Plan

{execution_analyst_output.strip()}

---

## 4. Risk Assessment

{risk_analyst_output.strip()}
{counter_section}{monitoring_section}
---

## Pipeline Metadata

| Parameter | Value |
|-----------|-------|
| Ticker | {ticker} |
| Risk Tolerance | {risk_tolerance} |
| Investment Period | {investment_period} |
| Execution Preferences | {execution_preferences} |
| Generated | {time_str} |
| Pipeline | financial-advisor v2.0.0 |
| Agent | oci1hermes |
| Methodology | 3-step chain of inquiry (진단 → 반증 → 모니터링) |
"""
    
    return report


def main():
    parser = argparse.ArgumentParser(description="Assemble financial advisor report")
    parser.add_argument("--stdin", action="store_true", help="Read all inputs as JSON from stdin")
    parser.add_argument("--ticker", help="Stock ticker")
    parser.add_argument("--risk", help="Risk tolerance")
    parser.add_argument("--period", help="Investment period")
    parser.add_argument("--prefs", default="no specific preferences", help="Execution preferences")
    parser.add_argument("--data-analyst", help="Path to data analyst output file")
    parser.add_argument("--trading-analyst", help="Path to trading analyst output file")
    parser.add_argument("--execution-analyst", help="Path to execution analyst output file")
    parser.add_argument("--risk-analyst", help="Path to risk analyst output file")
    parser.add_argument("--counter-verification", help="Path to counter-verification output file")
    parser.add_argument("--monitoring-sheet", help="Path to monitoring sheet output file")
    parser.add_argument("--output", required=True, help="Output file path")
    
    args = parser.parse_args()
    
    if args.stdin:
        data = json.load(sys.stdin)
        ticker = data["ticker"]
        risk = data["risk_tolerance"]
        period = data["investment_period"]
        prefs = data.get("execution_preferences", "no specific preferences")
        data_out = data["data_analyst"]
        trading_out = data["trading_analyst"]
        execution_out = data["execution_analyst"]
        risk_out = data["risk_analyst"]
        counter_out = data.get("counter_verification", "")
        monitoring_out = data.get("monitoring_sheet", "")
    else:
        ticker = args.ticker
        risk = args.risk
        period = args.period
        prefs = args.prefs
        
        with open(args.data_analyst) as f:
            data_out = f.read()
        with open(args.trading_analyst) as f:
            trading_out = f.read()
        with open(args.execution_analyst) as f:
            execution_out = f.read()
        with open(args.risk_analyst) as f:
            risk_out = f.read()
        
        counter_out = ""
        if args.counter_verification:
            with open(args.counter_verification) as f:
                counter_out = f.read()
        
        monitoring_out = ""
        if args.monitoring_sheet:
            with open(args.monitoring_sheet) as f:
                monitoring_out = f.read()
    
    report = assemble_report(
        ticker=ticker,
        risk_tolerance=risk,
        investment_period=period,
        execution_preferences=prefs,
        data_analyst_output=data_out,
        trading_analyst_output=trading_out,
        execution_analyst_output=execution_out,
        risk_analyst_output=risk_out,
        counter_verification_output=counter_out,
        monitoring_sheet_output=monitoring_out,
    )
    
    with open(args.output, "w") as f:
        f.write(report)
    
    print(f"Report assembled: {args.output} ({len(report)} chars)")
    sys.exit(0)


if __name__ == "__main__":
    main()
