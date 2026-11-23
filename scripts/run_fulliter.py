#!/usr/bin/env python3
"""Three BASE_ITER 10000 runs on the booted 4.4.0-210 guest."""

import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vm_kernel_sweep as sweep

ROOT = sweep.ROOT


def env():
    copied = os.environ.copy()
    copied["SSH_ASKPASS"] = r"D:\VMs\LEBench\askpass.cmd"
    copied["SSH_ASKPASS_REQUIRE"] = "force"
    copied["DISPLAY"] = "none"
    return copied


def password():
    value = os.environ.get("LEBENCH_VM_PASSWORD")
    if value:
        return value
    text = Path(r"D:\VMs\LEBench\LOGIN.txt").read_text(encoding="utf-8")
    match = re.search(r"Password:\s*(\S+)", text)
    if not match:
        raise SystemExit("password not found")
    return match.group(1)


def scp(local, remote):
    completed = subprocess.run(
        [
            "scp",
            "-P",
            "2222",
            "-o",
            "StrictHostKeyChecking=accept-new",
            "-o",
            "PreferredAuthentications=password",
            "-o",
            "PubkeyAuthentication=no",
            str(local),
            "lebench@127.0.0.1:" + remote,
        ],
        env=env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
    )
    print("scp", local.name, completed.returncode, flush=True)
    if completed.returncode != 0:
        print(completed.stderr.decode("utf-8", "replace")[-400:], flush=True)
        raise SystemExit("scp failed")


def pull():
    destination = ROOT / "results" / "fulliter" / "4.4.0-210-generic"
    destination.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [
            "scp",
            "-r",
            "-P",
            "2222",
            "-o",
            "StrictHostKeyChecking=accept-new",
            "-o",
            "PreferredAuthentications=password",
            "-o",
            "PubkeyAuthentication=no",
            "lebench@127.0.0.1:/home/lebench/LEBench/results/fulliter/4.4.0-210-generic/.",
            str(destination),
        ],
        env=env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=180,
    )
    print("pull", completed.returncode, flush=True)
    if completed.returncode != 0:
        print(completed.stderr.decode("utf-8", "replace")[-500:], flush=True)


def main():
    if sweep.uname() is None:
        print("starting VM", flush=True)
        sweep.vbox("startvm", "LEBench", "--type", "gui")
    deadline = time.time() + 240
    while time.time() < deadline and sweep.uname() is None:
        time.sleep(5)
    current = sweep.uname()
    print("uname", current, flush=True)
    if current != "4.4.0-210-generic":
        raise SystemExit("expected the recovery kernel, got %s" % current)

    scp(ROOT / "course" / "OS_Eval_fulliter.c", "/home/lebench/LEBench/course/OS_Eval_fulliter.c")
    scp(ROOT / "course" / "run_fulliter.sh", "/home/lebench/LEBench/course/run_fulliter.sh")
    script = r"""
set -e
sed -i 's/\r$//' /home/lebench/LEBench/course/run_fulliter.sh /home/lebench/LEBench/course/OS_Eval_fulliter.c
gcc -O0 -pthread -o /home/lebench/LEBench/course/full_bench /home/lebench/LEBench/course/OS_Eval_fulliter.c
echo COMPILED
bash /home/lebench/LEBench/course/run_fulliter.sh 4.4.0-210-generic /home/lebench/LEBench/results/fulliter/4.4.0-210-generic
chown -R lebench:lebench /home/lebench/LEBench/results/fulliter /home/lebench/LEBench/course/full_bench
"""
    code, out, err = sweep.sudo_script(password(), script, 14400)
    print("fulliter exit", code, flush=True)
    print(out[-1500:], flush=True)
    if err.strip():
        print(err[-800:], flush=True)
    pull()
    if code != 0:
        raise SystemExit("fulliter run failed")


if __name__ == "__main__":
    main()
