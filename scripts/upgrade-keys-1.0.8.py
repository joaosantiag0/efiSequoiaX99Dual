#!/usr/bin/env python3
"""Adiciona as chaves novas do OpenCore 1.0.8 que faltam num config antigo."""
import plistlib, pathlib, sys

p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "EFI/OC/config.plist")
c = plistlib.load(open(p, "rb"))

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
print("chaves 1.0.8 adicionadas em", p)
