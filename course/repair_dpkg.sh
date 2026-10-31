#!/bin/bash
set -x
ps aux | grep -E 'dpkg|wget|apt-get' | grep -v grep || true
killall -9 wget dpkg apt-get 2>/dev/null || true
sleep 1
rm -f /var/lib/dpkg/lock /var/lib/dpkg/lock-frontend /var/cache/apt/archives/lock /var/lib/apt/lists/lock
if [ -f /var/lib/dpkg/updates/0001 ]; then
  echo '--- updates/0001 head ---'
  head -c 120 /var/lib/dpkg/updates/0001 | od -c | head -8
  if grep -q '#padding' /var/lib/dpkg/updates/0001 || ! dpkg --audit >/dev/null 2>&1; then
    rm -f /var/lib/dpkg/updates/*
  fi
fi
export DEBIAN_FRONTEND=noninteractive
dpkg --configure -a || true
apt-get install -y -f || true
apt-get install -y module-init-tools wireless-crda || true
echo '--- vmlinuz ---'
ls -1 /boot/vmlinuz-* || true
echo '--- debs ---'
ls -lh /var/tmp/kernels/ 2>/dev/null || true
echo REPAIR_DONE
