#!/usr/bin/env python3
"""Test suite for the financial advisor pipeline.

Tests:
1. validate_inputs.py — ticker/risk/period validation and normalization
2. assemble_report.py — report assembly from mock sub-agent outputs
3. save_to_vault.py — vault file creation and naming
4. Integration — full pipeline with mock outputs

Run:
    python test_pipeline.py
    python test_pipeline.py -v          # verbose
    python test_pipeline.py TestValidation  # specific class
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Resolve script paths relative to this test file
SCRIPTS_DIR = Path(__file__).parent
VALIDATE_SCRIPT = SCRIPTS_DIR / "validate_inputs.py"
ASSEMBLE_SCRIPT = SCRIPTS_DIR / "assemble_report.py"
SAVE_SCRIPT = SCRIPTS_DIR / "save_to_vault.py"


# --- Mock sub-agent outputs for integration tests ---

MOCK_DATA_ANALYST = """# Market Analysis Report: AAPL
**Report Date:** 2026-07-05
**Sources Consulted:** 8

## Executive Summary
- Apple reported strong Q2 2026 earnings, beating estimates
- Services revenue grew 18% YoY, now 25% of total revenue
- iPhone 17 pre-orders exceeded expectations
- Analyst consensus: Overweight with $245 average price target
- Key risk: China regulatory uncertainty

## Recent SEC Filings & Regulatory
- 10-Q filed June 30, 2026: Revenue $98.2B (up 9% YoY)
- Form 4: CEO Tim Cook sold 50K shares (routine pre-planned)

## News, Performance & Sentiment
### Significant News
- iPhone 17 launch exceeded Wall Street expectations
- Apple Intelligence 2.0 driving upgrade cycle
### Stock Performance Context
- Trading at $228, up 12% YTD
- Volume: 55M avg daily (above 50-day average)
### Market Sentiment
- Bullish — driven by AI integration and services growth

## Analyst Commentary & Outlook
- Morgan Stanley: Overweight, PT $260 (raised from $240)
- Goldman Sachs: Buy, PT $250
- JP Morgan: Neutral, PT $220 (cautious on China)

## Key Risks & Opportunities
### Risks
- China regulatory crackdown on App Store
- Smartphone market saturation in developed markets
- FX headwinds from strong dollar
### Opportunities
- Apple Intelligence driving hardware upgrade supercycle
- Services revenue margin expansion
- AR/VR platform growth (Vision Pro 2)

## Key Sources
- Apple Q2 2026 10-Q - SEC.gov - 2026-06-30
- Morgan Stanley Research Note - 2026-07-02
- CNBC iPhone 17 Launch Coverage - 2026-07-01
"""

MOCK_TRADING_ANALYST = """## Strategy 1: Core Long-Term Buy & Hold with Compounding

**Description & Rationale:**
Given AAPL's consistent revenue growth, expanding services margins, and the AI-driven upgrade cycle, a core buy-and-hold position capitalizes on long-term compounding.

**Alignment with User Profile:**
- Risk: Moderate — established large-cap with predictable cash flows
- Period: Long-term — dividend reinvestment and capital appreciation

**Key Indicators to Watch:**
- Services revenue growth rate (target >15% YoY)
- iPhone unit sales trajectory

**Entry Conditions:**
- Enter on any 5%+ pullback from current levels
- Dollar-cost average monthly

**Exit Conditions / Targets:**
- Re-evaluate if P/E exceeds 35x or revenue growth drops below 3%

**Primary Risks:**
- Valuation compression if growth slows

## Strategy 2: Covered Call Income Strategy

**Description & Rationale:**
Generate income from existing AAPL position by selling OTM calls. Suitable for moderate risk tolerance with long-term holding.

**Alignment with User Profile:**
- Risk: Moderate — caps upside but generates consistent income
- Period: Long-term — enhances total return over time

**Key Indicators to Watch:**
- Implied volatility levels (sell calls when IV > 30%)
- Earnings dates (avoid selling calls into earnings)

