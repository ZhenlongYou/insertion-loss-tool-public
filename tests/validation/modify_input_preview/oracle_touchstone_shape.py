from __future__ import annotations

from pathlib import Path


def main() -> int:
    source = Path(__file__).resolve().parents[3] / "examples" / "formula_demo.s4p"
    lines = source.read_text(encoding="utf-8").splitlines()
    record_starts = [
        line for line in lines if line and not line[0].isspace() and line[0] not in "!#"
    ]
    first_frequency = float(record_starts[0].split()[0])
    last_frequency = float(record_starts[-1].split()[0])
    expected_ports = int(source.suffix.lower()[2:-1])
    if (
        expected_ports != 4
        or len(record_starts) != 201
        or first_frequency != 0.01
        or last_frequency != 40.0
        or expected_ports**2 != 16
    ):
        return 3
    print("ORACLE_OK 4 ports 201 frequency records 16 S-parameters 0.01-40 GHz")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
