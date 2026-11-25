#!/bin/bash
# Build vanilla Linux 4.20.13 with the paper's eleven-cause edits that apply
# to that version. Waits until the BASE_ITER 10000 run is finished so the
# two jobs do not share the guest.
set -u
ROOT=/home/lebench/LEBench
OUT=$ROOT/results/eleven
mkdir -p "$OUT" /home/lebench/src
exec >> "$OUT/driver.log" 2>&1
echo "START $(date -u +%Y-%m-%dT%H:%M:%SZ)"

while pgrep -f '/home/lebench/LEBench/course/full_bench' >/dev/null \
   || pgrep -f 'run_fulliter.sh' >/dev/null; do
  echo "WAIT_BENCH $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  sleep 30
done
echo "BENCH_IDLE $(date -u +%Y-%m-%dT%H:%M:%SZ)"

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y build-essential bc flex bison libssl-dev libelf-dev dpkg-dev wget xz-utils patch rsync

if ! swapon --show | grep -q /swap-eleven; then
  fallocate -l 6G /swap-eleven || dd if=/dev/zero of=/swap-eleven bs=1M count=6144
  chmod 600 /swap-eleven
  mkswap /swap-eleven
  swapon /swap-eleven
fi
echo "SWAP $(swapon --show)"

cd /home/lebench/src
if [ ! -f linux-4.20.13.tar.xz ]; then
  wget -O linux-4.20.13.tar.xz https://cdn.kernel.org/pub/linux/kernel/v4.x/linux-4.20.13.tar.xz
fi
if [ ! -d linux-4.20.13 ]; then
  tar -xf linux-4.20.13.tar.xz
fi
cd linux-4.20.13
cp /boot/config-4.20.13-042013-generic .config
make olddefconfig
cp .config "$OUT/config.before"

./scripts/config --disable PAGE_TABLE_ISOLATION
./scripts/config --disable RETPOLINE
./scripts/config --disable SLAB_FREELIST_RANDOM
./scripts/config --disable HARDENED_USERCOPY
./scripts/config --disable MEMCG
./scripts/config --disable USERFAULTFD
./scripts/config --disable CONTEXT_TRACKING_FORCE
./scripts/config --disable TRANSPARENT_HUGEPAGE_MADVISE
./scripts/config --enable TRANSPARENT_HUGEPAGE
./scripts/config --enable TRANSPARENT_HUGEPAGE_ALWAYS
make olddefconfig
if grep -q '^CONFIG_TRANSPARENT_HUGEPAGE_ALWAYS=y' .config; then
  echo "THP_ALWAYS selected"
else
  echo "THP_ALWAYS not selected"
fi
cp .config "$OUT/config.after"
echo "CONFIG_DIFF"
diff -u "$OUT/config.before" "$OUT/config.after" | head -n 200 || true

mkdir -p "$OUT/patches"
wget -O "$OUT/patches/fault-around-4.20.13.patch" \
  https://raw.githubusercontent.com/LinuxPerfStudy/ExperimentSetup/master/root_causes/fault_around/0001-Disable-fault-around-4.20.13.patch
wget -O "$OUT/patches/tlb-layout.patch" \
  https://raw.githubusercontent.com/LinuxPerfStudy/ExperimentSetup/master/root_causes/tlb_layout/0001-Update-TLB-spec1.patch
if patch -p1 --dry-run < "$OUT/patches/fault-around-4.20.13.patch"; then
  patch -p1 < "$OUT/patches/fault-around-4.20.13.patch"
  echo "FAULT_AROUND applied"
else
  echo "FAULT_AROUND failed"
fi
if patch -p1 --dry-run < "$OUT/patches/tlb-layout.patch"; then
  patch -p1 < "$OUT/patches/tlb-layout.patch"
  echo "TLB_LAYOUT applied"
else
  echo "TLB_LAYOUT failed"
fi
echo "IDLE_STATES skipped: the published patches are intel_idle Haswell backports for 3.3.6, 3.6.10, and 3.8.10. This guest is a VirtualBox i7-13700H, and the tree is 4.20.13."

echo "MAKE_START $(date -u +%Y-%m-%dT%H:%M:%SZ)"
if make -j2 bindeb-pkg LOCALVERSION=-eleven; then
  echo "MAKE_OK $(date -u +%Y-%m-%dT%H:%M:%SZ)"
else
  echo "MAKE_FAIL $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  exit 1
fi
ls -lh /home/lebench/src/*.deb
echo "BUILD_DONE $(date -u +%Y-%m-%dT%H:%M:%SZ)"
