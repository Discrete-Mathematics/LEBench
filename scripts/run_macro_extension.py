#!/usr/bin/env python3
"""Install the Claim 3 stack and run default vs spectre_v2=off on the guest."""

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


def scp_to(local, remote):
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
        env=env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=180,
    )
    if completed.returncode != 0:
        raise SystemExit(completed.stderr.decode("utf-8", "replace")[-800:])


def pull_tree():
    destination = ROOT / "results" / "macro"
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
            "lebench@127.0.0.1:/home/lebench/LEBench/results/macro/.",
            str(destination),
        ],
        env=env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=300,
    )
    print("pull exit", completed.returncode, flush=True)
    if completed.returncode != 0:
        print(completed.stderr.decode("utf-8", "replace")[-800:], flush=True)


def password():
    value = os.environ.get("LEBENCH_VM_PASSWORD")
    if value:
        return value
    text = Path(r"D:\VMs\LEBench\LOGIN.txt").read_text(encoding="utf-8")
    match = re.search(r"Password:\s*(\S+)", text)
    if not match:
        raise SystemExit("password not found")
    return match.group(1)


def ensure_guest():
    if sweep.uname() is None:
        print("starting VM", flush=True)
        sweep.vbox("startvm", "LEBench", "--type", "gui")
    deadline = time.time() + 240
    while time.time() < deadline:
        current = sweep.uname()
        if current:
            print("uname", current, flush=True)
            return current
        time.sleep(5)
    raise SystemExit("guest ssh did not come up")


def main():
    secret = password()
    ensure_guest()
    remote_dir = "/home/lebench/LEBench/macrobench"
    sweep.ssh("mkdir -p %s /home/lebench/LEBench/results/macro" % remote_dir, 30)
    for name in (
        "install_guest.sh",
        "run_macrobench.sh",
        "parse_macrobench.py",
        "plan.md",
        "README.md",
    ):
        scp_to(ROOT / "macrobench" / name, remote_dir + "/" + name)
    install = r"""
set -e
sed -i 's/\r$//' /home/lebench/LEBench/macrobench/*.sh /home/lebench/LEBench/macrobench/*.py
chmod 755 /home/lebench/LEBench/macrobench/*.sh
bash /home/lebench/LEBench/macrobench/install_guest.sh
"""
    code, out, err = sweep.sudo_script(secret, install, 1800)
    print("install exit", code, flush=True)
    print((out + err)[-1500:], flush=True)
    if code != 0:
        raise SystemExit("install failed")
    run = r"""
set -e
bash /home/lebench/LEBench/macrobench/run_macrobench.sh --config default --runs 3
chown -R lebench:lebench /home/lebench/LEBench/results
"""
    code, out, err = sweep.sudo_script(secret, run, 2400)
    print("default exit", code, flush=True)
    print((out + err)[-1500:], flush=True)
    if code != 0:
        raise SystemExit("default run failed")
    pull_tree()


if __name__ == "__main__":
    main()
