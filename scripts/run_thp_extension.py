#!/usr/bin/env python3
"""Run the reduced suite twice on 4.4.0-210: current THP, then the other mode.

The third level, always, is scripts/run_thp_always.py. Restore writes the bare
mode word. Writing the whole bracket string is parsed as its first token.
"""

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


def pull(mode):
    destination = ROOT / "results" / "thp" / mode
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
            "lebench@127.0.0.1:/home/lebench/LEBench/results/thp/%s/." % mode,
            str(destination),
        ],
        env=env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=180,
    )
    print("pull", mode, completed.returncode, flush=True)
    if completed.returncode != 0:
        print(completed.stderr.decode("utf-8", "replace")[-500:], flush=True)


def main():
    secret = password()
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

    script = r"""
set -e
if [ ! -x /home/lebench/LEBench/course/sweep_bench ]; then
  gcc -O0 -pthread -o /home/lebench/LEBench/course/sweep_bench /home/lebench/LEBench/course/OS_Eval_reduced.c
fi
thp=/sys/kernel/mm/transparent_hugepage/enabled
test -r "$thp"
original=$(cat "$thp")
echo "ORIGINAL $original"
mode_of() {
  echo "$1" | sed -n 's/.*\[\(always\|madvise\|never\)\].*/\1/p'
}
current=$(mode_of "$original")
if [ "$current" = "never" ]; then other=always; else other=never; fi
echo "CURRENT_MODE $current"
echo "OTHER_MODE $other"
run_mode() {
  name="$1"
  setting="$2"
  echo "$setting" > "$thp"
  readback=$(cat "$thp")
  echo "SET $name $readback"
  dest="/home/lebench/LEBench/results/thp/$name"
  rm -rf "$dest"
  bash /home/lebench/LEBench/course/run_reduced.sh "4.4.0-210-generic" "$dest"
  {
    echo "thp_setting: $setting"
    echo "thp_enabled: $(cat "$thp")"
    if [ -r /sys/kernel/mm/transparent_hugepage/defrag ]; then
      echo "thp_defrag: $(cat /sys/kernel/mm/transparent_hugepage/defrag)"
    fi
  } >> "$dest/environment.txt"
}
run_mode "$current" "$current"
run_mode "$other" "$other"
echo "$current" > "$thp"
echo "RESTORED $(cat "$thp")"
chown -R lebench:lebench /home/lebench/LEBench/results/thp
"""
    code, out, err = sweep.sudo_script(secret, script, 900)
    print("thp exit", code, flush=True)
    print(out[-2000:], flush=True)
    if err.strip():
        print(err[-800:], flush=True)
    if code != 0:
        raise SystemExit("thp run failed")
    for line in out.splitlines():
        if line.startswith("CURRENT_MODE ") or line.startswith("OTHER_MODE "):
            pull(line.split()[1])


if __name__ == "__main__":
    main()
