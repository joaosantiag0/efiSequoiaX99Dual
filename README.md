# Hackintosh X99 — Xeon E5 v3/v4 + NVIDIA RTX, sem Wi-Fi

EFI OpenCore **1.0.8** pronta para instalar o **último macOS realmente utilizável nesse hardware: macOS Sequoia 15.8.3 (24H241)** em um PC X99 *parecido* com a máquina de referência (Xeon E5-2673 v3), **sem placa Wi-Fi** e com **GPU NVIDIA RTX**.

> **Sobre a GPU:** RTX não tem driver da Apple. Este pacote já vem preparado para o
> driver independente **NullMoth 3.x** (GTX 16 / RTX 20-50, Metal 3) — instruções
> completas em [docs/NVIDIA-RTX.md](docs/NVIDIA-RTX.md). Se preferir estabilidade,
> é só colocar uma AMD (RX 580 / RX 6600) e usar `variants/config-amd.plist`.
>
> **Sobre a versão:** macOS Tahoe 26 roda em alguns Intel (MacPro7,1, iMac20,x),
> mas **não** no SMBIOS `iMacPro1,1` que este hardware usa. Sequoia 15.8.3 é a
> última versão instalável sem gambiarra de SMBIOS.

---

## 1. Hardware de referência (o que este EFI assume)

| Componente | Referência | Observação |
|---|---|---|
| CPU | Intel Xeon E5-26xx **v3** (Haswell-EP) ou **v4** (Broadwell-EP) | 12–22 núcleos funcionam; sem iGPU |
| Placa-mãe | X99 / C612 (Asus, Gigabyte, ASRock, Huananzhi, Kllisre, Machinist…) | chipset X99 |
| GPU | **NVIDIA RTX (20/30/40/50) ou GTX 16** | sem driver da Apple: usa o driver NullMoth 3.x — ver [docs/NVIDIA-RTX.md](docs/NVIDIA-RTX.md) |
| GPU (alternativa estável) | AMD RX 580 / RX 6600 | suporte nativo, `variants/config-amd.plist` |
| Memória | DDR4 ECC/REG ou UDIMM | 16 GB+ |
| Rede | **Ethernet** Realtek RTL8111/8168 **ou** Intel I218/I219 | é a única rede — não há Wi-Fi |
| Áudio | Realtek ALC1150 / ALC892 / ALC887 | `AppleALC` + `alcid=` |
| Disco | NVMe ou SATA AHCI | `NVMeFix` incluso |
| SMBIOS | `iMacPro1,1` | Xeon + GPU dedicada, suporta Sequoia nativamente |

**Nenhuma kext de Wi-Fi neste pacote** — de propósito: a placa é cabeada, então o
pacote vai só com Ethernet (Realtek RTL8111 + Intel I218/I219). Wi-Fi Intel/Realtek
exigiria `itlwm`/`AirportItlwm` com limitações e sem AirDrop.

**Sobre NVIDIA:** o pacote **não** injeta kexts de GPU no EFI — o driver NullMoth
instala em `/Library/Extensions` do sistema já instalado, e o EFI só entrega o
ambiente que ele exige (`csr-active-config 0x0A43`, `SecureBootModel Disabled`,
boot-args `nvfb/nvaccel/amfi`, `Lilu` + `AMFIPass`).

## 2. O que está neste repositório

