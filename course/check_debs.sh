#!/bin/bash
for f in /var/tmp/kernels/*.deb; do
  echo "==== $f"
  dpkg-deb -I "$f" 2>&1 | awk '/^ Package:|^ Version:|^ Architecture:/{print}'
  echo "size $(stat -c%s "$f")"
done
