#!/bin/bash
# Verifica a integridade do pacote EFI: estrutura, kexts, ACPI e config.plist.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EFI="$ROOT/EFI"
fail=0

chk() { if [[ -e "$1" ]]; then echo "  OK   $1"; else echo "  FALTA $1"; fail=1; fi; }

echo "== Estrutura =="
chk "$EFI/BOOT/BOOTx64.efi"
chk "$EFI/OC/OpenCore.efi"
for d in OpenRuntime HfsPlus ResetNvramEntry; do chk "$EFI/OC/Drivers/$d.efi"; done

echo "== ACPI =="
for a in SSDT-PLUG SSDT-USBX; do chk "$EFI/OC/ACPI/$a.aml"; done

echo "== Kexts (bundle + executável + Info.plist) =="
python3 - "$EFI" <<'PY'
import plistlib, sys, pathlib
efi = pathlib.Path(sys.argv[1])
cfg = plistlib.load(open(efi/"OC"/"config.plist","rb"))
bad = 0
for k in cfg["Kernel"]["Add"]:
    b = efi/"OC"/"Kexts"/k["BundlePath"]
    ok = (b/"Contents"/"Info.plist").exists() and (b/k["ExecutablePath"]).exists()
    print(f"  {'OK   ' if ok else 'FALHA'} {k['BundlePath']}")
    bad += 0 if ok else 1
for a in cfg["ACPI"]["Add"]:
    p = efi/"OC"/"ACPI"/a["Path"]
    print(f"  {'OK   ' if p.exists() else 'FALHA'} {a['Path']}")
    bad += 0 if p.exists() else 1
for d in cfg["UEFI"]["Drivers"]:
    if d["Enabled"]:
        p = efi/"OC"/"Drivers"/d["Path"]
        print(f"  {'OK   ' if p.exists() else 'FALHA'} Drivers/{d['Path']}")
        bad += 0 if p.exists() else 1
sys.exit(1 if bad else 0)
PY
[[ $? -eq 0 ]] || fail=1

echo "== ocvalidate =="
if "$ROOT/ocvalidate" "$EFI/OC/config.plist"; then :; else fail=1; fi

echo
if [[ $fail -eq 0 ]]; then echo "RESULTADO: tudo certo."; else echo "RESULTADO: há problemas acima."; fi
exit $fail
