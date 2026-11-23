#!/usr/bin/env python3
"""Copy the eleven-cause build script to the guest and detach it."""

import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_fulliter as full
import vm_kernel_sweep as sweep

ROOT = sweep.ROOT


def main():
    if sweep.uname() != "4.4.0-210-generic":
        raise SystemExit("guest is not on the recovery kernel: %s" % sweep.uname())
    full.scp(ROOT / "course" / "build_eleven.sh", "/home/lebench/LEBench/course/build_eleven.sh")
    script = r"""
set -e
mkdir -p /home/lebench/LEBench/results/eleven
sed -i 's/\r$//' /home/lebench/LEBench/course/build_eleven.sh
chmod 755 /home/lebench/LEBench/course/build_eleven.sh
if pgrep -f '/home/lebench/LEBench/course/build_eleven.sh' >/dev/null; then
  echo ALREADY
  exit 0
fi
setsid nohup bash /home/lebench/LEBench/course/build_eleven.sh \
  >/home/lebench/LEBench/results/eleven/nohup.out 2>&1 </dev/null &
echo STARTED $!
"""
    code, out, err = sweep.sudo_script(full.password(), script, 60)
    print("exit", code)
    print(out)
    if err.strip():
        print(err[-400:])
    if code != 0:
        raise SystemExit("could not start the build")


if __name__ == "__main__":
    main()