**Entry Conditions:**
- Own 100+ shares; sell 30-delta calls 30-45 DTE

**Exit Conditions / Targets:**
- Roll up and out if stock approaches strike
- Let expire worthless and repeat

**Primary Risks:**
- Capped upside during strong rallies

## Strategy 3: Sector Rotation with AAPL Overweight

**Description & Rationale:**
Overweight AAPL within a diversified tech allocation, rotating between growth and value depending on macro conditions.

**Alignment with User Profile:**
- Risk: Moderate — diversified but with conviction position
- Period: Long-term — adjust allocation quarterly

**Key Indicators to Watch:**
- Fed rate decisions, yield curve
- Tech sector relative strength vs S&P 500

**Entry Conditions:**
- Increase allocation when tech RSI < 40
- Reduce when RSI > 75

**Exit Conditions / Targets:**
- Maintain 15-25% portfolio allocation to AAPL

**Primary Risks:**
- Sector-wide correction could amplify losses

## Strategy 4: Value Averaging on Dips

**Description & Rationale:**
Buy more shares when price is below target growth path, buy fewer when above. Systematic approach that exploits volatility.

**Alignment with User Profile:**
- Risk: Moderate — disciplined, rules-based
- Period: Long-term — accumulation over 12+ months

**Key Indicators to Watch:**
- 50-day and 200-day moving averages
- Support levels ($210, $200)

**Entry Conditions:**
- Increase buys on 10%+ corrections from ATH
- Standard DCA on flat/up months

**Exit Conditions / Targets:**
- Hold indefinitely; reduce only for rebalancing

**Primary Risks:**
- Extended bear market could deplete buy-the-dip capital

## Strategy 5: Dividend Growth Focus with DRIP

**Description & Rationale:**
Focus on AAPL's growing dividend ($1.00/share, 15% annual growth rate) with automatic reinvestment for compounding.

**Alignment with User Profile:**
- Risk: Moderate/conservative — dividend provides downside cushion
- Period: Long-term — compounding requires 5+ year horizon

**Key Indicators to Watch:**
- Dividend growth rate (target >10% annually)
- Payout ratio (currently ~15%, very safe)
- Free cash flow generation

**Entry Conditions:**
- Enter at any price; DRIP handles timing
- Add lump sums after 10%+ corrections

**Exit Conditions / Targets:**
- Hold as long as dividend growth rate > 8%
- Re-evaluate if payout ratio exceeds 50%

**Primary Risks:**
- Low initial yield (~0.4%) means income is minimal initially
"""

MOCK_EXECUTION_ANALYST = """## I. Foundational Execution Philosophy

Given moderate risk tolerance and long-term horizon, execution prioritizes:
- Patience over urgency (limit orders preferred)
- Cost minimization (no market orders except emergency exits)
- Systematic allocation (rules-based, not emotional)

## II. Entry Execution Strategy

**Order Types:** Limit orders placed 0.5-1% below current market price
**Position Sizing:** Fixed fractional — risk max 2% of portfolio per new entry
**Initial Stop-Loss:** Chart-based at nearest support level (currently $210), ~8% below entry
**Scaling:** Initial position = 50% of target allocation; remainder via DCA

## III. Holding & In-Trade Management

**Monitoring:** Weekly review of position vs plan
**Trailing Stop:** Move to breakeven after 15% gain; trail at 12% below highest close
**Volatility:** Ignore daily noise; only act on weekly close below key support

## IV. Accumulation Strategy

**Trigger:** Add on 10%+ pullbacks from recent highs with intact fundamentals
**Sizing:** Each add = 25% of initial position size
**Max Position:** Cap at 20% of total portfolio

## V. Partial Sell Strategy

**Trigger:** Sell 25% at 2:1 risk/reward; 25% at 3:1
**Method:** Limit orders at target prices
**Remainder:** Hold with trailing stop on remaining position

## VI. Full Exit Strategy

