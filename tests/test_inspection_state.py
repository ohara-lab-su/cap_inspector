#!/usr/bin/env python
"""キャップ判定結果の保持と参照に関する回帰試験。"""

import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

# 実機やx_loggerの設定なしで画像認識ロジックを検証する。
if "x_logger" not in sys.modules:
    try:
        import x_logger
    except ImportError:
        logger_module = types.ModuleType("x_logger")

        class XLogger:
            def __init__(self, logger_name):
                self.logger_name = logger_name

            def error(self, message):
                pass

        logger_module.XLogger = XLogger
        sys.modules["x_logger"] = logger_module

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
package = types.ModuleType("cap_inspector")
package.__path__ = [str(Path(__file__).resolve().parents[1] / "src" / "cap_inspector")]
sys.modules["cap_inspector"] = package
from cap_inspector.cap_inspector import CapInspector


class InspectionStateTest(unittest.TestCase):
    """判定結果の読み出しが再検査しないことを確認する。"""

    def test_flags_read_without_capture(self):
        inspector = CapInspector()
        self.assertFalse(inspector.is_open())
        self.assertFalse(inspector.is_closed())
        inspector._is_open = True
        inspector._is_closed = False
        with patch.object(inspector, "_read_frame", side_effect=AssertionError):
            self.assertTrue(inspector.is_open())
            self.assertFalse(inspector.is_closed())

    def test_inspect_returns_mode_and_updates_both_flags(self):
        inspector = CapInspector()
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        with patch.object(inspector, "_read_frame", return_value=frame):
            with patch.object(inspector, "_detect_cap", return_value=[]):
                self.assertFalse(inspector.inspect("opened"))
                self.assertEqual(inspector.get_current_mode(), "opened")
                self.assertFalse(inspector.is_open())
                self.assertFalse(inspector.is_closed())

    def test_individual_setters(self):
        inspector = CapInspector()
        inspector.set_bottle_rim_y(280)
        inspector.set_target_open_mm(4.0)
        inspector.set_mode("opened")
        self.assertEqual(inspector.get_parameters()["BOTTLE_RIM_Y"], 280)
        self.assertEqual(inspector.get_parameters()["TARGET_OPEN_MM"], 4.0)
        self.assertEqual(inspector.get_parameters()["mode"], "opened")


if __name__ == "__main__":
    unittest.main()
