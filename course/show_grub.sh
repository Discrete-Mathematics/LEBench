#!/bin/bash
grep -n "4.4.0-210-generic" /boot/grub/grub.cfg | head -n 20
echo '----- block -----'
awk '
  /menuentry .Ubuntu, with Linux 4.4.0-210-generic/ {show=1}
  show {print}
  show && /initrd / {exit}
' /boot/grub/grub.cfg
