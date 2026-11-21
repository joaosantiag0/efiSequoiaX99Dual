#!/bin/bash
# Baixa o último macOS compatível com Intel: macOS Sequoia 15.8.3 (24H241).
#
# Requer: brew install mist-cli    (o Mist precisa de root)
# Uso: ./scripts/01-baixar-macos.sh [destino]     ex.: /Volumes/3Tb/macOS
#
# O "-t" aponta o diretório temporário para o destino, porque o Mist precisa de
# ~32 GB livres e /private/tmp (no disco do sistema) costuma não ter.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${1:-/Volumes/3Tb/macOS}"
VERSION="15.8.3"     # última versão Intel (Tahoe 26+ é Apple Silicon only)

command -v mist >/dev/null || { echo "Instale o Mist: brew install mist-cli"; exit 1; }
mkdir -p "$DEST/tmp"

echo ">>> Baixando macOS Sequoia $VERSION (~15.7 GB) para $DEST"
sudo mist download installer "$VERSION" application -o "$DEST" -t "$DEST/tmp" --no-ansi

echo
echo ">>> Gerando recovery BaseSystem.dmg (~850 MB, modo internet install)"
mkdir -p "$ROOT/_downloads"
python3 "$ROOT/_build/oc/Utilities/macrecovery/macrecovery.py" \
  -b Mac-7BA5B2D9E42DDD94 -m 00000000000000000 -os latest \
  -o "$ROOT/_downloads" download

# organiza no formato que o OpenCore espera no pendrive
mkdir -p "$ROOT/_downloads/com.apple.recovery.boot"
mv "$ROOT/_downloads/BaseSystem.dmg" "$ROOT/_downloads/BaseSystem.chunklist" \
   "$ROOT/_downloads/com.apple.recovery.boot/" 2>/dev/null || true

echo
echo "Pronto:"
ls -1 "$DEST"/*.app 2>/dev/null
ls -1 "$ROOT/_downloads/com.apple.recovery.boot"
