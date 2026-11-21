#!/bin/bash
# Gera um novo Serial / MLB / UUID válidos para iMacPro1,1.
# Sempre que trocar o serial, atualize também o ROM (MAC da placa) no config.
#
# Uso: ./scripts/04-gerar-serial.sh [modelo]   (padrão: iMacPro1,1)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MODEL="${1:-iMacPro1,1}"

echo ">>> 3 candidatos para $MODEL (Serial | MLB):"
"$ROOT/macserial" -m "$MODEL" -g -n 3

echo
echo ">>> MAC da en0 desta máquina (use como ROM na placa alvo):"
ifconfig en0 2>/dev/null | awk '/ether/ {print $2}' || echo "en0 não encontrada"
echo
echo "Depois de escolher, edite SERIAL / MLB / ROM / UUID em scripts/build-config.py"
echo "e rode: python3 scripts/build-config.py && ./ocvalidate EFI/OC/config.plist"
