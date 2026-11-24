#!/usr/bin/env python3
"""Drift control: separate "the kernel changed" from "the machine changed".

The sweep boots kernels one after another. That design cannot tell a kernel
effect from a machine effect: if the host slows down over an afternoon (thermal
throttling, another VM, a fan curve), later kernels inherit the drift. The
4.16-4.18 boots in `results/kernels/` look like a textbook case — every test,
including a pure-CPU loop that never enters the kernel, comes out about twice as
fast.

This script analyses an **interleaved** design: the same kernels are booted more
than once, in an order that breaks the confound, e.g.

    A B C A B C      (or)     A B A B

Each boot is passed in the order it happened:

    python3 analysis/analyze_drift.py \
        --run 4.15=results/drift/a1 \
        --run 4.16=results/drift/b1 \
        --run 4.20=results/drift/c1 \
        --run 4.15=results/drift/a2 \
        --run 4.16=results/drift/b2 \
        --run 4.20=results/drift/c2

It reports, per boot, the median latency across tests and the pure-CPU control,
then two rank correlations:

    Spearman(boot order, cpu time)     -> big when the machine itself drifts
    Spearman(boot order, median time)  -> big when the measurements follow it

and finally compares the within-kernel spread to the between-kernel spread. If
the between-kernel spread is not clearly larger, the "kernel effect" is not
separable from machine drift on this guest.
"""

import argparse
import glob
import os
import sys

CONTROL_TEST = "cpu"


def parse_kbest(path):
    out = {}
    with open(path) as fh:
        for line in fh:
            if "kbest:" not in line:
                continue
            name, _, value = line.partition(" kbest:,")
            try:
                out[name.strip()] = float(value.strip()) * 1e9
            except ValueError:
                continue
    return out


def load_dir(path):
    runs = []
    for run_dir in sorted(glob.glob(os.path.join(path, "run*"))):
        if os.path.isdir(run_dir):
            csvs = [p for p in glob.glob(os.path.join(run_dir, "*.csv"))
                    if "summary" not in os.path.basename(p).lower()]
            if csvs:
                runs.append(parse_kbest(sorted(csvs)[0]))
    if not runs:
        sys.exit("no run*/ CSVs under %s (run course/run_toggle.py there)" % path)
    tests = sorted(set().union(*[set(r) for r in runs]))
    data = {}
    for t in tests:
        values = [r[t] for r in runs if t in r]
        if values:
            data[t] = sum(values) / len(values)
    return data


def median(values):
    s = sorted(values)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0


def spearman(xs, ys):
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        for position, index in enumerate(order):
            r[index] = position + 1.0
        return r

    rx, ry = rank(xs), rank(ys)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else 0.0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", action="append", required=True,
                    metavar="LABEL=DIR",
                    help="one boot, in the order it happened; repeat the flag")
    ap.add_argument("--control", default=CONTROL_TEST,
                    help="test that never enters the kernel (default: cpu)")
    args = ap.parse_args()

    boots = []
    for spec in args.run:
        label, _, path = spec.partition("=")
        if not path:
            sys.exit("bad --run value: %r (expected LABEL=DIR)" % spec)
        boots.append((label.strip(), path.strip(), load_dir(path.strip())))

    if len(boots) < 3:
        sys.exit("need at least three boots for a drift check")

    # normalise to the first boot so the table reads as a ratio
    ref = boots[0][2]
    common = [t for t in sorted(ref)
              if all(t in data for _, _, data in boots) and ref[t] > 0]

    print("| boot | kernel | median ratio | %s (ms) | tests |" %
          args.control)
    print("| --- | --- | --- | --- | --- |")

    orders, cpu, med = [], [], []
    for i, (label, _, data) in enumerate(boots):
        ratios = [data[t] / ref[t] for t in common]
        cpu_ms = data.get(args.control, float("nan")) / 1e6
        orders.append(i)
        cpu.append(cpu_ms)
        med.append(median(ratios))
        print("| %d | %s | %.3f | %.2f | %d |" %
              (i + 1, label, median(ratios), cpu_ms, len(common)))

    rho_cpu = spearman(orders, cpu)
    rho_med = spearman(orders, med)

    print()
    print("Spearman(boot order, %s)   : %+.2f" % (args.control, rho_cpu))
    print("Spearman(boot order, median) : %+.2f" % (rho_med))

    # within-kernel vs between-kernel spread
    by_kernel = {}
    for label, _, data in boots:
        ratios = [data[t] / ref[t] for t in common]
        by_kernel.setdefault(label, []).append(median(ratios))

    within = []
    between = []
    for label, values in by_kernel.items():
        if len(values) > 1:
            within.append(max(values) - min(values))
    modes = [median(v) for v in by_kernel.values()]
    if len(modes) > 1:
        between.append(max(modes) - min(modes))
    w = max(within) if within else float("nan")
    b = between[0] if between else float("nan")

    print("\nwithin-kernel spread (same kernel, different boots) : %s" %
          ("%.3f" % w if within else "n/a — boot each kernel twice"))
    print("between-kernel spread                               : %s" %
          ("%.3f" % b if between else "n/a"))

    print("\nreading")
    if abs(rho_cpu) >= 0.7:
        print("  The pure-CPU control tracks the boot order. This guest drifts; "
              "kernel comparisons must be interleaved, and a single pass cannot "
              "separate kernel from machine.")
    else:
        print("  The pure-CPU control does not track the boot order. No machine "
              "drift was detected in this campaign.")
    if within and b == b and b <= w:
        print("  Within-kernel spread is not smaller than between-kernel spread: "
              "the kernel effect is not separable here.")
    elif within and b == b:
        print("  Within-kernel spread is smaller than between-kernel spread: the "
              "kernel effect survives the drift check.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
