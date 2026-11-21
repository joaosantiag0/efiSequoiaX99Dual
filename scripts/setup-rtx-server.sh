#!/bin/bash
# Roda como root no servidor: grava EFI no SSD interno e instala o driver NVIDIA
set -e

echo "=== 1) EFI no SSD interno (disk0s1) ==="
diskutil unmount /Volumes/EFI 2>/dev/null || true
newfs_msdos -v EFI -F 32 /dev/rdisk0s1 >/dev/null
mkdir -p /Volumes/EFI
diskutil mount /dev/disk0s1 >/dev/null
rm -rf /Volumes/EFI/EFI
tar xzf /tmp/efi-rtx.tar.gz -C /Volumes/EFI
echo "conteudo gravado:"
ls /Volumes/EFI/EFI /Volumes/EFI/EFI/OC
echo "boot-args na EFI:"
/usr/libexec/PlistBuddy -c "Print :NVRAM:Add:7C436110-AB2A-4BBB-A880-FE41995C9F82:boot-args" /Volumes/EFI/EFI/OC/config.plist

echo
echo "=== 2) Driver NullMoth 3.0 ==="
rm -rf /tmp/nvdrv && mkdir -p /tmp/nvdrv
tar xzf /tmp/nullmoth-nvidia-3.0.tar.gz -C /tmp/nvdrv
cd /tmp/nvdrv/pkgroot
echo "-- checksum --"
shasum -a 256 -c SHA256SUMS 2>&1 | tail -3
echo "-- install.sh --"
./install.sh 2>&1 | tail -45

echo
echo "=== 3) Estado ==="
kmutil showloaded --list-only 2>/dev/null | grep -ci nullmoth || true
