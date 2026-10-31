#!/bin/bash
set -e
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
EOF
chmod 755 /etc/grub.d/40_custom
update-grub
grub-reboot 'LEBench nopti'
reboot
