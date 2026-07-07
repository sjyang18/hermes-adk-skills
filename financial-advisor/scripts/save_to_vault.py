#!/usr/bin/env python3
"""Save assembled financial report to Obsidian vault.

Usage:
    python save_to_vault.py --report /path/to/report.md --ticker AAPL

Saves to: ~/obsidian-vault/Financial/YYYY-MM-DD-TICKER.md
Creates the Financial/ directory if it doesn't exist.
"""

import argparse
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


VAULT_BASE = Path.home() / "obsidian-vault"
FINANCIAL_DIR = VAULT_BASE / "financial"


def save_to_vault(report_path: str, ticker: str, vault_dir: str = None) -> str:
    """Save report to Obsidian vault.
    
    Args:
        report_path: Path to the assembled report markdown file
        ticker: Stock ticker symbol (for filename)
        vault_dir: Override vault directory (for testing)
    
    Returns:
        Path to the saved file in the vault
    """
    target_dir = Path(vault_dir) if vault_dir else FINANCIAL_DIR
    
    # Create directory if needed
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename: YYYY-MM-DD-TICKER.md
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filename = f"{date_str}-{ticker.upper()}.md"
    target_path = target_dir / filename
    
    # If file already exists, append a sequence number
    if target_path.exists():
        base = f"{date_str}-{ticker.upper()}"
        i = 2
        while (target_dir / f"{base}-{i}.md").exists():
            i += 1
        filename = f"{base}-{i}.md"
        target_path = target_dir / filename
    
    # Copy report to vault
    shutil.copy2(report_path, target_path)
    
    return str(target_path)


def main():
    parser = argparse.ArgumentParser(description="Save financial report to Obsidian vault")
    parser.add_argument("--report", required=True, help="Path to assembled report markdown")
    parser.add_argument("--ticker", required=True, help="Stock ticker symbol")
    parser.add_argument("--vault-dir", help="Override vault directory (for testing)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.report):
        print(f"Error: Report file not found: {args.report}", file=sys.stderr)
        sys.exit(1)
    
    saved_path = save_to_vault(args.report, args.ticker, args.vault_dir)
    print(f"Saved to vault: {saved_path}")
    sys.exit(0)


if __name__ == "__main__":
    main()
