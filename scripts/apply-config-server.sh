#!/bin/bash
# aplica a config nova (boot-args do driver RTX + csr 0x0A43) na EFI do servidor
set -e
ESP=/Volumes/EFI
OC="$ESP/EFI/OC"
if [ ! -f "$OC/config.plist" ]; then
  echo "ERRO: $OC/config.plist nao encontrado"
  exit 1
fi
STAMP=$(date +%Y%m%d-%H%M%S)
cp "$OC/config.plist" "$OC/config.plist.bak-$STAMP"
cp /tmp/config-new.plist "$OC/config.plist"
chmod 644 "$OC/config.plist"
sync
echo "backup: config.plist.bak-$STAMP"
ls -l "$OC"/config.plist*
echo "--- boot-args gravados ---"
/usr/libexec/PlistBuddy -c "Print :NVRAM:Add:7C436110-AB2A-4BBB-A880-FE41995C9F82:boot-args" "$OC/config.plist" 2>/dev/null || echo "(PlistBuddy nao leu)"
