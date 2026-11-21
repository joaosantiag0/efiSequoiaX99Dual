# Lista de peças — PC "gêmeo" da máquina de referência

A referência usada para este EFI: **Xeon E5-2673 v3 (12c/24t) + X99 + RX 6600 8 GB + macOS Sequoia 15.3.1**, rodando estável. Abaixo o que comprar/evitar para o PC novo.

## Núcleo (obrigatório)

| Peça | Recomendação | Por quê |
|---|---|---|
| CPU | Xeon **E5-2680 v4** (14c/28t, 2.4–3.3 GHz) ou E5-2673 v3 (mais barato) | v3/v4 = Haswell-EP/Broadwell-EP, mesma família do build de referência |
| Placa-mãe | X99 com chipset **X99/C612**, UEFI decente (Asus X99-A II, Gigabyte GA-X99-UD4, ou Kllisre/Huananzhi X99-F8 se o orçamento for apertado) | BIOS de marca simplifica CFG Lock, Above 4G e boot UEFI |
| Memória | 4×8 GB ou 4×16 GB DDR4 (ECC REG é aceito em Xeon) | **4 canais** — é o grande ganho do X99 |
| GPU (o que você tem) | **NVIDIA RTX 20/30/40/50** ou GTX 16 | sem driver da Apple → driver NullMoth 3.x, experimental (ver NVIDIA-RTX.md) |
| GPU (estável, opcional) | **Radeon RX 580 / 6600 / 6800** | suporte nativo, Metal 3, `variants/config-amd.plist` |
| Disco | NVMe M.2 (Kingston KC3000, WD SN770) | `NVMeFix` cobre o resto |
| Rede | **Ethernet onboard Realtek RTL8111** ou Intel I218/I219 | sem Wi-Fi, este é o único acesso à internet |
| Áudio | Codec onboard ALC1150/ALC892/ALC887 | `AppleALC` |
| Fonte | 500–650 W de marca | RX 6600 consome ~130 W |

## Pegadinhas de compra

- **GPU NVIDIA:** RTX 20-50 e GTX 16 só funcionam com o driver independente NullMoth (experimental, SIP reduzido). Se a máquina é de trabalho, coloque uma **AMD RX 580/6600** ao lado da RTX (a X99 tem slots) e use o macOS nela. GTX 900/10 (Maxwell/Pascal) ficam no máximo no High Sierra; Kepler vai até Monterey sem patch.
- **Evite Wi-Fi Intel AX200/AX201/Realtek 8822.** Precisam de `itlwm`, perdem AirDrop/Handoff e Handoff contínuo. Como o projeto é cabeado, não compre placa Wi-Fi.
- **Placas X99 chinesas**: quase todas funcionam, mas confira no manual se existe opção “Above 4G Decoding” e se o XHCI expõe as portas traseiras. Se faltar, use uma placa PCIe USB 3.0 com chip Renesas/NEC (suportada nativamente via `AppleUSBXHCI`).
- **Rede Intel I211-AT** (comum em X99 Asus/Gigabyte): o `IntelMausi` **não** cobre I210/I211. Nesse caso instale o `AppleIGB.kext`. As kexts de rede já incluídas cobrem I218/I219 e RTL8111/8168.
- **Memória**: Xeon E5 v3/v4 aceita DDR4 ECC REG (mais barata). Placa X99 de marca pode exigir UDIMM — verifique a QVL.

## Verificação rápida no PC alvo (antes de instalar)

Ligue o PC com um Linux live ou pelo próprio instalador e confirme:

```bash
lspci -nn | grep -Ei "vga|ethernet|audio"
```

- GPU: se for AMD, `1002:73ff` (RX 6600) ou outra `1002:73xx`. Se for NVIDIA, `10de:` (confira a
  família no [card support](https://github.com/nullmoth/nvidia-macos-driver) do driver).
- Ethernet deve ser `10ec:8168` (Realtek) ou `8086:15b8/15bb` (Intel I219).
- Áudio deve ser `8086:8d20` (X99) + codec Realtek.

Se os IDs baterem com a tabela acima, o EFI deste repositório sobe sem mudanças.

## Comparação com a máquina de referência

| | Referência (esta máquina) | PC novo alvo |
|---|---|---|
| CPU | E5-2673 v3 | E5-2673 v3 / v4 |
| GPU | RX 6600 8 GB (nativa) | **NVIDIA RTX** (driver NullMoth) |
| Wi-Fi | nenhum | nenhum |
| macOS | 15.3.1 | **15.8.3 (24H241)** |
| SMBIOS | iMacPro1,1 | iMacPro1,1 |
| EFI | igual em estrutura | mesma base, gerado em modo `nvidia` |
