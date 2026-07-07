#!/usr/bin/env python3
"""
Economic Research Agent — Test suite.
Tests API tools structure, prompts, CLI interface, and save_report.
"""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prompts import ERA_MAIN_INSTRUCTIONS, AUDITOR_JUDGE_INSTRUCTIONS, COMPLEXITY_CLASSIFIER
from save_report import save_report, slugify
from api_tools import (
    FRED_MSA_CODES, STATE_FIPS, STATE_TAX_RATES,
    fred_query, bls_query, census_query, hud_query, eia_query, tax_query,
)


def test_prompts_structure():
    """Verify prompts have required consulting protocol elements."""
    print("TEST: Prompts structure...")

    # Main ERA prompt
    assert "McKinsey" in ERA_MAIN_INSTRUCTIONS or "strategy consultanc" in ERA_MAIN_INSTRUCTIONS
    assert "FRED" in ERA_MAIN_INSTRUCTIONS
    assert "BLS" in ERA_MAIN_INSTRUCTIONS
    assert "Zero Hallucination" in ERA_MAIN_INSTRUCTIONS
    assert "proactively suggest" in ERA_MAIN_INSTRUCTIONS.lower()

    # Judge prompt
    assert "[REJECT]" in AUDITOR_JUDGE_INSTRUCTIONS
    assert "[ACCEPT]" in AUDITOR_JUDGE_INSTRUCTIONS
    assert "web_search" in AUDITOR_JUDGE_INSTRUCTIONS

    # Classifier
    assert '"LOW"' in COMPLEXITY_CLASSIFIER
    assert '"HIGH"' in COMPLEXITY_CLASSIFIER

    print("  ✓ All prompts have required elements")


def test_msa_codes_coverage():
    """Verify MSA code lookup has major US cities."""
    print("TEST: MSA codes coverage...")
    required_cities = ["Austin", "Raleigh", "Seattle", "Dallas", "Atlanta", "Denver"]
    for city in required_cities:
        assert city in FRED_MSA_CODES, f"Missing MSA code for {city}"
    assert len(FRED_MSA_CODES) >= 20
    print(f"  ✓ {len(FRED_MSA_CODES)} cities in MSA lookup")


def test_state_fips_coverage():
    """Verify all 50 states have FIPS codes."""
    print("TEST: State FIPS coverage...")
    assert len(STATE_FIPS) == 50, f"Expected 50 states, got {len(STATE_FIPS)}"
    assert STATE_FIPS["Texas"] == "48"
    assert STATE_FIPS["California"] == "06"
    assert STATE_FIPS["Washington"] == "53"
    print(f"  ✓ All 50 states covered")


def test_tax_rates_structure():
    """Verify tax rates have required fields."""
    print("TEST: Tax rates structure...")
    assert len(STATE_TAX_RATES) >= 30

    for state, rates in STATE_TAX_RATES.items():
        assert "corporate" in rates, f"{state} missing corporate rate"
        assert "individual_top" in rates, f"{state} missing individual rate"
        assert isinstance(rates["corporate"], (int, float))
        assert isinstance(rates["individual_top"], (int, float))

    # Verify known values
    assert STATE_TAX_RATES["Texas"]["corporate"] == 0  # No corporate income tax
    assert STATE_TAX_RATES["Texas"]["individual_top"] == 0
    assert STATE_TAX_RATES["California"]["individual_top"] == 13.3

    print(f"  ✓ {len(STATE_TAX_RATES)} states with valid tax data")


def test_tax_query_works():
    """Test tax query (no API key needed — local lookup)."""
    print("TEST: Tax query (local lookup)...")
    results = tax_query(["Texas", "California", "North Carolina"])
    assert len(results) == 3
    assert results[0]["state"] == "Texas"
    assert "0%" in results[0]["corporate_tax_rate"]
    assert "Tax Foundation" in results[0]["source"]
    assert results[1]["state"] == "California"
    assert "8.84%" in results[1]["corporate_tax_rate"]
    print("  ✓ Tax query returns correct data without API")


