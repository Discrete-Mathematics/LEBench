#!/bin/bash
set -e
update-grub
grub-reboot 'LEBench nopti'
reboot
