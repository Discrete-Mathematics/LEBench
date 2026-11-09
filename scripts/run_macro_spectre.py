#!/usr/bin/env python3
"""Boot 4.4.0-210 with spectre_v2=off and run the Claim 3 suite three times."""

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
        timeout=120,
    )
    if completed.returncode != 0:
        raise SystemExit(completed.stderr.decode("utf-8", "replace")[-500:])


def main():
    secret = password()
    scp_to(ROOT / "macrobench" / "run_macrobench.sh", "/home/lebench/LEBench/macrobench/run_macrobench.sh")
    boot = r"""
set -e
sed -i 's/\r$//' /home/lebench/LEBench/macrobench/run_macrobench.sh
cat > /etc/grub.d/40_custom <<'EOF'
#!/bin/sh
exec tail -n +3 $0
menuentry 'LEBench nopti' {
    recordfail
    load_video
    insmod gzio
    insmod part_msdos
    insmod ext2
    set root='hd0,msdos1'
    search --no-floppy --fs-uuid --set=root 3984d9d0-fbe8-49bf-9bf9-95cd695fd9a3
    linux /boot/vmlinuz-4.4.0-210-generic root=UUID=3984d9d0-fbe8-49bf-9bf9-95cd695fd9a3 ro quiet nopti
    initrd /boot/initrd.img-4.4.0-210-generic
}
menuentry 'LEBench spectreoff' {
    recordfail
    load_video
    insmod gzio
    insmod part_msdos
    insmod ext2
    set root='hd0,msdos1'
    search --no-floppy --fs-uuid --set=root 3984d9d0-fbe8-49bf-9bf9-95cd695fd9a3
    linux /boot/vmlinuz-4.4.0-210-generic root=UUID=3984d9d0-fbe8-49bf-9bf9-95cd695fd9a3 ro quiet spectre_v2=off
    initrd /boot/initrd.img-4.4.0-210-generic
}
EOF
chmod 755 /etc/grub.d/40_custom
update-grub
grub-reboot 'LEBench spectreoff'
reboot
"""
    sweep.sudo_script(secret, boot, 120)
    deadline = time.time() + 40
    while time.time() < deadline and sweep.uname() is not None:
        time.sleep(2)
    current = sweep.wait_kernel("4.4.0-210-generic", 180)
    print("booted", current, flush=True)
    code, out, err = sweep.ssh("cat /proc/cmdline", 30)
    print(out, err, flush=True)
    if "spectre_v2=off" not in out:
        raise SystemExit("spectre_v2=off did not appear on the command line")
    run = r"""
set -e
bash /home/lebench/LEBench/macrobench/run_macrobench.sh --config spectre-off --runs 3
chown -R lebench:lebench /home/lebench/LEBench/results
"""
    code, out, err = sweep.sudo_script(secret, run, 2400)
    print("spectre exit", code, flush=True)
    print((out + err)[-1200:], flush=True)
    if code != 0:
        raise SystemExit("spectre-off run failed")
    sweep.sudo_script(secret, "reboot\n", 30)


if __name__ == "__main__":
    main()
