# Pós-instalação

## 1. Copiar o EFI para o disco interno (senão o PC só liga com o pendrive)

```bash
diskutil list                       # descubra o diskN do disco com o macOS
./scripts/03-montar-efi.sh disk0
sudo rm -rf /Volumes/EFI/EFI
sudo ditto EFI /Volumes/EFI/EFI
```

Reinicie sem o pendrive. Se não aparecer o boot do macOS, entre na BIOS e selecione
`OpenCore` como primeiro item de boot (ou use o picker do OpenCore → `Reset NVRAM` uma vez).

## 2. Ethernet como `en0` (obrigatório p/ iMessage, App Store, iCloud)

Só existe uma placa de rede (a cabeada), mas o macOS precisa dela como **en0** e **built-in**:

```bash
# confira
networksetup -listallhardwareports
```

Se a Ethernet **não** for `en0`:

```bash
sudo rm /Library/Preferences/SystemConfiguration/NetworkInterfaces.plist
sudo rm /Library/Preferences/SystemConfiguration/preferences.plist
# reinicie e reative o serviço em Ajustes > Rede
```

Se ainda assim não for built-in, adicione em `DeviceProperties` o caminho PCI da NIC com
`built-in` = `01`. Para o RTL8111 em X99 costuma ser `PciRoot(0x0)/Pci(0x1C,0x0)/Pci(0x0,0x0)`.

## 3. Mapa USB (necessário para USB 3.0 e para dormir/acordar)

`XhciPortLimit` não funciona no Sequoia, então as portas precisam ser mapeadas:

1. Baixe o **USBToolBox** (macOS): https://github.com/USBToolBox/tool/releases
2. `Discover Ports` → conecte um pendrive em **cada** porta (uma por vez, 5 s cada).
3. `Select Ports` → deixe marcadas as portas físicas usadas; marque as internas (ex.: header USB do gabinete) como `Internal`.
4. `Build Kext` → gera `UTBMap.kext` + `USBToolBox.kext`.
5. Copie as duas para `EFI/OC/Kexts/` e adicione no `config.plist` (depois do `Lilu`, antes de outros):

```python
# edite scripts/build-config.py, em Kernel.Add:
kext("USBToolBox.kext", "USB toolbox"),
kext("UTBMap.kext", "USB port map"),
```

6. Rode `python3 scripts/build-config.py && ./ocvalidate EFI/OC/config.plist` e copie de novo para a EFI.

Enquanto não mapear, use as portas **USB 2.0 traseiras** — elas funcionam.

## 3.5. Driver da GPU NVIDIA (RTX)

Se a placa é NVIDIA, a aceleração **não** vem do EFI: instale o driver NullMoth
depois do macOS instalado. Passo a passo completo em
[NVIDIA-RTX.md](NVIDIA-RTX.md). Resumo:

1. Baixe o app **1401** (recomendado) ou o `nullmoth-nvidia-3.0.tar.gz`.
2. Rode, permita a extensão em Ajustes → Privacidade e Segurança, reinicie.
3. Depois que carregar, adicione `Kernel > Block` → `com.apple.iokit.IONDRVSupport` / `Exclude`.
4. Confira: `kmutil showloaded --list-only | grep nullmoth` (4 linhas).

## 4. Áudio

`boot-args` já tem `alcid=1`. Se o som não sair:

```bash
# veja o codec detectado
ioreg -l | grep -i "alc-layout-id\|IOAudio"
```

Teste outros layouts para ALC1150/ALC892: `alcid=1, 2, 3, 5, 7, 11, 13, 15, 16, 17, 18, 20, 27, 28, 30, 31, 66, 69, 82, 98, 99`.
Altere em `config.plist > NVRAM > boot-args` e reinicie. Lista completa por codec:
https://github.com/acidanthera/AppleALC/wiki/Supported-codecs

## 5. SMBIOS / iMessage

O build já vem com serial gerado para `iMacPro1,1`. **Gere o seu** e nunca compartilhe:

```bash
./scripts/04-gerar-serial.sh iMacPro1,1
```

Atualize `SERIAL`, `MLB`, `ROM` (MAC da placa de rede **do PC alvo**) e `UUID` em
`scripts/build-config.py`, rode `python3 scripts/build-config.py` e valide.

Checklist para iMessage/FaceTime:
- Serial, MLB, ROM e UUID coerentes (todos do mesmo SMBIOS `iMacPro1,1`);
- `en0` = Ethernet (item 2);
- `SystemProductName` correto;
- após mudar, `Reset NVRAM` no picker do OpenCore.

## 6. Sensores e temperatura

`SMCProcessor` + `SMCSuperIO` já estão ativos. Para ver no sistema, instale
**HWMonitorSMC2** ou **iStat Menus**. Se `SMCSuperIO` causar instabilidade em alguma
placa, basta desabilitar essa kext no config.

## 7. Atualizações do macOS

- Atualizações menores (15.8.x) podem ser feitas pelo app Ajustes → Atualização de Software.
- Antes: **backup do EFI** (`cp -R /Volumes/EFI/EFI ~/efi-backup`).
- Se uma atualização quebrar o boot, boot pelo pendrive, reverta o EFI e investigue.
- **Com driver NVIDIA:** remova o driver antes de cada atualização (entrada
  “1401: Remove NVIDIA driver” no picker) e reinstale depois.
- Não atualize para **Tahoe 26.x** com este SMBIOS (`iMacPro1,1`) — o instalador recusa.

## 8. Afinações opcionais

- **Dormir/acordar**: teste `pmset sleepnow`. Se acordar com tela preta, desligue
  “Put hard disks to sleep” e/ou adicione `HibernateMode=None` (já é o padrão aqui).
- **Trim em SSD SATA**: `sudo trimforce enable` (NVMe não precisa).
- **Gráficos**: `agdpmod=pikera` já está nos boot-args; não remova com RX 6000.
- **OpenCore futuros**: baixe o release novo, substitua `BOOTx64.efi`, `OpenCore.efi`,
  `Drivers/*` e rode `ocvalidate` no seu `config.plist` antes de reiniciar.
