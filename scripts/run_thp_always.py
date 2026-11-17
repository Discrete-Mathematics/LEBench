#!/usr/bin/env python3
"""One extra THP level: always, then restore madvise."""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_thp_extension as thp
import vm_kernel_sweep as sweep

SCRIPT = r"""
set -e
echo always > /sys/kernel/mm/transparent_hugepage/enabled
echo SET $(cat /sys/kernel/mm/transparent_hugepage/enabled)
dest=/home/lebench/LEBench/results/thp/always
rm -rf "$dest"
bash /home/lebench/LEBench/course/run_reduced.sh 4.4.0-210-generic "$dest"
{
  echo "thp_setting: always"
  echo "thp_enabled: $(cat /sys/kernel/mm/transparent_hugepage/enabled)"
  echo "thp_defrag: $(cat /sys/kernel/mm/transparent_hugepage/defrag)"
} >> "$dest/environment.txt"
echo madvise > /sys/kernel/mm/transparent_hugepage/enabled
echo RESTORED $(cat /sys/kernel/mm/transparent_hugepage/enabled)
chown -R lebench:lebench /home/lebench/LEBench/results/thp
"""


def main():
    secret = thp.password()
    code, out, err = sweep.sudo_script(secret, SCRIPT, 300)
    print("exit", code, flush=True)
    print(out[-800:], flush=True)
    if code != 0:
        print(err[-400:], flush=True)
        raise SystemExit("always run failed")
    thp.pull("always")


if __name__ == "__main__":
    main()
