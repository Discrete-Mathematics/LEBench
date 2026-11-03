#!/usr/bin/env python3
"""Boot the guest and run the batched-getpid binary three times.

Runs on the kernel that comes up, then once on 4.0.5 if that kernel is
installed. Results land in results/batching/<release>/.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vm_kernel_sweep as sweep

ROOT = sweep.ROOT
TARGETS = ["4.4.0-210-generic", "4.0.5-040005-generic"]


def scp_to(local, remote):
    env = os.environ.copy()
    env["SSH_ASKPASS"] = r"D:\VMs\LEBench\askpass.cmd"
    env["SSH_ASKPASS_REQUIRE"] = "force"
    env["DISPLAY"] = "none"
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
            "lebench@127.0.0.1:%s" % remote,
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
    )
    if completed.returncode != 0:
        raise SystemExit(completed.stderr.decode("utf-8", "replace")[-500:])


def pull(release):
    destination = ROOT / "results" / "batching" / release
    destination.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["SSH_ASKPASS"] = r"D:\VMs\LEBench\askpass.cmd"
    env["SSH_ASKPASS_REQUIRE"] = "force"
    env["DISPLAY"] = "none"
    remote = "lebench@127.0.0.1:/home/lebench/LEBench/results/batching/%s/*" % release
    subprocess.run(
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
            remote,
            str(destination),
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=180,
    )


def boot_release(password, release):
    if release == sweep.BASE_RELEASE:
        sweep.sudo_script(password, "reboot\n", 30)
    else:
        script = 'grub-reboot "Advanced options for Ubuntu>Ubuntu, with Linux %s"\nreboot\n' % release
        sweep.sudo_script(password, script, 30)
    current = sweep.wait_kernel(release, 180)
    print("booted", current, "wanted", release, flush=True)
    return current


def run_here(password, release):
    script = """
set -e
sed -i 's/\\r$//' /home/lebench/LEBench/course/OS_Eval_batched.c /home/lebench/LEBench/course/run_batched.sh
gcc -O0 -pthread -o /home/lebench/LEBench/course/batched_bench /home/lebench/LEBench/course/OS_Eval_batched.c
chown -R lebench:lebench /home/lebench/LEBench
bash /home/lebench/LEBench/course/run_batched.sh '%s' '/home/lebench/LEBench/results/batching/%s'
chown -R lebench:lebench /home/lebench/LEBench/results
""" % (release, release)
    code, out, err = sweep.sudo_script(password, script, 600)
    print("bench", release, "exit", code, flush=True)
    if code != 0:
        print((out + err)[-800:], flush=True)
    return code == 0


def main():
    password = os.environ.get("LEBENCH_VM_PASSWORD")
    if not password:
        text = Path(r"D:\VMs\LEBench\LOGIN.txt").read_text(encoding="utf-8")
        import re
        match = re.search(r"Password:\s*(\S+)", text)
        if not match:
            raise SystemExit("password not found")
        password = match.group(1)

    if sweep.uname() is None:
        print("starting VM", flush=True)
        sweep.vbox("startvm", "LEBench", "--type", "gui")
        deadline = time.time() + 180
        while time.time() < deadline and sweep.uname() is None:
            time.sleep(5)
    current = sweep.uname()
    print("uname", current, flush=True)
    if current is None:
        raise SystemExit("guest ssh did not come up")

    scp_to(ROOT / "course" / "OS_Eval_batched.c", "/home/lebench/LEBench/course/OS_Eval_batched.c")
    scp_to(ROOT / "course" / "run_batched.sh", "/home/lebench/LEBench/course/run_batched.sh")

    for release in TARGETS:
        if sweep.uname() != release:
            if boot_release(password, release) != release:
                print("skip", release, flush=True)
                continue
        if run_here(password, release):
            pull(release)
            print("pulled", release, flush=True)


if __name__ == "__main__":
    main()
