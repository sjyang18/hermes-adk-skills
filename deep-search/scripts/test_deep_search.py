#!/usr/bin/env python3
"""
Deep Search — Test suite to validate the ported skill components.
Tests prompt formatting, save_report, and the evaluation JSON parsing.
"""

import json
import os
import sys
import tempfile

# Add parent scripts dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prompts import (
    PLAN_GENERATOR,
    PLAN_REFINER,
    SECTION_PLANNER,
    SECTION_RESEARCHER,
    RESEARCH_EVALUATOR,
    ENHANCED_SEARCH,
    REPORT_COMPOSER,
    TODAY,
)
from save_report import save_report, slugify


def test_prompts_contain_required_elements():
    """Verify all prompts have key structural elements."""
    print("TEST: Prompts contain required elements...")

    # Plan generator should mention [RESEARCH] and [DELIVERABLE]
    assert "[RESEARCH]" in PLAN_GENERATOR
    assert "[DELIVERABLE]" in PLAN_GENERATOR
    assert "5 action-oriented" in PLAN_GENERATOR

    # Plan refiner should have template variables
    assert "{existing_plan}" in PLAN_REFINER
    assert "{user_feedback}" in PLAN_REFINER
    assert "[MODIFIED]" in PLAN_REFINER

    # Section planner
    assert "{research_plan}" in SECTION_PLANNER
    assert "4-6" in SECTION_PLANNER

    # Section researcher
    assert "Phase 1" in SECTION_RESEARCHER
    assert "Phase 2" in SECTION_RESEARCHER
    assert "{research_plan}" in SECTION_RESEARCHER
    assert "{report_sections}" in SECTION_RESEARCHER

    # Evaluator should produce JSON
    assert '"grade"' in RESEARCH_EVALUATOR
    assert '"pass"' in RESEARCH_EVALUATOR
    assert '"fail"' in RESEARCH_EVALUATOR
    assert "{research_findings}" in RESEARCH_EVALUATOR

    # Enhanced search
    assert "{evaluation_feedback}" in ENHANCED_SEARCH
    assert "{existing_findings}" in ENHANCED_SEARCH

    # Report composer
    assert "{research_plan}" in REPORT_COMPOSER
    assert "{research_findings}" in REPORT_COMPOSER
    assert "{report_sections}" in REPORT_COMPOSER
    assert "inline" in REPORT_COMPOSER.lower()

    print("  ✓ All prompts have required structural elements")


def test_today_date_injected():
    """Verify date is injected into prompts."""
    print("TEST: Today's date is injected...")
    assert TODAY in PLAN_GENERATOR
    assert TODAY in SECTION_RESEARCHER
    assert TODAY in RESEARCH_EVALUATOR
    print(f"  ✓ Date {TODAY} found in time-sensitive prompts")


def test_slugify():
    """Test slug generation."""
    print("TEST: Slugify function...")
    assert slugify("Hello World!") == "hello-world"
    assert slugify("AI & Machine Learning: 2024") == "ai-machine-learning-2024"
    assert slugify("a" * 100) == "a" * 50  # max length
    assert slugify("  spaces  ") == "spaces"
    print("  ✓ Slugify works correctly")


def test_save_report():
    """Test report saving with frontmatter."""
    print("TEST: Save report to vault...")
    with tempfile.TemporaryDirectory() as tmpdir:
        topic = "Test Research Topic"
        content = "# Report\n\nThis is test content.\n\n## Section 1\n\nDetails here."

        filepath = save_report(topic, content, vault_dir=tmpdir)

        assert os.path.exists(filepath)
        assert "test-research-topic" in filepath

        with open(filepath) as f:
            saved = f.read()

        # Check frontmatter
        assert "---" in saved
        assert "type: deep-search-report" in saved
        assert 'topic: "Test Research Topic"' in saved
        assert "tags: [research, deep-search, auto-generated]" in saved
        # Check content preserved
        assert "# Report" in saved
        assert "## Section 1" in saved

    print("  ✓ Report saved with correct frontmatter")


def test_evaluation_json_parsing():
    """Test that evaluator output can be parsed."""
    print("TEST: Evaluation JSON parsing...")

    # Simulate evaluator outputs
    pass_output = '{"grade": "pass", "comment": "Research is comprehensive", "follow_up_queries": []}'
    fail_output = '{"grade": "fail", "comment": "Missing depth on topic X", "follow_up_queries": ["query 1", "query 2", "query 3"]}'

    pass_data = json.loads(pass_output)
    assert pass_data["grade"] == "pass"
    assert pass_data["follow_up_queries"] == []

    fail_data = json.loads(fail_output)
    assert fail_data["grade"] == "fail"
    assert len(fail_data["follow_up_queries"]) == 3

    print("  ✓ Evaluation JSON parses correctly for pass and fail cases")


def test_workflow_sequence():
    """Validate the expected workflow sequence is documented."""
    print("TEST: Workflow sequence validation...")

    # Read the SKILL.md and verify step ordering
    skill_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "SKILL.md")
    with open(skill_path) as f:
        skill_content = f.read()

    expected_steps = [
        "Step 0",  # Collect Input
        "Step 1",  # Generate Plan
        "Step 2",  # User Review
        "Step 3",  # Section Planning
        "Step 4",  # Deep Research
        "Step 5",  # Iterative Refinement
        "Step 6",  # Report Composer
        "Step 7",  # Deliver & Save
    ]

    for step in expected_steps:
        assert step in skill_content, f"Missing {step} in SKILL.md"

    print(f"  ✓ All {len(expected_steps)} workflow steps documented in SKILL.md")


if __name__ == "__main__":
    print("=" * 60)
    print("Deep Search Skill — Test Suite")
    print("=" * 60)

    tests = [
        test_prompts_contain_required_elements,
        test_today_date_injected,
        test_slugify,
        test_save_report,
        test_evaluation_json_parsing,
        test_workflow_sequence,
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
            print(f"  ✗ ERROR: {e}")
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
    print("=" * 60)
    sys.exit(0 if failed == 0 else 1)
