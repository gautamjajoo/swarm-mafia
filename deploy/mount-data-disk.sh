#!/usr/bin/env bash
set -euo pipefail
# Only operate on the dedicated disk, never on the VM boot device.
device=/dev/disk/by-id/google-swarm-observatory-data
mountpoint=/srv/swarm-observatory
test -b "$device"
if ! sudo blkid "$device" >/dev/null 2>&1; then
  test "$(sudo blockdev --getsize64 "$device")" = 85899345920
  test -z "$(sudo wipefs --noheadings --output TYPE "$device")"
  sudo mkfs.ext4 -L swarm-data "$device"
fi
test "$(sudo blkid -s TYPE -o value "$device")" = ext4
sudo mkdir -p "$mountpoint"
uuid="$(sudo blkid -s UUID -o value "$device")"
if ! grep -q "UUID=$uuid " /etc/fstab; then
  printf 'UUID=%s /srv/swarm-observatory ext4 defaults,nofail,nodev,nosuid 0 2\n' "$uuid" | sudo tee -a /etc/fstab >/dev/null
fi
sudo systemctl daemon-reload
mountpoint -q "$mountpoint" || sudo mount "$mountpoint"
sudo install -d -o jajoo_kairosity_ai -g jajoo_kairosity_ai -m 700 "$mountpoint/data" "$mountpoint/backups"
findmnt "$mountpoint"
df -h "$mountpoint"
