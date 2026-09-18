from pathlib import Path
import tempfile
import unittest

import numpy as np

from insertion_loss_tool.touchstone import TouchstoneData, read_touchstone, write_touchstone

try:
    import skrf
except ImportError:  # pragma: no cover - optional validation environment
    skrf = None


@unittest.skipIf(skrf is None, "optional scikit-rf validation dependency is not installed")
class ScikitRfDifferentialTests(unittest.TestCase):
    def test_full_matrix_writer_matches_scikit_rf_for_common_port_counts(self):
        frequency_hz = np.array([1e9, 2.5e9])
        with tempfile.TemporaryDirectory() as tmp:
            for n_ports in (2, 3, 4, 6, 8):
                with self.subTest(n_ports=n_ports):
                    matrix = np.zeros((frequency_hz.size, n_ports, n_ports), dtype=complex)
                    for point in range(frequency_hz.size):
                        for out_port in range(n_ports):
                            for in_port in range(n_ports):
                                matrix[point, out_port, in_port] = complex(
                                    0.01 * (1 + point + 3 * out_port + in_port),
                                    -0.001 * (1 + 2 * out_port + in_port),
                                )
                    path = Path(tmp) / f"differential.s{n_ports}p"
                    expected = TouchstoneData(frequency_hz, matrix, z0=75.0)

                    write_touchstone(expected, path, frequency_unit="hz", data_format="ri")
                    authority = skrf.Network(str(path))
                    reread = read_touchstone(path)

                    np.testing.assert_allclose(authority.f, frequency_hz, rtol=0.0, atol=0.0)
                    np.testing.assert_allclose(authority.s, matrix, rtol=0.0, atol=1e-15)
                    np.testing.assert_allclose(reread.s, authority.s, rtol=0.0, atol=1e-15)


if __name__ == "__main__":
    unittest.main()
