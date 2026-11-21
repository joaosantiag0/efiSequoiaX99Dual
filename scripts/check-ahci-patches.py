#!/usr/bin/env python3
"""Procura os bytes dos patches de AppleAHCIPort dentro das Kernel Collections."""
import pathlib, sys

PATTERNS = {
    "ALPM 40600200": bytes.fromhex("40600200"),
    "hotplug f6836d010000447446": bytes.fromhex("f6836d010000447446"),
    "comreset a80174338bb388000000": bytes.fromhex("a80174338bb388000000"),
}

files = sorted(pathlib.Path("/System/Library/KernelCollections").glob("*.kc"))
if not files:
    sys.exit("nenhuma .kc encontrada")

for f in files:
    data = f.read_bytes()
    print(f"\n{f.name}  ({len(data)/1e6:.0f} MB)")
    for name, pat in PATTERNS.items():
        n = data.count(pat)
        print(f"  {'OK  ' if n else 'NAO '} {name}: {n} ocorrencia(s)")
