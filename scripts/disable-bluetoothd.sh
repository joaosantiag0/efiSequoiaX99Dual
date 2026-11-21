#!/bin/bash
# Silencia o bluetoothd em placas SEM Bluetooth (evita a enxurrada de
# "AppleKeyStore: unexpected session uid:-1 requested by bluetoothd" no log).
#
# Sintoma: o console de boot fica rolando essas linhas sem parar.
# Não é panic nem problema de driver: é o bluetoothd tentando abrir sessão de
# keybag que não existe, porque não há controladora Bluetooth na máquina.
#
# Uso: sudo ./scripts/disable-bluetoothd.sh
set -euo pipefail

[[ "$(id -u)" -eq 0 ]] || { echo "rode com sudo"; exit 1; }

echo ">>> desativando com.apple.bluetoothd (persiste entre boots)"
launchctl disable system/com.apple.bluetoothd

echo ">>> parando a instância atual"
launchctl bootout system/com.apple.bluetoothd 2>/dev/null || true

echo ">>> estado:"
launchctl print-disabled system | grep -i bluetooth || echo "  (sem entrada — verifique manualmente)"

if pgrep -x bluetoothd >/dev/null; then
  echo "AVISO: bluetoothd ainda está rodando (reinicie para aplicar)"
else
  echo "OK: bluetoothd parado."
fi

echo
echo "Para reverter:"
echo "  sudo launchctl enable system/com.apple.bluetoothd"
