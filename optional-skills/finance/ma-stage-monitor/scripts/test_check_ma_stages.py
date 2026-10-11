#!/usr/bin/env python3
"""Offline tests for check_ma_stages.py."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

SCRIPT = Path(__file__).with_name("check_ma_stages.py")
SPEC = importlib.util.spec_from_file_location("check_ma_stages", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class MAStageMonitorTests(unittest.TestCase):
    def setUp(self):
        self.index = pd.date_range("2025-01-01", periods=60, freq="B")
        self.rising = pd.DataFrame(
            {"Close": pd.Series(range(100, 160), index=self.index, dtype=float)}
        )

    def test_default_method_is_ema_5_20_40(self):
        stage, values, slopes = MODULE.get_stage_for_date(
            self.rising, self.index[-1]
        )
        expected = tuple(
            float(self.rising["Close"].ewm(span=window, adjust=False).mean().iloc[-1])
            for window in (5, 20, 40)
        )
        self.assertEqual(stage, "sml")
        self.assertEqual(values, expected)
        self.assertTrue(all(slope > 0 for slope in slopes))
        self.assertEqual(
            MODULE.trend_confirmation(stage, slopes), "confirmed_uptrend"
        )

    def test_sma_is_supported_but_not_default(self):
        _, ema_values, _ = MODULE.get_stage_for_date(self.rising, self.index[-1])
        _, sma_values, _ = MODULE.get_stage_for_date(
            self.rising, self.index[-1], ma_type="sma"
        )
        self.assertNotEqual(ema_values, sma_values)

    def test_methodology_change_creates_silent_baseline(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "state.json"
            state_path.write_text(
                json.dumps({"AMZN": {"stage": "msl", "date": "2025-01-01"}})
            )
            with patch.object(MODULE, "fetch_history", return_value=self.rising):
                results = MODULE.run_check(
                    ["AMZN"], Path(temp_dir), notify_only=True
                )
            self.assertEqual(results, [])
            saved = json.loads(state_path.read_text())
            self.assertEqual(saved["AMZN"]["methodology"], "1d:ema:5,20,40")
            self.assertEqual(saved["AMZN"]["stage"], "sml")

    def test_windows_must_be_distinct_and_ascending(self):
        with self.assertRaises(ValueError):
            MODULE.validate_windows([5, 40, 20])
        with self.assertRaises(ValueError):
            MODULE.validate_windows([5, 20, 20])


if __name__ == "__main__":
    unittest.main()
