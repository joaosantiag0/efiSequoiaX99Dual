#!/usr/bin/env python3
"""
Reconstrói a config da MÁQUINA DE REFERÊNCIA (disk0s1) para o estado em que ela
estava rodando, usando o backup do usuário como base + os valores capturados
da config viva antes de ser sobrescrita.

Objetivo: reboot seguro (SIP 0x0803 como antes, pikera para a RX 6600, áudio
layout 11, ethernet built-in).
"""
import plistlib, pathlib, sys

p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/Volumes/EFI/EFI/OC/config.plist")
c = plistlib.load(open(p, "rb"))

# --- SIP: 0x0803 (era o valor da máquina; "Custom Configuration", kext signing off)
c["NVRAM"]["Add"]["7C436110-AB2A-4BBB-A880-FE41995C9F82"]["csr-active-config"] = (0x0803).to_bytes(4, "little")

# --- boot-args: mantém pikera (RX 6600) e npci
c["NVRAM"]["Add"]["7C436110-AB2A-4BBB-A880-FE41995C9F82"]["boot-args"] = \
    b"keepsyms=1 debug=0x100 npci=0x2000 agdpmod=pikera"

# --- DeviceProperties: áudio layout 11, NVMe e Ethernet built-in (wifi fica de fora)
c["DeviceProperties"]["Add"] = {
    "PciRoot(0x0)/Pci(0x1,0x1)/Pci(0x0,0x0)": {"# nvme": b"\x01\x00\x00\x00", "built-in": b"\x01\x00\x00\x00"},
    "PciRoot(0x0)/Pci(0x1B,0x0)": {"# audio": "", "layout-id": 11},
    "PciRoot(0x0)/Pci(0x1C,0x2)/Pci(0x0,0x0)": {"# ethernet": "", "built-in": b"\x01\x00\x00\x00"},
}

# --- Boot picker como estava (escondido, OpenCanopy, timeout 15)
b = c["Misc"]["Boot"]
b["ShowPicker"] = False
b["Timeout"] = 15
b["PickerMode"] = "External"
b["HideAuxiliary"] = True
b["LauncherOption"] = "Full"
b["LauncherPath"] = "Default"

# --- Security como estava
s = c["Misc"]["Security"]
s["AllowSetDefault"] = True
s["ExposeSensitiveData"] = 15
s["ScanPolicy"] = 2687747
s["SecureBootModel"] = "Disabled"
s["Vault"] = "Optional"
s["DmgLoading"] = "Signed"

# --- Quirks como estavam
k = c["Kernel"]["Quirks"]
k["AppleXcpmCfgLock"] = False
k["AppleXcpmForceBoost"] = True
k["ProvideCurrentCpuInfo"] = False
k["XhciPortLimit"] = True
c["UEFI"]["Quirks"]["IgnoreInvalidFlexRatio"] = True
c["UEFI"]["Quirks"]["ReleaseUsbOwnership"] = False
c["Booter"]["Quirks"]["ResizeAppleGpuBars"] = -1

# --- chaves novas do OpenCore 1.0.8 (inofensivas em versões antigas)
c["Booter"]["Quirks"].setdefault("ClearTaskSwitchBit", False)
c["Booter"]["Quirks"].setdefault("AllowRelocationBlock", False)
c["Kernel"]["Quirks"].setdefault("DisableIoMapperMapping", False)
c["Kernel"]["Quirks"].setdefault("CustomPciSerialDevice", False)
c["UEFI"]["Quirks"].setdefault("DisableSecurityPolicy", False)
c["UEFI"]["Quirks"].setdefault("ShimRetainProtocol", False)
c["UEFI"]["Quirks"].setdefault("ResizeUsePciRbIo", False)
c["Misc"]["Boot"].setdefault("PickerAudioAssist", False)
c["Misc"]["Boot"].setdefault("ConsoleAttributes", 0)
for d in c["UEFI"]["Drivers"]:
    d.setdefault("HideVerbose", False)

plistlib.dump(c, open(p, "wb"), sort_keys=False)
print("config da máquina de referência reconstruído:", p)
