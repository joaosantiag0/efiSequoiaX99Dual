#!/usr/bin/env python3
"""
Gera o config.plist do Hackintosh (X99 + Xeon E5 v3/v4 + Radeon RX 6600, sem Wi-Fi)
a partir do Sample.plist do OpenCore 1.0.8, garantindo que todas as chaves da
versão existam. Rodar:  python3 scripts/build-config.py
"""
import plistlib, pathlib, shutil, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "_build" / "Sample.plist"
GPU_MODE = (sys.argv[1] if len(sys.argv) > 1 else "nvidia").lower()
if GPU_MODE not in ("nvidia", "amd"):
    print("Uso: python3 scripts/build-config.py [nvidia|amd]"); raise SystemExit(1)
OUT = ROOT / "EFI" / "OC" / "config.plist" if GPU_MODE == "nvidia" else ROOT / "variants" / "config-amd.plist"

SERIAL = "C02XXXXXXXXXX"
MLB = "XXXXXXXXXXXXXXXXX"
ROM = bytes.fromhex("000000000000")          # MAC da en0 (troque pelo MAC da placa alvo)
UUID = "00000000-0000-0000-0000-000000000000"

# AMD (RX 6600): agdpmod=pikera evita tela preta.
# NVIDIA RTX: driver NullMoth (v3.x) exige nvfb/nvaccel + AMFI liberado; e
# agdpmod=pikera tem de sair (o README do driver manda remover).
BOOT_ARGS = {
    "amd": "-v keepsyms=1 debug=0x100 alcid=1 agdpmod=pikera",
    "nvidia": ("-v keepsyms=1 debug=0x100 alcid=1 gfxrst=4 "
               "nvfb=1 nvaccel=1 nvfbheads=4 -nvkmsnosmooth "
               "amfi_get_out_of_my_way=0x1 amfi=0x80 ipc_control_port_options=0"),
}[GPU_MODE]

# 0x0A43 libera kexts não assinados (exigido pelo driver NVIDIA); SIP íntegro no AMD.
CSR = 0x0A43 if GPU_MODE == "nvidia" else 0x00000000

def setk(d, path, value):
    cur = d
    keys = path.split(".")
    for k in keys[:-1]:
        if k not in cur:
            cur[k] = {}
        cur = cur[k]
    if keys[-1] not in cur:
        print(f"  ! criando chave inexistente: {path}")
    cur[keys[-1]] = value

def kext(bundle, comment="", exe=None, min_kernel="", max_kernel=""):
    return {
        "Arch": "Any",
        "BundlePath": bundle,
        "Comment": comment,
        "Enabled": True,
        "ExecutablePath": exe or f"Contents/MacOS/{bundle.replace('.kext','')}",
        "MaxKernel": max_kernel,
        "MinKernel": min_kernel,
        "PlistPath": "Contents/Info.plist",
    }

with open(SAMPLE, "rb") as f:
    c = plistlib.load(f)

# ---------------------------------------------------------------- ACPI
setk(c, "ACPI.Add", [
    {"Comment": "CPU power management plugin-type", "Enabled": True, "Path": "SSDT-PLUG.aml"},
    {"Comment": "USB power properties",        "Enabled": True, "Path": "SSDT-USBX.aml"},
])
setk(c, "ACPI.Delete", [])
setk(c, "ACPI.Patch", [])
setk(c, "ACPI.Quirks.FadtEnableReset", False)
setk(c, "ACPI.Quirks.NormalizeHeaders", False)
setk(c, "ACPI.Quirks.RebaseRegions", False)
setk(c, "ACPI.Quirks.ResetHwSig", False)
setk(c, "ACPI.Quirks.ResetLogoStatus", True)
setk(c, "ACPI.Quirks.SyncTableIds", False)

