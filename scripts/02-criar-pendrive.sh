#!/bin/bash
# Cria o pendrive de instalação do macOS a partir do Install Assistant (.app)
# gerado pelo Mist, e copia o EFI do OpenCore.
#
# Uso:  ./scripts/02-criar-pendrive.sh "/Volumes/3Tb/macOS/Install macOS Sequoia.app" disk6
#       (disk6 = o pendrive; confira com: diskutil list)
#
# ATENÇÃO: o volume do pendrive é APAGADO.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="${1:-}"
DISK="${2:-}"

if [[ -z "$APP" || -z "$DISK" ]]; then
  echo "Uso: $0 \"/caminho/Install macOS Sequoia.app\" diskN"
  exit 1
fi
[[ -d "$APP" ]] || { echo "ERRO: app não encontrado: $APP"; exit 1; }
[[ -b "/dev/$DISK" ]] || { echo "ERRO: disco inválido: /dev/$DISK"; exit 1; }

echo ">>> Discos presentes:"
diskutil list
echo
diskutil info "/dev/$DISK" | grep -E "Device / Media Name|Disk Size|Removable"
echo
read -r -p "Confirma APAGAR /dev/$DISK? Digite APAGAR: " ok
[[ "$ok" == "APAGAR" ]] || { echo "Cancelado."; exit 1; }

VOLNAME="OPENCORE"
echo ">>> Formatando /dev/$DISK como HFS+ / GPT"
sudo diskutil eraseDisk JHFS+ "$VOLNAME" GPT "/dev/$DISK"

echo ">>> Criando mídia de instalação (10-30 min)"
sudo "$APP/Contents/Resources/createinstallmedia" --volume "/Volumes/$VOLNAME" --nointeraction

INSTALL_VOL="$(ls -d "/Volumes/Install macOS"* 2>/dev/null | head -1)"
echo ">>> Instalador montado em: $INSTALL_VOL"

echo ">>> Montando a partição EFI"
EFI_DEV="$(diskutil list "/dev/$DISK" | awk '/EFI/ {print $NF; exit}')"
sudo diskutil mount "/dev/$EFI_DEV"
EFI_MNT="/Volumes/EFI"
[[ -d "$EFI_MNT" ]] || { echo "ERRO: EFI não montou em $EFI_MNT"; exit 1; }

echo ">>> Copiando EFI do OpenCore"
sudo rm -rf "$EFI_MNT/EFI"
sudo ditto "$ROOT/EFI" "$EFI_MNT/EFI"

echo ">>> Validando config.plist"
"$ROOT/ocvalidate" "$EFI_MNT/EFI/OC/config.plist"

echo
echo "PRONTO. Pendrive inicializável criado."
echo "  EFI:        $EFI_MNT/EFI"
echo "  Instalador: $INSTALL_VOL"
diskutil eject "/dev/$DISK" || true
