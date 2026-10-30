#!/usr/bin/env python3
"""Build and run LEBench on the kernel that is booted now.

The upstream run.py harness reboots through every installed kernel.
This entry point is the reduced-scale path for the course reproduction:
it compiles OS_Eval, repeats the suite, and stores stdout, stderr, the
CSV, and a version record under results/. Paths are taken from this
repository, not hard-coded to a home directory.
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TEST_DIR = REPO_ROOT / "TEST_DIR"
BINARY = TEST_DIR / "OS_Eval"


def capture(command):
    """Return stdout of command, or a short failure note."""
    try:
        completed = subprocess.run(
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except OSError as exc:
        return "%s: %s" % (" ".join(command), exc)
    text = completed.stdout.strip()
    if completed.returncode != 0:
        return "%s exited %d\n%s" % (" ".join(command), completed.returncode, text)
    return text


def write_environment(path, kernel):
    lines = [
        "timestamp_utc: %s" % datetime.now(timezone.utc).isoformat(),
        "kernel: %s" % kernel,
        "platform: %s" % (platform.platform(),),
        "uname: %s" % (platform.uname(),),
        "python: %s" % sys.version.replace("\n", " "),
        "",
        "$ gcc --version",
        capture(["gcc", "--version"]),
        "",
        "$ make --version",
        capture(["make", "--version"]),
        "",
        "$ python3 --version",
        capture(["python3", "--version"]),
        "",
        "$ cat /etc/os-release",
        capture(["cat", "/etc/os-release"]),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def build():
    subprocess.check_call(["make", "-C", str(TEST_DIR)])
    if not BINARY.is_file():
        raise SystemExit("make finished but %s is missing" % BINARY)


def run_once(run_dir, kernel, env):
    run_dir.mkdir(parents=True)
    stdout_path = run_dir / "stdout.txt"
    stderr_path = run_dir / "stderr.txt"
    with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open(
        "w", encoding="utf-8"
    ) as stderr:
        return_code = subprocess.call(
            [str(BINARY), "0", kernel],
            cwd=str(REPO_ROOT),
            env=env,
            stdout=stdout,
            stderr=stderr,
        )
    (run_dir / "exit_code.txt").write_text("%d\n" % return_code, encoding="utf-8")

    csv_name = "output.%s.csv" % kernel
    produced = REPO_ROOT / csv_name
    if produced.is_file():
        shutil.move(str(produced), str(run_dir / csv_name))
    return return_code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runs",
        type=int,
        default=3,
        help="independent process repetitions (default: 3)",
    )
    parser.add_argument(
        "--label",
        default=None,
        help="directory name under results/ (default: kernel release)",
    )
    args = parser.parse_args()
    if args.runs < 1:
        raise SystemExit("--runs must be at least 1")

    if platform.system() != "Linux":
        raise SystemExit(
            "OS_Eval uses Linux-only system calls and must be run on Linux "
            "(current system: %s). Build the image in setup/Dockerfile or "
            "use a Linux machine, then re-run this script."
            % platform.system()
        )

    if hasattr(os, "geteuid") and os.geteuid() != 0:
        print(
            "warning: context-switch tests raise their priority and may be "
            "noisy without root. Re-run with sudo for measurements that will "
            "be compared with the paper.",
            file=sys.stderr,
        )

    build()
    kernel = platform.release()
    label = args.label or kernel
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    batch = REPO_ROOT / "results" / label / stamp
    batch.mkdir(parents=True)
    write_environment(batch / "environment.txt", kernel)

    env = os.environ.copy()
    # OS_Eval concatenates this prefix onto "output_file.csv" and
    # "/TEST_DIR/socket", so the trailing separator is required.
    env["LEBENCH_DIR"] = str(REPO_ROOT) + os.sep

    print("writing logs to %s" % batch)
    for index in range(1, args.runs + 1):
        print("starting run %d of %d" % (index, args.runs))
        return_code = run_once(batch / ("run%d" % index), kernel, env)
        if return_code != 0:
            raise SystemExit("run %d exited %d; logs kept in %s" % (index, return_code, batch))

    summary = REPO_ROOT / "scripts" / "summarize_runs.py"
    subprocess.check_call([sys.executable, str(summary), str(batch)])
    print("finished %d run(s) under %s" % (args.runs, batch))


if __name__ == "__main__":
    main()