# ---------------------------------------------------------------- Booter
setk(c, "Booter.MmioWhitelist", [])
setk(c, "Booter.Patch", [])
for k, v in {
    "AvoidRuntimeDefrag": True,
    "FixupAppleEfiImages": True,
    "DevirtualiseMmio": False,
    "DisableSingleUser": False,
    "DisableVariableWrite": False,
    "DiscardHibernateMap": False,
    "EnableSafeModeSlide": True,
    "EnableWriteUnprotector": False,
    "ForceBooterSignature": False,
    "ProtectMemoryRegions": False,
    "ProtectSecureBoot": False,
    "ProtectUefiServices": False,
    "ProvideCustomSlide": True,
    "ProvideMaxSlide": 0,
    "RebuildAppleMemoryMap": True,
    "ResizeAppleGpuBars": 0 if GPU_MODE == "nvidia" else -1,
    "SetupVirtualMap": True,
    "SignalAppleOS": False,
    "SyncRuntimePermissions": True,
}.items():
    setk(c, f"Booter.Quirks.{k}", v)

# ---------------------------------------------------------------- DeviceProperties
# Nenhuma propriedade é obrigatória: a RX 6600 funciona via WhateverGreen + agdpmod=pikera.
# Se quiser fixar o layout de áudio por PCI em vez de alcid=, descomente:
# setk(c, "DeviceProperties.Add", {"PciRoot(0x0)/Pci(0x1B,0x0)": {"layout-id": bytes([11, 0, 0, 0])}})
setk(c, "DeviceProperties.Add", {})
setk(c, "DeviceProperties.Delete", {})

# ---------------------------------------------------------------- Kernel
KEXTS = [
    kext("Lilu.kext", "Patch engine (load first)"),
]
if GPU_MODE == "nvidia":
    KEXTS.append(kext("AMFIPass.kext", "AMFI bypass for unsigned GPU driver"))
KEXTS += [
    kext("VirtualSMC.kext", "SMC emulator"),
    kext("SMCProcessor.kext", "CPU temperature and power", "Contents/MacOS/SMCProcessor"),
    kext("SMCSuperIO.kext", "Motherboard sensors", "Contents/MacOS/SMCSuperIO"),
    kext("WhateverGreen.kext", "AMD GPU framebuffer patches"),
    kext("AppleALC.kext", "ALC audio (layout via alcid)"),
    kext("RealtekRTL8111.kext", "Realtek 8111/8168 Ethernet"),
    kext("IntelMausi.kext", "Intel I218/I219 Ethernet"),
    kext("NVMeFix.kext", "NVMe fixes", min_kernel="19.0.0"),
    kext("RestrictEvents.kext", "Suppress hardware/CPU warnings"),
    kext("CpuTscSync.kext", "TSC sync across cores (Xeon)"),
]
setk(c, "Kernel.Add", KEXTS)
setk(c, "Kernel.Block", [])
setk(c, "Kernel.Force", [])
setk(c, "Kernel.Patch", [])
setk(c, "Kernel.Emulate", {"Cpuid1Data": b"", "Cpuid1Mask": b"", "DummyPowerManagement": False,
                           "MaxKernel": "", "MinKernel": ""})
setk(c, "Kernel.Quirks.AppleCpuPmCfgLock", False)
setk(c, "Kernel.Quirks.AppleXcpmCfgLock", True)
setk(c, "Kernel.Quirks.AppleXcpmExtraMsrs", True)      # obrigatório em Haswell-EP/Broadwell-EP
setk(c, "Kernel.Quirks.AppleXcpmForceBoost", False)
setk(c, "Kernel.Quirks.CustomSMBIOSGuid", False)
setk(c, "Kernel.Quirks.DisableIoMapper", True)         # VT-d ligado na BIOS -> true
setk(c, "Kernel.Quirks.DisableLinkeditJettison", True)
setk(c, "Kernel.Quirks.DisableRtcChecksum", False)
setk(c, "Kernel.Quirks.ExtendBTFeatureFlags", False)
setk(c, "Kernel.Quirks.ExternalDiskIcons", False)
setk(c, "Kernel.Quirks.ForceAquantiaEthernet", False)
setk(c, "Kernel.Quirks.ForceSecureBootScheme", False)
setk(c, "Kernel.Quirks.IncreasePciBarSize", False)
setk(c, "Kernel.Quirks.LapicKernelPanic", False)
setk(c, "Kernel.Quirks.LegacyCommpage", False)
setk(c, "Kernel.Quirks.PanicNoKextDump", True)
setk(c, "Kernel.Quirks.PowerTimeoutKernelPanic", True)
setk(c, "Kernel.Quirks.ProvideCurrentCpuInfo", True)   # contagem de núcleos correta em Xeon
setk(c, "Kernel.Quirks.SetApfsTrimTimeout", -1)
setk(c, "Kernel.Quirks.ThirdPartyDrives", False)
setk(c, "Kernel.Quirks.XhciPortLimit", False)          # não funciona no Sequoia: use mapa USB

