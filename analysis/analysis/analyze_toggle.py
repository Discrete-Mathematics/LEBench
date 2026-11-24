#!/usr/bin/env python3
"""Compare the two arms of a claim-2 toggle experiment and emit a verdict.

Inputs are the directories written by `course/run_toggle.py`:

    <dir>/run1/output.<release>.csv  ...  runN/...
    <dir>/environment.txt
    <dir>/summary.csv        (used only when the run directories are gone)

Each reportable number is the mean and sample standard deviation of the K-best
values of N runs. A test counts as different only when the two intervals are
disjoint 鈥?the same rule the rest of this repository uses.

Usage:

    python3 analysis/analyze_toggle.py \
        --baseline results/toggles/cgroup-on \
        --variant  results/toggles/cgroup-off \
        --cause 6 --toggle cgroup_disable=memory

`--baseline` is the arm with the paper's default state (the mitigation or the
feature enabled); `--variant` is the arm with it switched off. The ratio printed
is variant / baseline, so a ratio below 1 means the switch made the test faster.

Prints a markdown table ready to paste into docs/verdicts.md, then the verdict
line, then the evidence lines that show the switch actually took effect.
"""

import argparse
import csv
import glob
import os
import sys

# Cause -> (tests the paper associates with it, expected sign of variant/baseline)
#   -1 : switching the feature off should make these tests FASTER
#   +1 : switching the feature off should make them SLOWER
CAUSE = {
    "1": (["getpid", "small read", "recv", "fork"], -1),      # KPTI, nopti
    "2": (["select", "poll", "epoll",
           "select big", "poll big", "epoll big"], -1),        # Retpoline off
    "5": (["small page fault", "mid page fault",
           "big page fault"], -1),                            # fault-around window
    "6": (["big munmap", "mid munmap", "small munmap"], -1),   # cgroup memory off
    "7": (["small page fault", "mid page fault",
           "big page fault"], +1),                            # THP off should hurt
}

CONTROL = "getpid"


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


def mean_sd(values):
    n = len(values)
    mean = sum(values) / n
    if n < 2:
        return mean, 0.0
    var = sum((v - mean) ** 2 for v in values) / (n - 1)
    return mean, var ** 0.5


def load_dir(path):
    """Return ({test: (mean, sd, n)}, environment dict)."""
    runs = []
    for run_dir in sorted(glob.glob(os.path.join(path, "run*"))):
        if not os.path.isdir(run_dir):
            continue
        csvs = [p for p in glob.glob(os.path.join(run_dir, "*.csv"))
                if "summary" not in os.path.basename(p).lower()]
        if csvs:
            runs.append(parse_kbest(sorted(csvs)[0]))

    if runs:
        tests = sorted(set().union(*[set(r) for r in runs]))
        data = {}
        for t in tests:
            values = [r[t] for r in runs if t in r]
            if values:
                data[t] = (mean_sd(values)[0], mean_sd(values)[1], len(values))
    else:
        summary = os.path.join(path, "summary.csv")
        if not os.path.exists(summary):
            sys.exit("no run*/ CSVs and no summary.csv under %s" % path)
        data = {}
        with open(summary) as fh:
            for row in csv.DictReader(fh):
                data[row["test"]] = (float(row["mean_ns"]),
                                     float(row["stdev_ns"]),
                                     int(row.get("n") or 0))

    env = {}
    env_path = os.path.join(path, "environment.txt")
    if os.path.exists(env_path):
        with open(env_path) as fh:
            for line in fh:
                if ": " in line:
                    key, _, value = line.partition(": ")
                    env[key.strip()] = value.strip()
    return data, env


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--baseline", required=True, help="paper's default state")
    ap.add_argument("--variant", required=True, help="the switched-off state")
    ap.add_argument("--cause", default="", help="paper cause number, 1-11")
    ap.add_argument("--toggle", default="", help="the parameter that was changed")
    ap.add_argument("--label-baseline", default="baseline")
    ap.add_argument("--label-variant", default="variant")
    args = ap.parse_args()

    base_data, base_env = load_dir(args.baseline)
    var_data, var_env = load_dir(args.variant)

    shared = [t for t in sorted(set(base_data) & set(var_data))
              if base_data[t][0] > 0]

    print("| Test | %s | %s | ratio | intervals |" %
          (args.label_baseline, args.label_variant))
    print("| --- | --- | --- | --- | --- |")

    rows = []
    for t in shared:
        bm, bsd, _ = base_data[t]
        vm, vsd, _ = var_data[t]
        disjoint = (bm - bsd) > (vm + vsd) or (vm - vsd) > (bm + bsd)
        ratio = vm / bm if bm else float("nan")
        rows.append((t, bm, bsd, vm, vsd, ratio, disjoint))
        print("| %s | %.0f 卤 %.0f | %.0f 卤 %.0f | %.3f | %s |" %
              (t, bm, bsd, vm, vsd, ratio, "disjoint" if disjoint else "overlap"))

    if not rows:
        sys.exit("no common tests between the two arms")

    # ---- verdict ---------------------------------------------------------
    cause = args.cause or "?"
    expected_tests, expected_sign = CAUSE.get(cause, ([], 0))
    moved = [r for r in rows if r[6]]
    relevant = [r for r in rows if r[0] in expected_tests] or rows
    relevant_moved = [r for r in relevant if r[6]]

    if not moved:
        verdict = "**not supported** 鈥?no test separates (every interval overlaps)"
    elif not relevant_moved:
        others = ", ".join("%s %.2fx" % (r[0], r[5]) for r in moved)
        verdict = ("**not supported for this cause** 鈥?the tests it predicts are "
                   "flat; the only separation is elsewhere (%s)" % others)
    else:
        names = ", ".join("%s %.2fx" % (r[0], r[5]) for r in relevant_moved)
        signs = {1 if r[5] > 1 else -1 for r in relevant_moved}
        if expected_sign == 0:
            verdict = "informational: %s" % names
        elif signs == {expected_sign}:
            verdict = "**supported** 鈥?expected direction: %s" % names
        elif signs == {-expected_sign}:
            verdict = "**opposite direction** 鈥?%s" % names
        else:
            verdict = "**mixed** 鈥?%s" % names

    print()
    print("Cause %s%s 鈥?%s" % (
        cause, (" (`%s`)" % args.toggle) if args.toggle else "", verdict))

    control = [r for r in rows if r[0] == CONTROL]
    if control:
        c = control[0]
        print("\ncontrol `%s`: %.0f 鈫?%.0f ns (%.3f, %s) 鈥?%s" %
              (CONTROL, c[1], c[3], c[5], "disjoint" if c[6] else "overlap",
               "CONTROL MOVED: treat the whole comparison with suspicion"
               if c[6] else "control stable, as intended"))

    # ---- did the switch actually take effect? ----------------------------
    print("\nevidence")
    keys = ("cmdline", "indirect_thunks", "cgroup_disabled", "thp_enabled",
            "fault_around_bytes", "vuln_meltdown", "vuln_spectre_v2")
    for key in keys:
        if key in base_env or key in var_env:
            print("  %-20s %s: %-42s %s: %s" %
                  (key,
                   args.label_baseline[:8], base_env.get(key, "-")[:42],
                   args.label_variant[:9], var_env.get(key, "-")))

    if args.toggle:
        needle = args.toggle.split("=")[0]
        found = any(needle in (e.get("cmdline") or "")
                    for e in (base_env, var_env))
        print("  %-20s %s" % ("switch in cmdline",
                              "yes" if found else
                              "NOT FOUND 鈥?the two arms may be the same boot"))
    return 0


if __name__ == "__main__":
    sys.exit(main())

