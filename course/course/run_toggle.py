#!/usr/bin/env python3
"""Run the reduced LEBench suite on the *currently booted* kernel and capture
enough evidence to prove that the switch under test was actually in effect.

Deliberately does **not** reboot. Rebooting is `course/boot_toggle.sh`'s job,
because a wrong GRUB edit is how the guest was lost once already.

Written for the guest's Python 3.5 (no f-strings, no pathlib-only tricks).

Usage, on the guest, as root:

    python3 course/run_toggle.py --label cgroup-off --runs 3
    python3 course/run_toggle.py --label cgroup-on  --runs 3

Output:

    results/toggles/<label>/environment.txt
    results/toggles/<label>/run<N>/stdout.txt, stderr.txt, exit_code.txt,
                                 output.<release>.csv
    results/toggles/<label>/summary.csv

Exit code 0 only when every run finished and the evidence block was written.
"""

import argparse
import csv
import os
import platform
import subprocess
import sys
import time

KERNEL_CANDIDATES = [
    "/boot/config-{}",
    "/lib/modules/{}/build/.config",
]


def sh(cmd):
    """Run a shell command, return stripped stdout ('' on failure)."""
    try:
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        return out.decode("utf-8", "replace").strip()
    except Exception:
        return ""


def read_file(path, default=""):
    try:
        with open(path) as fh:
            return fh.read().strip()
    except Exception:
        return default


def evidence():
    """Everything that proves which switch state this boot is in."""
    rel = platform.release()
    ev = {}
    ev["kernel"] = rel
    ev["cmdline"] = read_file("/proc/cmdline")
    ev["date_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    ev["gcc"] = sh("gcc --version | head -1")
    ev["cpu"] = sh("grep -m1 'model name' /proc/cpuinfo | cut -d: -f2-").strip()
    ev["nproc"] = str(os.cpu_count())

    # per-mitigation state; these are the lines a reader checks first
    vuln_dir = "/sys/devices/system/cpu/vulnerabilities"
    if os.path.isdir(vuln_dir):
        for name in sorted(os.listdir(vuln_dir)):
            ev["vuln_" + name] = read_file(os.path.join(vuln_dir, name))

    # retpoline presence: the number that decides whether cause 2 is testable
    ev["indirect_thunks"] = sh("grep -c __x86_indirect_thunk /proc/kallsyms")

    # cgroup memory controller
    ev["cgroup_disabled"] = ""
    for line in read_file("/proc/cgroups").splitlines():
        parts = line.split()
        if parts and parts[0] == "memory":
            ev["cgroup_disabled"] = parts[-1]

    # THP
    ev["thp_enabled"] = read_file("/sys/kernel/mm/transparent_hugepage/enabled")
    ev["thp_defrag"] = read_file("/sys/kernel/mm/transparent_hugepage/defrag")

    # fault-around
    ev["fault_around_bytes"] = read_file(
        "/sys/kernel/debug/fault_around_bytes", "unreadable (debugfs not mounted)")

    # kernel config, if the package left one behind
    for pattern in KERNEL_CANDIDATES:
        path = pattern.format(rel)
        if os.path.exists(path):
            cfg = read_file(path)
            for key in ("CONFIG_SLAB_FREELIST_RANDOM", "CONFIG_HARDENED_USERCOPY",
                        "CONFIG_PAGE_TABLE_ISOLATION", "CONFIG_RETPOLINE",
                        "CONFIG_MEMCG", "CONFIG_TRANSPARENT_HUGEPAGE",
                        "CONFIG_CONTEXT_TRACKING_FORCE"):
                for line in cfg.splitlines():
                    if line.startswith(key + "=") or line.startswith("# " + key + " is"):
                        ev["cfg_" + key] = line
            break
    return ev


def parse_kbest(path):
    """LEBench CSV -> {test: nanoseconds} using the kbest row of each test."""
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


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--label", required=True,
                    help="short name for this switch state, e.g. cgroup-off")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--binary", default="course/sweep_bench")
    ap.add_argument("--outdir", default="results/toggles")
    ap.add_argument("--timeout", type=int, default=1200,
                    help="seconds per run; the reduced suite takes ~20 s")
    args = ap.parse_args()

    if os.geteuid() != 0:
        sys.exit("run as root: sudo python3 course/run_toggle.py ...")
    if not os.path.exists(args.binary):
        sys.exit("binary not found: %s (build it with: make -C course)" % args.binary)

    dest = os.path.join(args.outdir, args.label)
    os.makedirs(dest, exist_ok=True)

    ev = evidence()
    with open(os.path.join(dest, "environment.txt"), "w") as fh:
        for key in sorted(ev):
            fh.write("%s: %s\n" % (key, ev[key]))

    if not ev.get("indirect_thunks") and args.label.endswith("-off"):
        pass  # not an error: a zero thunk count is itself a result

    print("=" * 66)
    print("label      : %s" % args.label)
    print("kernel     : %s" % ev["kernel"])
    print("cmdline    : %s" % ev["cmdline"])
    print("thunks     : %s  (0 = no retpolines to switch off)" % ev.get("indirect_thunks"))
    print("cgroup mem : disabled=%s" % ev.get("cgroup_disabled"))
    print("=" * 66)

    per_run = []
    for i in range(1, args.runs + 1):
        run_dir = os.path.join(dest, "run%d" % i)
        os.makedirs(run_dir, exist_ok=True)
        stdout_path = os.path.join(run_dir, "stdout.txt")
        stderr_path = os.path.join(run_dir, "stderr.txt")

        started = time.time()
        with open(stdout_path, "w") as out, open(stderr_path, "w") as err:
            proc = subprocess.Popen([args.binary], stdout=out, stderr=err)
            try:
                code = proc.wait(timeout=args.timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                code = -1
        elapsed = time.time() - started

        with open(os.path.join(run_dir, "exit_code.txt"), "w") as fh:
            fh.write("%d\n" % code)

        # LEBench writes the CSV into the current directory, named after the kernel
        produced = "output.%s.csv" % ev["kernel"]
        if os.path.exists(produced):
            os.replace(produced, os.path.join(run_dir, produced))

        print("run %d/%d  exit=%d  wall=%.1fs" % (i, args.runs, code, elapsed))
        if code != 0:
            sys.exit("run %d failed; inspect %s" % (i, stderr_path))
        if not os.path.exists(os.path.join(run_dir, produced)):
            sys.exit("run %d produced no CSV; is the binary the LEBench one?" % i)
        per_run.append(parse_kbest(os.path.join(run_dir, produced)))

    tests = sorted(set().union(*[set(r) for r in per_run]))
    with open(os.path.join(dest, "summary.csv"), "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["test", "mean_ns", "stdev_ns", "n"] +
                        ["run%d_ns" % (i + 1) for i in range(len(per_run))])
        for test in tests:
            values = [r[test] for r in per_run if test in r]
            if not values:
                continue
            mean, sd = mean_sd(values)
            writer.writerow([test, "%.3f" % mean, "%.3f" % sd, len(values)] +
                            ["%.3f" % v for v in values])

    print("\nwrote %s" % os.path.join(dest, "summary.csv"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