# ---------------------------------------------------------------- Misc
setk(c, "Misc.Boot.HideAuxiliary", False)
setk(c, "Misc.Boot.HibernateSkipsPicker", False)
setk(c, "Misc.Boot.LauncherOption", "Full")
setk(c, "Misc.Boot.PickerAttributes", 17)
setk(c, "Misc.Boot.PickerMode", "Builtin")
setk(c, "Misc.Boot.PickerVariant", "Auto")
setk(c, "Misc.Boot.PollAppleHotKeys", True)
setk(c, "Misc.Boot.ShowPicker", True)
setk(c, "Misc.Boot.TakeoffDelay", 0)
setk(c, "Misc.Boot.Timeout", 8)
setk(c, "Misc.Debug.AppleDebug", False)
setk(c, "Misc.Debug.ApplePanic", False)
setk(c, "Misc.Debug.DisableWatchDog", True)
setk(c, "Misc.Debug.DisplayDelay", 0)
setk(c, "Misc.Debug.DisplayLevel", 0x80000000)
setk(c, "Misc.Debug.Target", 3)
setk(c, "Misc.Security.AllowSetDefault", False)
setk(c, "Misc.Security.ApECID", 0)
setk(c, "Misc.Security.AuthRestart", False)
setk(c, "Misc.Security.BlacklistAppleUpdate", True)
setk(c, "Misc.Security.DmgLoading", "Signed")
setk(c, "Misc.Security.EnablePassword", False)
setk(c, "Misc.Security.ExposeSensitiveData", 6)
setk(c, "Misc.Security.HaltLevel", 0x80000000)
setk(c, "Misc.Security.ScanPolicy", 0)
setk(c, "Misc.Security.SecureBootModel", "Disabled")
setk(c, "Misc.Security.Vault", "Optional")
setk(c, "Misc.Serial.Init", False)
setk(c, "Misc.Serial.Override", False)
setk(c, "Misc.Tools", [])

# ---------------------------------------------------------------- NVRAM
setk(c, "NVRAM.Add.7C436110-AB2A-4BBB-A880-FE41995C9F82", {
    "boot-args": BOOT_ARGS.encode(),
    "csr-active-config": CSR.to_bytes(4, "little"),
    "prev-lang:kbd": b"pt-BR:13",
    "run-efi-updater": b"No",
})
setk(c, "NVRAM.Add.4D1EDE05-38C7-4A6A-9CC6-4BCCA8B38C14", {
    "DefaultBackgroundColor": bytes([0, 0, 0, 0]),
})
setk(c, "NVRAM.Delete.7C436110-AB2A-4BBB-A880-FE41995C9F82", ["boot-args", "csr-active-config"])
setk(c, "NVRAM.LegacyOverwrite", False)
setk(c, "NVRAM.WriteFlash", True)

