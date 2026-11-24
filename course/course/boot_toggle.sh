#!/bin/sh
# One-shot kernel command-line switch for the claim-2 experiments.
#
#   sudo ./boot_toggle.sh --add cgroup_disable=memory
#   sudo ./boot_toggle.sh --restore
#   sudo ./boot_toggle.sh --status
#
# Why this is a separate script from run_toggle.py: a wrong GRUB edit is how the
# guest's disk was lost once (2026-11-21). This script therefore
#   * accepts only a whitelist of parameters that cannot make the kernel
#     unbootable,
#   * backs up /etc/default/grub before touching it,
#   * never installs GRUB onto a disk and never calls grub-install,
#   * prints the resulting command line before rebooting.
#
# The parameter is persistent until --restore. Run one arm of the experiment,
# restore, run the other arm.

set -e

GRUB_FILE=/etc/default/grub
BACKUP_DIR=/root/grub-backups
MARKER="cs340-toggle"

ALLOWED="pti=off spectre_v2=off cgroup_disable=memory"

usage() {
    echo "usage: $0 --add <param> | --restore | --status | --dry-run --add <param>"
    echo "allowed parameters: $ALLOWED"
    exit 1
}

require_root() {
    [ "$(id -u)" -eq 0 ] || { echo "run as root" >&2; exit 1; }
}

current_cmdline() {
    grep '^GRUB_CMDLINE_LINUX_DEFAULT=' "$GRUB_FILE" | cut -d'"' -f2
}

case "$1" in
    --status)
        echo "file    : $GRUB_FILE"
        echo "cmdline : $(current_cmdline)"
        echo "running : $(cat /proc/cmdline)"
        exit 0
        ;;
    --dry-run)
        DRY=1; shift
        ;;
    --add)
        DRY=0; PARAM="$2"; shift 2
        ;;
    --restore)
        require_root
        if [ -f "$BACKUP_DIR/latest" ]; then
            cp "$(cat "$BACKUP_DIR/latest")" "$GRUB_FILE"
            update-grub
            echo "restored $GRUB_FILE from $(cat "$BACKUP_DIR/latest")"
            echo "reboot to apply: shutdown -r now"
        else
            echo "no backup found in $BACKUP_DIR" >&2
            exit 1
        fi
        exit 0
        ;;
    *)
        usage
        ;;
esac

[ -n "$PARAM" ] || usage

case " $ALLOWED " in
    *" $PARAM "*) : ;;
    *) echo "refusing unknown parameter: $PARAM" >&2; usage ;;
esac

if [ "$DRY" -eq 0 ]; then require_root; fi

mkdir -p "$BACKUP_DIR"
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
cp "$GRUB_FILE" "$BACKUP_DIR/grub.$STAMP"
echo "$BACKUP_DIR/grub.$STAMP" > "$BACKUP_DIR/latest"

OLD=$(current_cmdline)
case "$OLD" in
    *"$PARAM"*) NEW="$OLD" ;;
    *) NEW="$OLD $PARAM" ;;
esac

echo "old cmdline: $OLD"
echo "new cmdline: $NEW"

if [ "$DRY" -eq 1 ]; then
    echo "(dry run: nothing written)"
    exit 0
fi

sed -i "s|^GRUB_CMDLINE_LINUX_DEFAULT=.*|GRUB_CMDLINE_LINUX_DEFAULT=\"$NEW\"|" "$GRUB_FILE"
update-grub

echo
echo "GRUB updated. The switch takes effect after a reboot:"
echo "    shutdown -r now"
echo "Then verify with:  cat /proc/cmdline"
echo "Undo with:         $0 --restore"
