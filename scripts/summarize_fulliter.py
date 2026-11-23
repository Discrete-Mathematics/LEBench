#!/usr/bin/env python3
"""Print mean ± sample stdev for the BASE_ITER 10000 runs."""

import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FULL = ROOT / "results" / "fulliter" / "4.4.0-210-generic"


def kbest(path):
    vals = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "kbest" not in line:
            continue
        name = line.split("kbest")[0].strip()
        nums = [p for p in line.split(",") if p.strip()[:1].isdigit()]
        if nums:
            vals[name] = float(nums[-1]) * 1e9
    return vals


def nearest(value):
    return int(value + 0.5) if value >= 0 else int(value - 0.5)


def main():
    runs = [kbest(FULL / ("run%d.csv" % i)) for i in (1, 2, 3)]
    names = list(runs[0])
    print("exit", (FULL / "run3.exit_code.txt").read_text().strip())
    for name in names:
        samples = [run[name] for run in runs]
        mu = statistics.mean(samples)
        sd = statistics.stdev(samples)
        print(
            "%-18s %6d +/- %6d   %s"
            % (name, nearest(mu), nearest(sd), [nearest(s) for s in samples])
        )


if __name__ == "__main__":
    main()
