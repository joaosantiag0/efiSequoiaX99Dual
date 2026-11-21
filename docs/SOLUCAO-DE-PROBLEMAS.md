# Solução de problemas

Legenda: para ver mensagens detalhadas, os `boot-args` já incluem `-v keepsyms=1 debug=0x100`.

## Panic em ~2 s: "panic occurred prior to initialization" / thread Unknown

Sintoma: tela de panic preta, `System uptime in nanoseconds: ~2170000000`,
`Mac OS version: Not yet set` e um frame pointer com ASCII estranho
(ex.: `0x62007600650072` = "bver" em UTF-16). É corrupção de pilha no início do
kernel, não erro de kext de terceiros.

Causa confirmada nesta plataforma (X99 Haswell-EP): **combo de Booter quirks
errado + CPUID spoof ausente**. A máquina de referência (mesmo hardware, macOS
15.3.1) roda com o combo **antigo**:

| Quirk | Valor correto aqui |
|---|---|
| `EnableWriteUnprotector` | **true** |
| `RebuildAppleMemoryMap` | **false** |
| `SyncRuntimePermissions` | **false** |
| `FixupAppleEfiImages` | **false** |
| `Kernel > Emulate > Cpuid1Data` | `C3060300...` (Haswell, 0x306C3) |

O combo moderno (`RebuildAppleMemoryMap=true` + `SyncRuntimePermissions=true` +
`EnableWriteUnprotector=false`) **pane** nesse firmware.

Solução aplicada: `EFI/OC/config.plist` agora é gerado a partir do EFI que
funciona nesta máquina, com:

```bash
sudo diskutil mount disk0s1      # EFI da máquina de referência
python3 scripts/build-config-from-reference.py --gpu nvidia
python3 scripts/upgrade-keys-1.0.8.py EFI/OC/config.plist
```

Além dos quirks, vieram do EFI de referência: os **9 SSDTs** (incluindo
`SSDT-PLUG` com o caminho correto `\_SB.SCK0.CP00`, `SSDT-UNC`, `SSDT-HPET`,
`SSDT-RTC0`, `SSDT-GPRW`), as 8 renomeações de ACPI, `npci=0x2000` nos boot-args
e `layout-id 11` no DeviceProperties para o áudio.

## A máquina reinicia/pane antes do instalador

| Sintoma | Causa provável | Correção |
|---|---|---|
| Kernel panic em `AppleIntelCPUPowerManagement` / trava em `AppleACPICPU` | MSR 0xE2 travado ou SSDT-PLUG com caminho errado | `AppleXcpmCfgLock=true` (já ativo). Troque `SSDT-PLUG.aml` por `SSDT-PLUG-ALT.aml` (compilado de `docs/acpi/SSDT-PLUG-ALT.dsl`) |
| Panic imediato com vários núcleos | falta de sincronia de TSC | `CpuTscSync.kext` já incluso — confirme que está habilitado e depois do `Lilu` |
| Trava em `[ PCI Configuration Begin ]` | Above 4G / BAR | BIOS: Above 4G `Enabled`, Resizable BAR `Disabled`; se persistir adicione `npci=0x2000` aos boot-args |
| Reinicia em loop sem mensagem | BIOS em Legacy/CSM | CSM `Disabled`, boot UEFI only, Secure Boot `Disabled` |
| Para 1 min em `PCI configuration end` (NVIDIA) | BAR1 subindo | normal no 1º boot com o driver; se persistir, `nvrmsettle=10000` |

## Não passa do logo da Apple / tela preta

- **AMD (RX 6600) com tela preta depois do boot**: confirme `agdpmod=pikera` nos boot-args
  (no modo NVIDIA esse argumento deve estar **fora** — ele conflita com o driver RTX).
- **NVIDIA RTX sem aceleração / tela preta**: o driver ainda não foi instalado ou não carregou.
  Veja [NVIDIA-RTX.md](NVIDIA-RTX.md) seção 7. Antes do driver, o sistema roda no framebuffer
  da firmware — funciona, mas sem Metal.
- **HDMI sem sinal, DisplayPort ok** (ou vice-versa): troque a saída; em algumas placas X99 o
  GOP da BIOS só inicializa a saída principal. Alternativa: `UEFI > Output > DirectGopRendering=true`.
- **Progresso para em 50%**: normalmente é USB. Use porta USB 2.0 traseira e, se possível,
  um pendrive 2.0.

## `Still waiting for root device`

O macOS não achou o disco/instalador. Causas: USB 3.0 sem mapa (use USB 2.0), controlador
SATA em RAID (`AHCI` na BIOS), ou NVMe em slot atrás de PLX. Ative `AHCI`, desligue RAID.

## Instalador não enxerga o disco

- No Disk Utility, use `Ver > Mostrar todos os dispositivos` e apague o **disco** (não o volume)
  como APFS/GUID.
- Se o disco já tem Windows: mantenha a partição EFI existente e crie o APFS no espaço livre.
- NVMe não aparece: BIOS em `UEFI only` e disco em GPT (não MBR).

## Áudio mudo

1. Teste layouts: `alcid=1` → `alcid=11` → `alcid=2` (ver docs/POS-INSTALACAO.md).
2. Confirme que `AppleALC.kext` está habilitado e depois do `Lilu`.
3. Em algumas X99, HPET/IRQ conflitam: gere `SSDT-HPET.aml` com o **SSDTTime** na máquina alvo.
4. Saída padrão precisa ser “Alto-falantes internos”.

## USB 3.0 lento ou portas mortas

Falta mapa USB. Siga docs/POS-INSTALACAO.md seção 3. Enquanto isso, use USB 2.0.

## Rede não sobe

```bash
# qual driver foi carregado?
kextstat | grep -Ei "RTL8111|IntelMausi|AppleIGB"
```

| Chip | Kext |
|---|---|
| Realtek RTL8111/8168 | `RealtekRTL8111.kext` (incluso) |
| Intel I218/I219 | `IntelMausi.kext` (incluso) |
| Intel I210/I211 | **não incluso** → instale `AppleIGB.kext` |
| Killer/Aquantia | instale o driver específico |

Se o link sobe mas não pega IP: `sudo ifconfig en0 down && sudo ifconfig en0 up`, ou renomeie
o serviço em Ajustes > Rede. Wi-Fi não existe neste build — não procure placa sem fio.

## Boot loop depois de uma atualização

1. Boote pelo pendrive (o EFI dele está intacto).
2. Monte a EFI do disco e restaure o backup: `sudo rm -rf /Volumes/EFI/EFI && sudo cp -R ~/efi-backup /Volumes/EFI/EFI`.
3. Atualize OpenCore + kexts (`Lilu`/`WhateverGreen` primeiro) e valide com `ocvalidate`.

## Como coletar log para pedir ajuda

```bash
# na máquina quebrada, pelo Recovery ou pendrive:
# ative Misc > Debug > Target = 67 no config e reinicie
# o log sai em /Volumes/EFI/opencore-YYYY-MM-DD-HH-MMSS.txt
```

Sempre informe: CPU, placa-mãe, GPU, versão do macOS, trecho do log e o que mudou desde o último boot bom.
