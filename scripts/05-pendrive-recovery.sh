#!/bin/bash
# Pendrive de RECOVERY (internet install, ~850 MB de BaseSystem.dmg) — serve em
# qualquer pendrive de 8 GB+, inclusive os de 14/15 GB que não caberiam o .app
# completo de 15,7 GB. Durante a instalação o restante é baixado da Apple,
# então a Ethernet precisa estar funcionando (não há Wi-Fi neste build).
#
# Uso: ./scripts/05-pendrive-recovery.sh diskN
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DISK="${1:-}"
SRC="$ROOT/_downloads/com.apple.recovery.boot"

[[ -n "$DISK" ]] || { echo "Uso: $0 diskN"; diskutil list; exit 1; }
[[ -b "/dev/$DISK" ]] || { echo "ERRO: disco inválido"; exit 1; }
[[ -f "$SRC/BaseSystem.dmg" ]] || { echo "ERRO: rode ./scripts/01-baixar-macos.sh antes"; exit 1; }

diskutil list
read -r -p "Confirma APAGAR /dev/$DISK? Digite APAGAR: " ok
[[ "$ok" == "APAGAR" ]] || exit 1

# GPT cria automaticamente a partição EFI (200 MB) + a partição de dados FAT32.
# FAT32 é o único formato que o OpenCore lê no pendrive E que aceita o
# BaseSystem.dmg (847 MB) sem problema de tamanho.
echo ">>> Formatando /dev/$DISK (GPT + FAT32)"
sudo diskutil eraseDisk MS-DOS OPENCORE GPT "/dev/$DISK"
sleep 2

echo ">>> Copiando recovery (847 MB, pode demorar em USB 2.0)"
sudo mkdir -p /Volumes/OPENCORE/com.apple.recovery.boot
sudo cp "$SRC/BaseSystem.dmg" "$SRC/BaseSystem.chunklist" /Volumes/OPENCORE/com.apple.recovery.boot/

echo ">>> Montando EFI e copiando OpenCore"
EFI_DEV="$(diskutil list "/dev/$DISK" | awk '/EFI/ {print $NF; exit}')"
sudo diskutil mount "/dev/$EFI_DEV"
sudo rm -rf /Volumes/EFI/EFI
sudo ditto "$ROOT/EFI" /Volumes/EFI/EFI

"$ROOT/ocvalidate" /Volumes/EFI/EFI/OC/config.plist
echo
echo "PRONTO."
echo "  Recovery: /Volumes/OPENCORE/com.apple.recovery.boot"
echo "  EFI:      /Volumes/EFI/EFI"
echo "Boot pelo pendrive -> OpenCore -> 'Install macOS Sequoia'"
diskutil eject "/dev/$DISK" || true
