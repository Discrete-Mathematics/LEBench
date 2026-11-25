#!/usr/bin/env python3
"""Resume the interrupted 4.20.13 build after selecting THP always."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_fulliter as full
import vm_kernel_sweep as sweep

SCRIPT = r"""
set -e
if swapon --show | grep -q /swap-eleven; then
  echo SWAP_ON
else
  swapon /swap-eleven
  echo SWAP_ADDED
fi
cd /home/lebench/src/linux-4.20.13
./scripts/config --disable TRANSPARENT_HUGEPAGE_MADVISE
./scripts/config --enable TRANSPARENT_HUGEPAGE
./scripts/config --enable TRANSPARENT_HUGEPAGE_ALWAYS
make olddefconfig
echo '--- thp ---'
grep TRANSPARENT_HUGEPAGE .config
echo '--- context ---'
grep CONTEXT_TRACKING .config || true
if ! grep -q '^CONFIG_TRANSPARENT_HUGEPAGE_ALWAYS=y' .config; then
  echo ALWAYS_NOT_SET
  exit 2
fi
LOG=/home/lebench/LEBench/results/eleven/driver.log
echo "MAKE_RESUME $(date -u +%Y-%m-%dT%H:%M:%SZ) thp-always" >> "$LOG"
setsid nohup make -j2 bindeb-pkg LOCALVERSION=-eleven >> "$LOG" 2>&1 </dev/null &
echo STARTED $!
"""


def main():
    if sweep.uname() != "4.4.0-210-generic":
        raise SystemExit("guest is not on the recovery kernel: %s" % sweep.uname())
    code, out, err = sweep.sudo_script(full.password(), SCRIPT, 180)
    print(out)
    if err.strip():
        print(err[-400:])
    print("exit", code)
    if code != 0:
        raise SystemExit("resume did not start")


if __name__ == "__main__":
    main()
