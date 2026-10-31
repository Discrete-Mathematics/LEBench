#!/usr/bin/env python3
"""Boot the installed kernel once with nopti and repeat the reduced suite."""

import importlib.util
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sweep", ROOT / "scripts" / "vm_kernel_sweep.py")
sweep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sweep)

password = [line.split(":", 1)[1].strip() for line in Path(r"D:\VMs\LEBench\LOGIN.txt").read_text(encoding="utf-8").splitlines() if line.startswith("Password:")][0]
script = (ROOT / "course" / "boot_nopti.sh").read_text(encoding="utf-8").replace("\r\n", "\n")
code, _out, err = sweep.sudo_script(password, script, 180)
print("grub-reboot exit", code)
if err.strip():
    print(err[-400:])

deadline = time.time() + 300
cmdline = ""
while time.time() < deadline:
    try:
        status, out, _err = sweep.ssh("cat /proc/cmdline", 20)
    except Exception as exc:
        print("waiting", exc)
        time.sleep(5)
        continue
    cmdline = out.strip()
    print("cmdline", cmdline)
    if status == 0 and "nopti" in cmdline:
        break
    time.sleep(5)
else:
    raise SystemExit("nopti boot did not come up")

if not sweep.run_bench(password, "4.4.0-210-nopti", ROOT / "results" / "kernels" / "progress.log"):
    raise SystemExit("nopti benchmark failed")
sweep.pull_results("4.4.0-210-nopti")
sweep.reboot_to_base(password)
if sweep.wait_kernel(sweep.BASE_RELEASE, 300) != sweep.BASE_RELEASE:
    raise SystemExit("did not return to the base kernel")
print("extension done", cmdline)
