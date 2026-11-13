"""Unit tests for macrobench/parse_macrobench.py.

Run with:  python3 -m unittest discover -s tests -v
Kept Python 3.5 compatible because the measurement guest ships 3.5.
"""

import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "parse_macrobench", str(ROOT / "macrobench" / "parse_macrobench.py")
)

HEADER = ["config", "run", "app", "test", "metric", "value", "unit"]


def load_module():
    module = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(module)
    return module


parse_macrobench = load_module()


def write_batch(root, config, values):
    directory = Path(root) / config
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "results.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADER)
        for index, value in enumerate(values):
            writer.writerow([config, index + 1, "redis", "GET", "throughput", value, "req_per_s"])


class AggregateTest(unittest.TestCase):
    def rows(self, values, config="default"):
        return [
            {
                "config": config,
                "app": "redis",
                "test": "GET",
                "metric": "throughput",
                "unit": "req_per_s",
                "value": value,
            }
            for value in values
        ]

    def test_mean_and_sample_stdev(self):
        stats = parse_macrobench.aggregate(self.rows([100.0, 110.0, 120.0]))
        entry = stats[("default", "redis", "GET", "throughput")]
        self.assertEqual(entry["n"], 3)
        self.assertAlmostEqual(entry["mean"], 110.0, places=6)
        self.assertAlmostEqual(entry["std"], 10.0, places=6)
        self.assertAlmostEqual(entry["min"], 100.0, places=6)
        self.assertAlmostEqual(entry["max"], 120.0, places=6)

    def test_single_sample_has_zero_stdev(self):
        stats = parse_macrobench.aggregate(self.rows([42.0]))
        self.assertAlmostEqual(stats[("default", "redis", "GET", "throughput")]["std"], 0.0, places=6)


class LoadRowsTest(unittest.TestCase):
    def test_reads_nested_batches_and_skips_non_numeric_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "default"
            directory.mkdir()
            path = directory / "results.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(HEADER)
                writer.writerow(["default", 1, "redis", "GET", "throughput", "100.5", "req_per_s"])
                writer.writerow(["default", 2, "redis", "GET", "throughput", "not-a-number", "req_per_s"])

            rows = parse_macrobench.load_rows(tmp)
            self.assertEqual(len(rows), 1)
            self.assertAlmostEqual(rows[0]["value"], 100.5, places=6)

    def test_ignores_files_outside_result_batches(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "summary.csv").write_text("config,app\n", encoding="utf-8")
            self.assertEqual(parse_macrobench.load_rows(tmp), [])


class MainTest(unittest.TestCase):
    def test_writes_summary_with_ratio_against_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_batch(tmp, "default", [100.0, 110.0, 120.0])
            write_batch(tmp, "spectre-off", [132.0, 132.0, 132.0])

            parse_macrobench.main([tmp])

            with open(str(Path(tmp) / "summary.csv"), newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

            ratios = {
                row["config"]: row["ratio_vs_default"]
                for row in rows
                if row["metric"] == "throughput" and row["config"] != "default"
            }
            self.assertIn("spectre-off", ratios)
            self.assertAlmostEqual(float(ratios["spectre-off"]), 132.0 / 110.0, places=3)

    def test_empty_root_exits(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit):
                parse_macrobench.main([tmp])


if __name__ == "__main__":
    unittest.main()