**Profitable Exit:** When thesis changes (growth < 3%) or valuation extreme (P/E > 40)
**Loss Exit:** If stop-loss triggered (weekly close below $210) — market order at next open
**Slippage:** Minimal concern for AAPL given $50B+ daily volume
"""

MOCK_RISK_ANALYST = """## Executive Summary of Risks
- Concentration risk: Single stock exposure regardless of diversification strategy
- Market risk: Broad tech correction could cause 20-30% drawdown
- Execution risk: Behavioral deviation from plan during volatility
- Overall qualitative risk level: **Medium**

## Market Risks
**Identification:** Directional (bull/bear), volatility, gap risk (earnings), interest rate sensitivity
**Assessment:** A 20% drawdown is historically likely within any 2-year period. Moderate risk tolerance should be comfortable with this.
**Mitigation:** Position sizing (max 20% portfolio), trailing stops, diversification across strategies

## Liquidity Risks
**Identification:** AAPL is among the most liquid stocks globally
**Assessment:** Minimal — daily volume exceeds $10B
**Mitigation:** No special measures needed; standard limit orders sufficient

## Counterparty & Platform Risks
**Identification:** Broker stability, platform outages during high volatility
**Assessment:** Low for major brokers; could miss exit signals during outages
**Mitigation:** Use top-tier regulated broker; set contingent/bracket orders that execute server-side

## Operational & Technological Risks
**Identification:** Human error in order entry, failure to follow plan during drawdowns
**Assessment:** Moderate — most common source of underperformance
**Mitigation:** Pre-set limit orders and alerts; maintain trading journal; quarterly plan review

## Strategy-Specific & Model Risks
**Identification:** Covered call strategy caps upside; DCA underperforms in sustained bull markets
**Assessment:** Moderate — opportunity cost during strong rallies
**Mitigation:** Limit covered calls to 50% of position; accept DCA underperformance as cost of risk management

## Psychological Risks
**Identification:** FOMO during rallies (wanting to add more), panic during corrections (wanting to sell all)
**Assessment:** High impact on returns if not managed
**Mitigation:** Written investment policy statement; scheduled quarterly reviews only; automated execution where possible

