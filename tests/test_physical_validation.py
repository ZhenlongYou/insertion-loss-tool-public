from pathlib import Path
import tempfile
import unittest

import numpy as np

from insertion_loss_tool.gui import run_self_test
from insertion_loss_tool.touchstone import TouchstoneData, read_touchstone
from insertion_loss_tool.validation import (
    assert_sampled_passive,
    diagnose_sampled_network,
    minimum_s2p_insertion_loss_db,
)


class PhysicalValidationTests(unittest.TestCase):
    def test_diagnostics_match_independent_numpy_oracle_and_reject_false_green(self):
        frequency_hz = np.array([1e9, 2e9])
        matrix = np.array(
            [
                [[0.0, 1.04], [1.04, 0.0]],
                [[0.0, 0.80], [0.80, 0.0]],
            ],
            dtype=complex,
        )
        data = TouchstoneData(frequency_hz=frequency_hz, s=matrix)

        independent = np.linalg.svd(matrix, compute_uv=False).max(axis=1)
        diagnostics = diagnose_sampled_network(data)

        self.assertAlmostEqual(diagnostics.maximum_singular_value, float(independent[0]))
        self.assertEqual(diagnostics.worst_frequency_hz, 1e9)
        self.assertFalse(diagnostics.sampled_passive)
        with self.assertRaisesRegex(ValueError, "not passive"):
            assert_sampled_passive(data, context="legacy self-test output")

    def test_s2p_loss_floor_matches_closed_form_power_budget(self):
        expected = -10.0 * np.log10(1.0 - 10.0 ** (-20.0 / 10.0))

        actual = minimum_s2p_insertion_loss_db(20.0)

        self.assertAlmostEqual(actual, expected, places=14)

    def test_gui_self_test_outputs_are_reread_and_sampled_passive(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = run_self_test(tmp)
            network_paths = [path for path in paths if Path(path).suffix.lower() in {".s2p", ".s4p"}]
            self.assertEqual(len(network_paths), 4)
            for path in network_paths:
                loaded = read_touchstone(path)
                singular_values = np.linalg.svd(loaded.s, compute_uv=False)
                self.assertLessEqual(
                    float(np.max(singular_values)),
                    1.0 + 1e-9,
                    Path(path).name,
                )


if __name__ == "__main__":
    unittest.main()