```
EFI/
  BOOT/BOOTx64.efi
  OC/
    OpenCore.efi
    config.plist            ← validado com ocvalidate 1.0.8 (0 erros)
    ACPI/  SSDT-PLUG.aml    ← plugin-type / gerenciamento de energia
           SSDT-USBX.aml    ← limites de corrente USB
    Drivers/ OpenRuntime.efi, HfsPlus.efi, ResetNvramEntry.efi
    Kexts/  Lilu 1.7.3, AMFIPass 1.4.1 (só no modo NVIDIA),
            VirtualSMC 1.3.9 (+SMCProcessor, SMCSuperIO),
            WhateverGreen 1.7.2, AppleALC 1.9.8, RealtekRTL8111 3.0.4,
            IntelMausi 1.0.8, NVMeFix 1.1.3, RestrictEvents 1.1.6,
            CpuTscSync 1.1.2
docs/
  acpi/*.dsl             ← fontes dos SSDTs (+ opcionais: EC, SBUS-MCHC, PLUG-ALT)
  HARDWARE.md            ← peças recomendadas e ajustes de BIOS
  NVIDIA-RTX.md          ← driver NullMoth: instalação, verificação, desfazer
  DUAL-BOOT-WINDOWS.md   ← conviver com Windows Server em outro SSD (BitLocker, boot)
  BIOS-X99-2.17.1249.md  ← caminho exato de cada opção na BIOS AMI dessas X99
  POS-INSTALACAO.md      ← USB map, áudio, iMessage, updates
  SOLUCAO-DE-PROBLEMAS.md
variants/config-amd.plist ← config pronto para GPU AMD (RX 580/6600)
scripts/
  00-verificar-efi.sh    ← confere estrutura + kexts + ocvalidate
  01-baixar-macos.sh     ← baixa Sequoia 15.8.3 (Mist) + recovery
  02-criar-pendrive.sh   ← cria o pendrive bootável e copia o EFI
  03-montar-efi.sh       ← monta partição EFI
  04-gerar-serial.sh     ← gera Serial/MLB novos
  build-config-from-reference.py ← gera o config a partir do EFI que funciona
  build-config.py        ← gerador "do zero" (histórico; prefira o de cima)
  upgrade-keys-1.0.8.py  ← adiciona chaves novas do OpenCore 1.0.8
ocvalidate, macserial    ← binários oficiais do OpenCore 1.0.8
_downloads/BaseSystem.dmg ← recovery ~850 MB (internet install)
```

## 3. Escolhas técnicas (o porquê)

| Ajuste | Valor | Motivo |
|---|---|---|
| `Kernel > Quirks > AppleXcpmExtraMsrs` | `true` | **obrigatório** em Haswell-EP/Broadwell-EP (Xeon E5 v3/v4) |
| `AppleXcpmCfgLock` | `true` | maioria das X99 tem MSR 0xE2 travado |
| `ProvideCurrentCpuInfo` | `true` | reporta número de núcleos/threads correto em Xeon |
| `IgnoreInvalidFlexRatio` (UEFI) | `true` | Haswell ignora `MSR 0x194` |
| `DisableIoMapper` | `true` | VT-d pode ficar ligado na BIOS sem panic |
| `SecureBootModel` | `Disabled` | Sequoia em Haswell |
| `boot-args` | `... amfi_get_out_of_my_way=0x1 amfi=0x80 nvfb=1 nvaccel=1 nvfbheads=4 gfxrst=4` | libera o bundle Metal do driver RTX; `gfxrst=4` evita panic do WhateverGreen com a NVIDIA |
| `csr-active-config` | `430A0000` (0x0A43) | SIP reduzido: obrigatório para kext não assinada do driver RTX |
| `Kernel > Add` | `Lilu` + `AMFIPass` | AMFI bypass exigido pelo driver |
| `ResizeAppleGpuBars` / `ResizeGpuBars` | `0` / `-1` | valor seguro do instalador com NVIDIA (BAR grande trava o PCI) |
| `XhciPortLimit` | `false` | quebrado desde o Big Sur: mapeie USB no pós-instalação |

## 4. Antes de instalar: BIOS

Se sua placa é X99 chinesa com a BIOS **AMI Aptio 2.17.1249** (Huananzhi,
Jingsha, JGINYUE, Machinist), o caminho exato de cada opção está em
[docs/BIOS-X99-2.17.1249.md](docs/BIOS-X99-2.17.1249.md) — inclusive a aba
**IntelRCSetup**, que é onde ficam VT-d e Hyper-Threading nessas placas.

Resumo genérico (nomes variam por fabricante):

- **CSM / Legacy Boot**: `Disabled` (boot só UEFI)
- **Secure Boot**: `Disabled` / `Other OS`
- **Above 4G Decoding**: `Enabled` (essencial: a RTX mapeia memória acima de 4 GB)
- **Re-Size BAR / Resizable BAR**: `Disabled`
- **VT-d**: `Disabled` (ou `Enabled`, o config já lida via `DisableIoMapper`)
- **CFG Lock / MSR 0xE2**: `Disabled` (se sua placa permitir)
- **XHCI Hand-off**: `Enabled`
- **Fast Boot**: `Disabled`
- **Serial/COM Port**: `Disabled`
- **Hyper-Threading**: `Enabled`
- **Intel Virtualization (VT-x)**: `Enabled` (só se for usar VM)
- **Onboard Audio**: `Enabled`
- **TPM**: `Disabled`

