#!/bin/bash
# Monta a partição EFI de um disco (pendrive ou disco interno) para copiar o EFI
# Uso: ./scripts/03-montar-efi.sh disk6
set -euo pipefail
DISK="${1:-}"
[[ -n "$DISK" ]] || { echo "Uso: $0 diskN"; diskutil list; exit 1; }
EFI_DEV="$(diskutil list "/dev/$DISK" | awk '/EFI/ {print $NF; exit}')"
[[ -n "$EFI_DEV" ]] || { echo "ERRO: nenhuma partição EFI em /dev/$DISK"; exit 1; }
sudo diskutil mount "/dev/$EFI_DEV"
echo "EFI montada em /Volumes/EFI (device $EFI_DEV)"
ls -la /Volumes/EFI