def test_api_missing_key_handling():
    """Test graceful fallback when API keys are missing."""
    print("TEST: Missing API key fallback to web_search...")

    # Temporarily unset keys
    orig_fred = os.environ.pop("FRED_API_KEY", None)
    orig_census = os.environ.pop("CENSUS_API_KEY", None)
    orig_hud = os.environ.pop("HUD_API_KEY", None)
    orig_eia = os.environ.pop("EIA_API_KEY", None)

    try:
        fred_result = fred_query(["Austin"], "unemployment")
        assert "fallback" in fred_result[0]
        assert fred_result[0]["fallback"] == "web_search"
        assert "fred.stlouisfed.org" in fred_result[0]["query"]

        census_result = census_query(["Texas"], "education")
        assert "fallback" in census_result[0]
        assert "data.census.gov" in census_result[0]["query"]

        hud_result = hud_query(states=["Texas"], metric="fmr")
        assert "fallback" in hud_result[0]
        assert "huduser.gov" in hud_result[0]["query"]

        eia_result = eia_query(["Texas"], "electricity")
        assert "fallback" in eia_result[0]
        assert "eia.gov" in eia_result[0]["query"]
    finally:
        # Restore keys
        if orig_fred:
            os.environ["FRED_API_KEY"] = orig_fred
        if orig_census:
            os.environ["CENSUS_API_KEY"] = orig_census
        if orig_hud:
            os.environ["HUD_API_KEY"] = orig_hud
        if orig_eia:
            os.environ["EIA_API_KEY"] = orig_eia

    print("  ✓ All APIs return web_search fallback query when key missing")


def test_save_report():
    """Test vault saving with frontmatter."""
    print("TEST: Save report...")
    with tempfile.TemporaryDirectory() as tmpdir:
        topic = "Austin vs Raleigh Tech Hub"
        content = "# Comparison\n\n| Metric | Austin | Raleigh |\n|--------|--------|---------|"
        regions = ["Austin", "Raleigh"]

        filepath = save_report(topic, content, regions, vault_dir=tmpdir)

        assert os.path.exists(filepath)
        assert "austin-vs-raleigh-tech-hub" in filepath

        with open(filepath) as f:
            saved = f.read()

        assert "type: economic-research" in saved
        assert "Austin, Raleigh" in saved
        assert "# Comparison" in saved

    print("  ✓ Report saved with correct frontmatter and regions")


def test_cli_interface():
    """Test CLI argument parsing."""
    print("TEST: CLI interface...")
    # Just verify the script is importable and has main()
    import api_tools
    assert hasattr(api_tools, 'main')
    assert hasattr(api_tools, 'fred_query')
    assert hasattr(api_tools, 'bls_query')
    assert hasattr(api_tools, 'census_query')
    assert hasattr(api_tools, 'hud_query')
    assert hasattr(api_tools, 'eia_query')
    assert hasattr(api_tools, 'tax_query')
    print("  ✓ CLI module has all expected functions")


def test_skill_md_structure():
    """Verify SKILL.md has required sections."""
    print("TEST: SKILL.md structure...")
    skill_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "SKILL.md")
    with open(skill_path) as f:
        content = f.read()

    required_sections = [
        "Prerequisites",
        "FRED_API_KEY",
        "BLS_API_KEY",
        "Workflow",
        "Consultative Protocol",
        "Pitfalls",
    ]
    for section in required_sections:
        assert section in content, f"Missing '{section}' in SKILL.md"

    print(f"  ✓ SKILL.md has all {len(required_sections)} required sections")


if __name__ == "__main__":
    print("=" * 60)
    print("Economic Research Agent — Test Suite")
    print("=" * 60)

    tests = [
        test_prompts_structure,
        test_msa_codes_coverage,
        test_state_fips_coverage,
        test_tax_rates_structure,
        test_tax_query_works,
        test_api_missing_key_handling,
        test_save_report,
        test_cli_interface,
        test_skill_md_structure,
    ]

    passed = 0
    failed = 0

    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ ERROR: {type(e).__name__}: {e}")
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
    print("=" * 60)
    sys.exit(0 if failed == 0 else 1)
