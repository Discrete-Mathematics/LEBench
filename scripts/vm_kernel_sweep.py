#!/usr/bin/env python3
"""Boot each author-listed kernel in the LEBench VM and run the reduced suite.

The guest is Ubuntu 16.04.6 in VirtualBox. GRUB's saved default stays on the
known-good kernel. Each candidate is selected with grub-reboot, which applies
to one boot only, so a panic falls back to the known-good kernel on the next
power-on.

The VM password is read from LEBENCH_VM_PASSWORD or from --password-file.
It is not stored in this repository.
"""

import argparse
import base64
import msvcrt
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VBOX = Path(r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe")
BASE_RELEASE = "4.4.0-210-generic"
RAW_PREFIX = "https://raw.githubusercontent.com/LinuxPerfStudy/ExperimentSetup/master/"


def kernel_list():
    text = (ROOT / "EXPERIMENTS.md").read_text(encoding="utf-8")
    match = re.search(r"`(3\.0\.7-030007-generic,.*4\.20\.13-042013-generic)`", text)
    if not match:
        raise SystemExit("could not read the kernel list in EXPERIMENTS.md")
    return [item.strip() for item in match.group(1).split(",")]


def image_urls():
    listing = Path(r"D:\VMs\LEBench\kernel-image-paths.txt")
    urls = {}
    pattern = re.compile(r"/linux-image-(unsigned-)?(\d+\.\d+\.\d+-\d+-generic)_")
    for line in listing.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        match = pattern.search(line)
        if not match:
            continue
        unsigned, release = match.group(1), match.group(2)
        if release not in urls or not unsigned:
            urls[release] = RAW_PREFIX + line
    return urls


def ssh(command, timeout):
    env = os.environ.copy()
    env["SSH_ASKPASS"] = r"D:\VMs\LEBench\askpass.cmd"
    env["SSH_ASKPASS_REQUIRE"] = "force"
    env["DISPLAY"] = "none"
    completed = subprocess.run(
        [
            "ssh",
            "-p",
            "2222",
            "-o",
            "StrictHostKeyChecking=accept-new",
            "-o",
            "PreferredAuthentications=password",
            "-o",
            "PubkeyAuthentication=no",
            "-o",
            "ConnectTimeout=8",
            "-o",
            "ServerAliveInterval=15",
            "-o",
            "ServerAliveCountMax=3",
            "lebench@127.0.0.1",
            command,
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    return completed.returncode, completed.stdout.decode("utf-8", "replace"), completed.stderr.decode("utf-8", "replace")


def sudo_script(password, script, timeout):
    payload = base64.b64encode(script.encode("utf-8")).decode("ascii")
    command = "echo %s | sudo -S -p '' bash -c 'echo %s | base64 -d | bash'" % (password, payload)
    try:
        return ssh(command, timeout)
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"


def uname():
    try:
        code, out, _err = ssh("uname -r", 20)
    except subprocess.TimeoutExpired:
        return None
    if code != 0:
        return None
    return out.strip()


def wait_kernel(expected, timeout_s):
    """Wait for a reboot. If GRUB falls back to the known-good kernel, return that."""
    drop_deadline = time.time() + 40
    while time.time() < drop_deadline:
        if uname() is None:
            break
        time.sleep(2)
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        current = uname()
        if current == expected:
            return current
        if current == BASE_RELEASE and expected != BASE_RELEASE:
            return current
        time.sleep(5)
    return None


def vbox(*args):
    subprocess.run([str(VBOX), *args], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def recover_base():
    vbox("controlvm", "LEBench", "poweroff")
    time.sleep(3)
    vbox("startvm", "LEBench", "--type", "gui")
    return wait_kernel(BASE_RELEASE, 300)


def log(path, message):
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    line = "%s %s\n" % (stamp, message)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line)
    print(line, end="")


def ensure_grub(password, progress):
    script = r"""
set -e
python3 - <<'PY'
from pathlib import Path
path = Path("/etc/default/grub")
text = path.read_text()
lines = []
for line in text.splitlines():
    if line.startswith("GRUB_DEFAULT=") or line.startswith("#GRUB_DEFAULT="):
        continue
    if line.startswith("GRUB_TIMEOUT=") or line.startswith("GRUB_TIMEOUT_STYLE="):
        continue
    if "HIDDEN_TIMEOUT" in line:
        continue
    lines.append(line)
lines.append('GRUB_DEFAULT="Advanced options for Ubuntu>Ubuntu, with Linux 4.4.0-210-generic"')
lines.append("GRUB_TIMEOUT_STYLE=menu")
lines.append("GRUB_TIMEOUT=3")
path.write_text("\n".join(lines) + "\n")
PY
update-grub
"""
    code, out, err = sudo_script(password, script, 180)
    log(progress, "grub default update exit %s" % code)
    if code != 0:
        log(progress, err[-500:])
        raise SystemExit("could not set the GRUB default")


def modules_url(image_url):
    """4.16+ images are unsigned and depend on a modules package the authors did not ship."""
    if "linux-image-unsigned-" not in image_url:
        return ""
    version_dir = image_url.rstrip("/").split("/")[-2]
    name = image_url.rsplit("/", 1)[-1].replace("linux-image-unsigned-", "linux-modules-", 1)
    return "https://kernel.ubuntu.com/~kernel-ppa/mainline/%s/%s" % (version_dir, name)


def install_and_reboot(password, release, url, progress):
    modules = modules_url(url)
    script = """
set -e
export DEBIAN_FRONTEND=noninteractive
for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
  if ! fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1; then
    break
  fi
  sleep 4
done
if [ -f /var/lib/dpkg/updates/0001 ] && grep -q '#padding' /var/lib/dpkg/updates/0001; then
  rm -f /var/lib/dpkg/updates/* /var/lib/dpkg/lock /var/lib/dpkg/lock-frontend
fi
dpkg --configure -a || true
deb=/var/tmp/kernels/%s.deb
mod='%s'
if [ ! -f /boot/vmlinuz-%s ] || [ ! -f /boot/initrd.img-%s ]; then
  mkdir -p /var/tmp/kernels
  if [ ! -s "$deb" ]; then
    wget -O "$deb.part" '%s'
    mv "$deb.part" "$deb"
  fi
  if [ -n "$mod" ]; then
    mdeb=/var/tmp/kernels/%s.modules.deb
    if [ ! -s "$mdeb" ]; then
      wget -O "$mdeb.part" "$mod"
      mv "$mdeb.part" "$mdeb"
    fi
    dpkg -i "$mdeb" || true
  fi
  dpkg -i "$deb" || apt-get install -y -f
fi
test -f /boot/vmlinuz-%s
test -f /boot/initrd.img-%s
update-grub
grub-reboot "Advanced options for Ubuntu>Ubuntu, with Linux %s"
reboot
""" % (release, modules, release, release, url, release, release, release, release)
    code, out, err = sudo_script(password, script, 1500)
    log(progress, "install %s exit %s" % (release, code))
    if err.strip():
        log(progress, err[-400:].replace("\n", " | "))
    return code, out, err


def run_bench(password, release, progress):
    script = """
set -e
chown -R lebench:lebench /home/lebench/LEBench
bash /home/lebench/LEBench/course/run_reduced.sh '%s' '/home/lebench/LEBench/results/kernels/%s'
chown -R lebench:lebench /home/lebench/LEBench/results
""" % (release, release)
    code, out, err = sudo_script(password, script, 1800)
    log(progress, "bench %s exit %s" % (release, code))
    if code != 0:
        log(progress, (out + err)[-400:].replace("\n", " | "))
    return code == 0


def pull_results(release):
    destination = ROOT / "results" / "kernels" / release
    destination.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["SSH_ASKPASS"] = r"D:\VMs\LEBench\askpass.cmd"
    env["SSH_ASKPASS_REQUIRE"] = "force"
    env["DISPLAY"] = "none"
    remote = "lebench@127.0.0.1:/home/lebench/LEBench/results/kernels/%s/*" % release
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


def reboot_to_base(password):
    sudo_script(password, "reboot\n", 30)


def screenshot(name):
    destination = ROOT / "results" / "kernels" / "screenshots"
    destination.mkdir(parents=True, exist_ok=True)
    vbox("controlvm", "LEBench", "screenshotpng", str(destination / ("%s.png" % name)))


def acquire_lock():
    path = ROOT / "results" / "kernels" / "sweep.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+")
    try:
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        raise SystemExit("another kernel sweep already holds results/kernels/sweep.lock")
    handle.seek(0)
    handle.truncate()
    handle.write("%d\n" % os.getpid())
    handle.flush()
    return handle


def failure_log():
    return ROOT / "results" / "kernels" / "boot-failures.txt"


def already_done(release):
    directory = ROOT / "results" / "kernels" / release
    if all((directory / ("run%d.csv" % index)).is_file() and (directory / ("run%d.csv" % index)).stat().st_size > 0 for index in (1, 2, 3)):
        return True
    text = failure_log().read_text(encoding="utf-8") if failure_log().is_file() else ""
    return release in text.split()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--password-file", default=r"D:\VMs\LEBench\LOGIN.txt")
    parser.add_argument("--limit", type=int, default=0, help="stop after this many kernels (0 means all)")
    args = parser.parse_args()
    password = os.environ.get("LEBENCH_VM_PASSWORD")
    if not password:
        text = Path(args.password_file).read_text(encoding="utf-8")
        match = re.search(r"Password:\s*(\S+)", text)
        if not match:
            raise SystemExit("set LEBENCH_VM_PASSWORD or put Password: in the password file")
        password = match.group(1)

    lock_handle = acquire_lock()
    progress = ROOT / "results" / "kernels" / "progress.log"
    releases = kernel_list()
    first = [
        "4.0.5-040005-generic",
        "4.15.15-041515-generic",
        "4.14.15-041415-generic",
        "4.20.13-042013-generic",
        "4.4.5-040405-generic",
        "4.9.11-040911-generic",
        "4.19.11-041911-generic",
    ]
    releases = [item for item in first if item in releases] + [item for item in releases if item not in first]
    urls = image_urls()
    log(progress, "kernel list has %d entries" % len(releases))
    if uname() != BASE_RELEASE:
        if recover_base() != BASE_RELEASE:
            raise SystemExit("the known-good kernel did not boot")
    ensure_grub(password, progress)

    done = 0
    for release in releases:
        if args.limit and done >= args.limit:
            break
        done += 1
        if already_done(release):
            log(progress, "skip existing %s" % release)
            continue
        url = urls.get(release)
        if not url:
            log(progress, "NO DEB %s" % release)
            continue
        if uname() != BASE_RELEASE:
            if recover_base() != BASE_RELEASE:
                log(progress, "lost the base kernel before %s" % release)
                break
        code, _out, err = install_and_reboot(password, release, url, progress)
        # A reboot often kills SSH with 255, or leaves it until the client
        # timeout (124). Either one can still have landed on the new kernel.
        log(progress, "waiting for %s after install exit %s" % (release, code))
        booted = wait_kernel(release, 180)
        if booted != release and code not in (0, 255, 4294967295, 124):
            log(progress, "INSTALL FAIL %s exit %s" % (release, code))
            if err.strip():
                log(progress, err[-300:].replace("\n", " | "))
            continue
        if booted != release:
            current = uname()
            if code == 124 and current == BASE_RELEASE:
                log(progress, "INSTALL TIMEOUT %s still on %s" % (release, current))
                continue
            screenshot(release.replace("/", "_"))
            log(progress, "BOOT FAIL %s (uname=%s)" % (release, current))
            with failure_log().open("a", encoding="utf-8") as handle:
                handle.write(release + "\n")
            if current != BASE_RELEASE:
                if recover_base() != BASE_RELEASE:
                    log(progress, "could not return to the base kernel")
                    break
            continue
        ok = run_bench(password, release, progress)
        try:
            pull_results(release)
        except (subprocess.TimeoutExpired, OSError) as exc:
            log(progress, "scp failed for %s: %s" % (release, exc))
        if not ok:
            log(progress, "BENCH FAIL %s" % release)
        reboot_to_base(password)
        if wait_kernel(BASE_RELEASE, 300) != BASE_RELEASE:
            if recover_base() != BASE_RELEASE:
                log(progress, "could not return after %s" % release)
                break
    log(progress, "sweep stopped")


if __name__ == "__main__":
    main()