## Overall Alignment with User Profile
The combined strategy set is well-aligned with moderate risk tolerance and long-term horizon.
Key trade-off: Accepting lower short-term returns for capital preservation and compounding.
Residual risk: Single-stock concentration even with multiple strategies — consider parallel analysis for 2-3 additional tickers for true diversification.
"""


class TestValidation(unittest.TestCase):
    """Test validate_inputs.py"""
    
    def run_validate(self, ticker, risk, period, prefs=""):
        cmd = [sys.executable, str(VALIDATE_SCRIPT),
               "--ticker", ticker, "--risk", risk, "--period", period]
        if prefs:
            cmd.extend(["--prefs", prefs])
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result
    
    def test_valid_inputs(self):
        """Standard valid inputs should pass."""
        r = self.run_validate("AAPL", "moderate", "long-term")
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertTrue(data["valid"])
        self.assertEqual(data["inputs"]["ticker"], "AAPL")
        self.assertEqual(data["inputs"]["risk_tolerance"], "moderate")
        self.assertEqual(data["inputs"]["investment_period"], "long-term")
    
    def test_ticker_correction(self):
        """Known typo APPL should be corrected to AAPL."""
        r = self.run_validate("APPL", "moderate", "long-term")
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertTrue(data["valid"])
        self.assertEqual(data["inputs"]["ticker"], "AAPL")
        self.assertTrue(any("Corrected" in w for w in data["warnings"]))
    
    def test_ticker_case_insensitive(self):
        """Lowercase ticker should be uppercased."""
        r = self.run_validate("msft", "moderate", "long-term")
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertEqual(data["inputs"]["ticker"], "MSFT")
    
    def test_invalid_ticker(self):
        """Invalid ticker format should fail."""
        r = self.run_validate("123ABC", "moderate", "long-term")
        self.assertNotEqual(r.returncode, 0)
    
    def test_risk_fuzzy_match(self):
        """Partial risk input should be matched."""
        r = self.run_validate("AAPL", "mod", "long-term")
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertEqual(data["inputs"]["risk_tolerance"], "moderate")
    
    def test_period_alias(self):
        """Period aliases should work."""
        r = self.run_validate("AAPL", "moderate", "long")
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertEqual(data["inputs"]["investment_period"], "long-term")
    
    def test_invalid_risk(self):
        """Invalid risk should fail."""
        r = self.run_validate("AAPL", "yolo", "long-term")
        self.assertNotEqual(r.returncode, 0)
    
    def test_invalid_period(self):
        """Invalid period should fail."""
        r = self.run_validate("AAPL", "moderate", "forever")
        self.assertNotEqual(r.returncode, 0)
    
    def test_execution_preferences_default(self):
        """Missing prefs should default to 'no specific preferences'."""
        r = self.run_validate("AAPL", "moderate", "long-term")
        data = json.loads(r.stdout)
        self.assertEqual(data["inputs"]["execution_preferences"], "no specific preferences")
    
    def test_execution_preferences_custom(self):
        """Custom prefs should pass through."""
        r = self.run_validate("AAPL", "moderate", "long-term", "prefer limit orders, Fidelity")
        data = json.loads(r.stdout)
        self.assertEqual(data["inputs"]["execution_preferences"], "prefer limit orders, Fidelity")
    
    def test_brk_b_ticker(self):
        """Ticker with dot notation (BRK.B) should be valid."""
        r = self.run_validate("BRK.B", "conservative", "long-term")
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertEqual(data["inputs"]["ticker"], "BRK.B")


class TestAssembleReport(unittest.TestCase):
    """Test assemble_report.py"""
    
    def test_assemble_from_stdin(self):
        """Assembly from JSON stdin should produce valid markdown."""
        input_data = json.dumps({
            "ticker": "AAPL",
            "risk_tolerance": "moderate",
            "investment_period": "long-term",
            "execution_preferences": "no specific preferences",
            "data_analyst": MOCK_DATA_ANALYST,
            "trading_analyst": MOCK_TRADING_ANALYST,
            "execution_analyst": MOCK_EXECUTION_ANALYST,
            "risk_analyst": MOCK_RISK_ANALYST,
        })
        
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            output_path = f.name
        
        try:
            r = subprocess.run(
                [sys.executable, str(ASSEMBLE_SCRIPT), "--stdin", "--output", output_path],
                input=input_data, capture_output=True, text=True
            )
            self.assertEqual(r.returncode, 0, f"stderr: {r.stderr}")
            
            with open(output_path) as f:
                content = f.read()
            
            # Verify structure
            self.assertIn("---\ntype: financial-analysis", content)
            self.assertIn("ticker: AAPL", content)
            self.assertIn("# Financial Analysis: AAPL", content)
            self.assertIn("## 1. Market Data Analysis", content)
            self.assertIn("## 2. Trading Strategies", content)
            self.assertIn("## 3. Execution Plan", content)
            self.assertIn("## 4. Risk Assessment", content)
            self.assertIn("Not financial advice", content)
            self.assertIn("## Pipeline Metadata", content)
        finally:
            os.unlink(output_path)
    
    def test_assemble_from_files(self):
        """Assembly from individual files should work."""
        tmp_dir = tempfile.mkdtemp()
        
        # Write mock outputs to files
        files = {
            "data.md": MOCK_DATA_ANALYST,
            "trading.md": MOCK_TRADING_ANALYST,
            "execution.md": MOCK_EXECUTION_ANALYST,
            "risk.md": MOCK_RISK_ANALYST,
        }
        for name, content in files.items():
            with open(os.path.join(tmp_dir, name), "w") as f:
                f.write(content)
        
        output_path = os.path.join(tmp_dir, "report.md")
        
        try:
            r = subprocess.run([
                sys.executable, str(ASSEMBLE_SCRIPT),
                "--ticker", "AAPL",
                "--risk", "moderate",
                "--period", "long-term",
                "--data-analyst", os.path.join(tmp_dir, "data.md"),
                "--trading-analyst", os.path.join(tmp_dir, "trading.md"),
                "--execution-analyst", os.path.join(tmp_dir, "execution.md"),
                "--risk-analyst", os.path.join(tmp_dir, "risk.md"),
                "--output", output_path,
            ], capture_output=True, text=True)
            
            self.assertEqual(r.returncode, 0, f"stderr: {r.stderr}")
            self.assertTrue(os.path.exists(output_path))
            
            with open(output_path) as f:
                content = f.read()
            self.assertIn("# Financial Analysis: AAPL", content)
            # Should be substantial
            self.assertGreater(len(content), 5000)
        finally:
            import shutil
            shutil.rmtree(tmp_dir)
    
    def test_frontmatter_valid_yaml(self):
        """Frontmatter should be parseable YAML."""
        import tempfile
        input_data = json.dumps({
            "ticker": "GOOGL",
            "risk_tolerance": "aggressive",
            "investment_period": "short-term",
            "execution_preferences": "market orders OK",
            "data_analyst": "test data",
            "trading_analyst": "test trading",
            "execution_analyst": "test execution",
            "risk_analyst": "test risk",
        })
        
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            output_path = f.name
        
        try:
            subprocess.run(
                [sys.executable, str(ASSEMBLE_SCRIPT), "--stdin", "--output", output_path],
                input=input_data, capture_output=True, text=True
            )
            with open(output_path) as f:
                content = f.read()
            
            # Extract frontmatter
            parts = content.split("---")
            self.assertGreaterEqual(len(parts), 3)
            frontmatter = parts[1]
            self.assertIn("ticker: GOOGL", frontmatter)
            self.assertIn("risk_tolerance: aggressive", frontmatter)
        finally:
            os.unlink(output_path)


class TestSaveToVault(unittest.TestCase):
    """Test save_to_vault.py"""
    
    def test_save_creates_file(self):
        """Should create file in vault directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create a mock report
            report_path = os.path.join(tmp_dir, "report.md")
            with open(report_path, "w") as f:
                f.write("# Test Report\nContent here.")
            
            vault_dir = os.path.join(tmp_dir, "vault", "Financial")
            
            r = subprocess.run([
                sys.executable, str(SAVE_SCRIPT),
                "--report", report_path,
                "--ticker", "AAPL",
                "--vault-dir", vault_dir,
            ], capture_output=True, text=True)
            
            self.assertEqual(r.returncode, 0, f"stderr: {r.stderr}")
            self.assertIn("Saved to vault:", r.stdout)
            
            # Verify file exists
            saved_files = list(Path(vault_dir).glob("*.md"))
            self.assertEqual(len(saved_files), 1)
            self.assertIn("AAPL", saved_files[0].name)
    
    def test_save_creates_directory(self):
        """Should create vault directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = os.path.join(tmp_dir, "report.md")
            with open(report_path, "w") as f:
                f.write("# Test")
            
            vault_dir = os.path.join(tmp_dir, "deep", "nested", "vault")
            
            r = subprocess.run([
                sys.executable, str(SAVE_SCRIPT),
                "--report", report_path,
                "--ticker", "MSFT",
                "--vault-dir", vault_dir,
            ], capture_output=True, text=True)
            
            self.assertEqual(r.returncode, 0)
            self.assertTrue(os.path.isdir(vault_dir))
    
    def test_save_duplicate_sequencing(self):
        """Duplicate saves on same day should get sequence numbers."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = os.path.join(tmp_dir, "report.md")
            with open(report_path, "w") as f:
                f.write("# Test")
            
            vault_dir = os.path.join(tmp_dir, "vault")
            
            # Save twice
            for _ in range(3):
                r = subprocess.run([
                    sys.executable, str(SAVE_SCRIPT),
                    "--report", report_path,
                    "--ticker", "AAPL",
                    "--vault-dir", vault_dir,
                ], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0)
            
            saved_files = sorted(Path(vault_dir).glob("*.md"))
            self.assertEqual(len(saved_files), 3)
            # First file: YYYY-MM-DD-AAPL.md
            # Second: YYYY-MM-DD-AAPL-2.md
            # Third: YYYY-MM-DD-AAPL-3.md
    
    def test_save_missing_report_fails(self):
        """Should fail gracefully if report file doesn't exist."""
        r = subprocess.run([
            sys.executable, str(SAVE_SCRIPT),
            "--report", "/nonexistent/path.md",
            "--ticker", "AAPL",
        ], capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)