# ---------------------------------------------------------------- PlatformInfo
setk(c, "PlatformInfo.Automatic", True)
setk(c, "PlatformInfo.UpdateDataHub", True)
setk(c, "PlatformInfo.UpdateNVRAM", True)
setk(c, "PlatformInfo.UpdateSMBIOS", True)
setk(c, "PlatformInfo.UpdateSMBIOSMode", "Create")
setk(c, "PlatformInfo.UseRawUuidEncoding", False)
setk(c, "PlatformInfo.Generic.AdviseFeatures", False)
setk(c, "PlatformInfo.Generic.MLB", MLB)
setk(c, "PlatformInfo.Generic.ROM", ROM)
setk(c, "PlatformInfo.Generic.SystemProductName", "iMacPro1,1")
setk(c, "PlatformInfo.Generic.SystemSerialNumber", SERIAL)
setk(c, "PlatformInfo.Generic.SystemUUID", UUID)
setk(c, "PlatformInfo.Generic.SystemMemoryStatus", "Auto")

# ---------------------------------------------------------------- UEFI
setk(c, "UEFI.APFS.MinDate", -1)
setk(c, "UEFI.APFS.MinVersion", 0)
setk(c, "UEFI.Audio.AudioSupport", False)
setk(c, "UEFI.ConnectDrivers", True)
setk(c, "UEFI.Drivers", [
    {"Arguments": "", "Comment": "OpenCore runtime services", "Enabled": True, "HideVerbose": False, "LoadEarly": False, "Path": "OpenRuntime.efi"},
    {"Arguments": "", "Comment": "HFS+ reading (installer)", "Enabled": True, "HideVerbose": False, "LoadEarly": False, "Path": "HfsPlus.efi"},
    {"Arguments": "", "Comment": "Reset NVRAM entry", "Enabled": True, "HideVerbose": False, "LoadEarly": False, "Path": "ResetNvramEntry.efi"},
])
setk(c, "UEFI.Input.KeyForgetThreshold", 5)
setk(c, "UEFI.Input.KeySupport", True)
setk(c, "UEFI.Input.KeySupportMode", "Auto")
setk(c, "UEFI.Input.KeySwap", False)
setk(c, "UEFI.Input.PointerSupport", False)
setk(c, "UEFI.Input.TimerResolution", 50000)
setk(c, "UEFI.Output.ClearScreenOnModeSwitch", False)
setk(c, "UEFI.Output.DirectGopRendering", False)
setk(c, "UEFI.Output.ForceResolution", False)
setk(c, "UEFI.Output.GopPassThrough", "Disabled")
setk(c, "UEFI.Output.IgnoreTextInGraphics", False)
setk(c, "UEFI.Output.ProvideConsoleGop", True)
setk(c, "UEFI.Output.ReconnectOnResChange", False)
setk(c, "UEFI.Output.Resolution", "Max")
setk(c, "UEFI.Output.SanitiseClearScreen", False)
setk(c, "UEFI.Output.TextRenderer", "BuiltinGraphics")
setk(c, "UEFI.Output.UIScale", 0)
for k, v in {
    "ActivateHpetSupport": False,
    "DisableSecurityPolicy": False,
    "EnableVectorAcceleration": True,
    "EnableVmx": False,
    "ExitBootServicesDelay": 0,
    "ForceOcWriteFlash": False,
    "ForgeUefiSupport": False,
    "IgnoreInvalidFlexRatio": False,
    "ReleaseUsbOwnership": True,
    "ReloadOptionRoms": False,
    "RequestBootVarRouting": True,
    "ResizeGpuBars": -1,
    "TscSyncTimeout": 0,
    "UnblockFsConnect": False,
}.items():
    setk(c, f"UEFI.Quirks.{k}", v)
setk(c, "UEFI.ReservedMemory", [])

with open(OUT, "wb") as f:
    plistlib.dump(c, f, sort_keys=False)

x = plistlib.load(open(OUT, "rb"))
print(f"config gerado ({GPU_MODE}):", OUT)
print("  Kexts:", len(x["Kernel"]["Add"]), "| ACPI:", [a["Path"] for a in x["ACPI"]["Add"]])
print("  SMBIOS:", x["PlatformInfo"]["Generic"]["SystemProductName"], x["PlatformInfo"]["Generic"]["SystemSerialNumber"])
print("  boot-args:", x["NVRAM"]["Add"]["7C436110-AB2A-4BBB-A880-FE41995C9F82"]["boot-args"].decode())