## 5. Instalação (passo a passo)

```bash
# 0) confira o pacote
./scripts/00-verificar-efi.sh
```

**Modo RECOVERY (recomendado — funciona em pendrive de 8 GB+, inclusive os de 14 GB):**

```bash
./scripts/01-baixar-macos.sh /Volumes/3Tb/macOS   # só a parte do BaseSystem (849 MB)
diskutil list                                    # descubra o diskN do pendrive
./scripts/05-pendrive-recovery.sh diskN          # APAGA o pendrive; ~850 MB
```

O pendrive fica com `com.apple.recovery.boot/` (BaseSystem 847 MB) + `EFI/`.
Durante a instalação o restante do Sequoia 15.8.3 é baixado da Apple — por isso a
**Ethernet precisa funcionar** (não há Wi-Fi neste build).

**Modo completo (pendrive de 16 GB+):**

```bash
brew install mist-cli
./scripts/01-baixar-macos.sh /Volumes/3Tb/macOS                # .app de 15,7 GB
./scripts/02-criar-pendrive.sh "/Volumes/3Tb/macOS/Install macOS Sequoia.app" diskN
```

> Um pendrive de 14 GB **não** cabe o `.app` completo (15,7 GB). Use o modo recovery.

3. No PC alvo: BIOS em UEFI (seção 4), pendrive conectado em porta **USB 2.0** (traseira), boot pelo pendrive.
   O instalador roda no **framebuffer da firmware** (a RTX ainda não tem driver ali), então a
   interface fica lenta e em resolução baixa — é normal. A aceleração vem depois, com o driver.
4. No picker do OpenCore: `Install macOS Sequoia` → **Disk Utility** → apague o disco alvo como **APFS / GUID** → feche → `Install macOS Sequoia`.
5. O instalador reinicia 2–3 vezes. **Sempre boote pelo pendrive** e escolha o item `macOS Installer` / o novo volume; na 1ª vez o OpenCore já registra a entrada no disco.
6. Terminada a instalação, monte a EFI do **disco interno** e copie o EFI (passo 6 do pós-instalação).

## 6. Pós-instalação (resumo)

Detalhes em [docs/POS-INSTALACAO.md](docs/POS-INSTALACAO.md):

```bash
./scripts/03-montar-efi.sh disk0        # EFI do disco interno
sudo rm -rf /Volumes/EFI/EFI
sudo ditto EFI /Volumes/EFI/EFI
```

Depois: **driver da RTX** ([docs/NVIDIA-RTX.md](docs/NVIDIA-RTX.md)), mapa USB (USBToolBox),
layout de áudio, `en0` = Ethernet para iMessage/App Store, serial próprio.

## 7. Solução de problemas

Veja [docs/SOLUCAO-DE-PROBLEMAS.md](docs/SOLUCAO-DE-PROBLEMAS.md) — cobre tela preta, `Still waiting for root device`, panic em `AppleACPICPU`, áudio mudo, USB 3 lento e boot loop.

## 8. Avisos

- Hackintosh viola o EULA da Apple para uso em hardware não-Apple. Uso por sua conta e risco.
- O driver RTX é **experimental**, reduz a segurança do sistema (SIP/AMFI) e tem licença
  não comercial. Para máquina de trabalho, use GPU AMD.
- Faça backup antes de mexer em EFI/BIOS; guarde o pendrive, ele é o seu socorro.
- Antes de atualizar o macOS, faça backup do EFI e verifique se o OpenCore/kexts estão atualizados.

---

## 8. Serial / MLB — gere os seus

Este repositório **não** distribui Serial/MLB/UUID reais: os `config.plist` vêm com
placeholders (`C02XXXXXXXXXX` / `XXXXXXXXXXXXXXXXX` / ROM zerada).

Antes de usar, gere a sua identidade com o `macserial` incluído:

```bash
./scripts/04-gerar-serial.sh iMacPro1,1
```

Depois edite `PlatformInfo > Generic` no `EFI/OC/config.plist` (ou rode
`python3 scripts/build-config-from-reference.py`) com **Serial, MLB, ROM (MAC da
sua placa de rede) e UUID** — todos coerentes entre si. Sem isso, iCloud/iMessage
não funcionam (e usar o serial de outra pessoa quebra a conta dela).