class TestIntegration(unittest.TestCase):
    """End-to-end integration tests using mock sub-agent outputs."""
    
    def test_full_pipeline_mock(self):
        """Full pipeline: validate → assemble → save."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Step 0: Validate
            r = subprocess.run([
                sys.executable, str(VALIDATE_SCRIPT),
                "--ticker", "AAPL", "--risk", "moderate", "--period", "long-term",
                "--prefs", "prefer limit orders"
            ], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0)
            inputs = json.loads(r.stdout)["inputs"]
            
            # Step 5: Assemble (using mock outputs for steps 1-4)
            report_path = os.path.join(tmp_dir, "report.md")
            assemble_input = json.dumps({
                "ticker": inputs["ticker"],
                "risk_tolerance": inputs["risk_tolerance"],
                "investment_period": inputs["investment_period"],
                "execution_preferences": inputs["execution_preferences"],
                "data_analyst": MOCK_DATA_ANALYST,
                "trading_analyst": MOCK_TRADING_ANALYST,
                "execution_analyst": MOCK_EXECUTION_ANALYST,
                "risk_analyst": MOCK_RISK_ANALYST,
            })
            
            r = subprocess.run([
                sys.executable, str(ASSEMBLE_SCRIPT), "--stdin", "--output", report_path
            ], input=assemble_input, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0)
            
            # Step 6: Save to vault
            vault_dir = os.path.join(tmp_dir, "vault")
            r = subprocess.run([
                sys.executable, str(SAVE_SCRIPT),
                "--report", report_path,
                "--ticker", "AAPL",
                "--vault-dir", vault_dir,
            ], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0)
            
            # Verify final output
            saved_files = list(Path(vault_dir).glob("*.md"))
            self.assertEqual(len(saved_files), 1)
            
            with open(saved_files[0]) as f:
                final = f.read()
            
            # Verify all sections present
            self.assertIn("type: financial-analysis", final)
            self.assertIn("ticker: AAPL", final)
            self.assertIn("## 1. Market Data Analysis", final)
            self.assertIn("## 2. Trading Strategies", final)
            self.assertIn("## 3. Execution Plan", final)
            self.assertIn("## 4. Risk Assessment", final)
            self.assertIn("Not financial advice", final)
            
            # Verify content from each stage is present
            self.assertIn("Morgan Stanley", final)  # from data analyst
            self.assertIn("Covered Call", final)    # from trading analyst
            self.assertIn("trailing stop", final.lower())  # from execution
            self.assertIn("Psychological Risks", final)    # from risk analyst
    
    def test_pipeline_handles_different_tickers(self):
        """Pipeline should work with various ticker formats."""
        for ticker in ["GOOGL", "BRK.B", "TSLA", "NVDA"]:
            with tempfile.TemporaryDirectory() as tmp_dir:
                r = subprocess.run([
                    sys.executable, str(VALIDATE_SCRIPT),
                    "--ticker", ticker, "--risk", "aggressive", "--period", "short-term"
                ], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, f"Failed for ticker: {ticker}")
                data = json.loads(r.stdout)
                self.assertEqual(data["inputs"]["ticker"], ticker)


if __name__ == "__main__":
    unittest.main()
