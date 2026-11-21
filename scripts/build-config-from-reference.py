#!/usr/bin/env python3
"""
Reconstrói o EFI do PC novo a partir do EFI QUE JÁ FUNCIONA nesta máquina
(X99 + Xeon E5-2673 v3, macOS 15.3.1), removendo o stack de Wi-Fi e ajustando
o necessário para o instalador.

Motivo: o config gerado "do zero" usava o combo moderno de Booter quirks
(RebuildAppleMemoryMap + SyncRuntimePermissions) e não tinha o CPUID spoof de
Haswell que esta plataforma precisa. Resultado: panic em ~2 s.

Uso:  python3 scripts/build-config-from-reference.py [--src /Volumes/EFI] [--gpu nvidia|amd]
"""
import plistlib, shutil, sys, pathlib, argparse

ROOT = pathlib.Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("--src", default="/Volumes/EFI", help="EFI de referência montada")
ap.add_argument("--gpu", default="nvidia", choices=["nvidia", "amd"])
args = ap.parse_args()

SRC = pathlib.Path(args.src) / "EFI"
DST = ROOT / "EFI"
if not (SRC / "OC" / "config.plist").exists():
    sys.exit(f"ERRO: {SRC}/OC/config.plist não encontrado (monte a EFI de referência)")

# ---------------------------------------------------------------- 1. arquivos
WIFI_KEXTS = {"IOSkywalkFamily.kext", "IO80211FamilyLegacy.kext"}

shutil.rmtree(DST / "OC" / "ACPI", ignore_errors=True)
shutil.rmtree(DST / "OC" / "Kexts", ignore_errors=True)
shutil.rmtree(DST / "OC" / "Drivers", ignore_errors=True)
shutil.rmtree(DST / "OC" / "Resources", ignore_errors=True)
shutil.rmtree(DST / "OC" / "Tools", ignore_errors=True)

for sub in ("ACPI", "Kexts", "Drivers", "Resources", "Tools"):
    shutil.copytree(SRC / "OC" / sub, DST / "OC" / sub)

for k in WIFI_KEXTS:
    shutil.rmtree(DST / "OC" / "Kexts" / k, ignore_errors=True)

# limpa lixo do macOS
for p in list(DST.rglob("._*")) + list(DST.rglob(".DS_Store")) + list(DST.rglob(".contentFlavour")) + list(DST.rglob(".contentVisibility")):
    p.unlink(missing_ok=True)

# ---------------------------------------------------------------- 2. config
cfg = plistlib.load(open(SRC / "OC" / "config.plist", "rb"))

# 2a. kexts: fora o que é de Wi-Fi
cfg["Kernel"]["Add"] = [
    k for k in cfg["Kernel"]["Add"]
    if not any(w in k["BundlePath"] for w in ("IOSkywalk", "IO80211FamilyLegacy", "AirPortBrcmNIC"))
]
cfg["Kernel"]["Block"] = [
    b for b in cfg["Kernel"]["Block"] if "IOSkywalk" not in b["Identifier"]
]

# 2b. DeviceProperties: sem a entrada de Wi-Fi
dp = cfg["DeviceProperties"]["Add"]
for key in list(dp):
    if "# wifi" in dp[key]:
        del dp[key]

# 2c. boot-args: tira agdpmod=pikera (AMD-only), mantém npci=0x2000 e -v
BOOT_ARGS = {
    # instalador/fase 1: sem driver de GPU, SIP do EFI de referência
    "nvidia": "keepsyms=1 debug=0x100 -v npci=0x2000 alcid=11",
    "amd": "keepsyms=1 debug=0x100 -v npci=0x2000 alcid=11 agdpmod=pikera",
}[args.gpu]
nv = cfg["NVRAM"]["Add"]["7C436110-AB2A-4BBB-A880-FE41995C9F82"]
nv["boot-args"] = BOOT_ARGS.encode()

# 2d. picker visível (a referência usa ShowPicker=false porque já está instalada)
cfg["Misc"]["Boot"]["ShowPicker"] = True
cfg["Misc"]["Boot"]["Timeout"] = 10
cfg["Misc"]["Boot"]["HideAuxiliary"] = False      # mostra Recovery/Reset NVRAM
cfg["Misc"]["Boot"]["PickerMode"] = "Builtin"     # texto: não depende de ícones
for d in cfg["UEFI"]["Drivers"]:
    if d["Path"] == "OpenCanopy.efi":
        d["Enabled"] = False
cfg["Misc"]["Security"]["ScanPolicy"] = 0        # varre tudo (USB do instalador)

# 2e. SMBIOS próprio (iMacPro1,1, igual à referência)
g = cfg["PlatformInfo"]["Generic"]
g["SystemProductName"] = "iMacPro1,1"
g["SystemSerialNumber"] = "C02XXXXXXXXXX"
g["MLB"] = "XXXXXXXXXXXXXXXXX"
g["ROM"] = bytes.fromhex("000000000000")
g["SystemUUID"] = "00000000-0000-0000-0000-000000000000"

# 2f. CFG Lock: a referência usa false porque aquela placa tem MSR 0xE2 liberado.
# Como a placa nova pode ter o MSR travado, deixa o patch ligado (inofensivo se
# já estiver liberado).
cfg["Kernel"]["Quirks"]["AppleXcpmCfgLock"] = True

# 2g. sem travas de segurança que quebram o picker
cfg["Misc"]["Security"]["SecureBootModel"] = "Disabled"
cfg["Misc"]["Security"]["Vault"] = "Optional"

out = DST / "OC" / "config.plist"
plistlib.dump(cfg, open(out, "wb"), sort_keys=False)

print("config gerado de:", SRC / "OC" / "config.plist")
print("  boot-args:", BOOT_ARGS)
print("  CSR:", cfg["NVRAM"]["Add"]["7C436110-AB2A-4BBB-A880-FE41995C9F82"]["csr-active-config"].hex())
print("  CPUID spoof:", cfg["Kernel"]["Emulate"]["Cpuid1Data"][:4].hex())
print("  ACPI:", [a["Path"] for a in cfg["ACPI"]["Add"]])
print("  Kexts:", [k["BundlePath"] for k in cfg["Kernel"]["Add"]])
