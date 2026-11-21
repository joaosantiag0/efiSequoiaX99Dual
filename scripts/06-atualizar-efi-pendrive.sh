#!/bin/bash
# Atualiza SÓ o EFI de um pendrive já preparado (não apaga o recovery).
# Use depois de mudar o config.plist ou as kexts.
#
# Uso: ./scripts/06-atualizar-efi-pendrive.sh        (usa /Volumes/EFI)
#      ./scripts/06-atualizar-efi-pendrive.sh disk6  (monta a EFI de disk6 antes)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DISK="${1:-}"

if [[ -n "$DISK" ]]; then
  EFI_DEV="$(diskutil list "/dev/$DISK" | awk '/EFI/ {print $NF; exit}')"
  [[ -n "$EFI_DEV" ]] || { echo "ERRO: sem partição EFI em /dev/$DISK"; exit 1; }
  sudo diskutil mount "/dev/$EFI_DEV"
fi

[[ -d /Volumes/EFI ]] || { echo "ERRO: /Volumes/EFI não está montada. Passe o diskN."; exit 1; }

echo ">>> Validando antes de copiar"
"$ROOT/ocvalidate" "$ROOT/EFI/OC/config.plist"

echo ">>> Copiando EFI para o pendrive"
sudo rm -rf /Volumes/EFI/EFI
sudo ditto "$ROOT/EFI" /Volumes/EFI/EFI

echo ">>> Conferindo o que ficou no pendrive"
grep -c "<key>" /Volumes/EFI/EFI/OC/config.plist >/dev/null
/usr/libexec/PlistBuddy -c "Print :NVRAM:Add:7C436110-AB2A-4BBB-A880-FE41995C9F82:boot-args" \
  /Volumes/EFI/EFI/OC/config.plist
echo "OK. Ejete antes de desconectar: diskutil eject /dev/${DISK:-diskX}"
