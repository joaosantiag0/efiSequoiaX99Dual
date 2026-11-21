# Dual boot: macOS (SSD novo) + Windows Server (SSD existente)

Resposta curta: **nada do Windows é apagado** pelo instalador do macOS. O macOS
grava só no SSD novo (container APFS + Preboot + Recovery) e nada é escrito na
partição EFI nem nas partições NTFS do SSD do Windows.

O que pode te dar dor de cabeça são **três coisas de firmware/BIOS**, não o disco:

1. **BitLocker** (se o Windows Server usa) — desligar Secure Boot/TPM na BIOS
   dispara o pedido da chave de recuperação.
2. **Windows instalado em modo Legacy/MBR** — ao colocar a BIOS em UEFI-only
   (necessário para o macOS), o Windows deixa de bootar.
3. **Ordem de boot** — o OpenCore se registra como primeiro; voltar ao Windows
   passa a ser F12 no POST.

---

## 1. Antes de instalar o macOS (faça nesta ordem)

### 1.1 Confira se o Windows é UEFI

No Windows Server, abra `diskpart` como administrador:

```
diskpart
list disk
select disk 0        # o disco do Windows
detail disk
exit
```

- Se aparecer **`GPT`** na coluna `Gpt` → é UEFI. ✅ pode seguir.
- Se o disco tiver `*` na coluna `Mbr` → é **Legacy**. Veja a seção 5 antes de continuar.

Confirme também a partição EFI existente:

```
list volume
```
Deve existir um volume FAT32 de ~100–500 MB sem letra (System/EFI).

### 1.2 Suspenda o BitLocker (se estiver ativo)

```powershell
manage-bde -status
```

Se `Protection Status` for **On**:

```powershell
manage-bde -protectors -disable C: -RebootCount 2
```

Isso deixa a máquina reiniciar 2 vezes sem pedir a chave. **Guarde a chave de
recuperação** (`manage-bde -protectors -get C:`) em outro lugar mesmo assim.
Reative depois do dual boot configurado: `manage-bde -protectors -enable C:`.

> Se você não fizer isso e desabilitar Secure Boot/TPM na BIOS, o próximo boot
> para no prompt de recuperação do BitLocker.

### 1.3 Desligue o Fast Startup / hibernação

```powershell
powercfg /h off
```

Com Fast Startup, o NTFS fica "sujo" e o macOS monta o volume somente leitura
(ou não monta). Não corrompe nada, mas atrapalha.

### 1.4 Anote a identidade do SSD do Windows

```powershell
Get-PhysicalDisk | Select-Object FriendlyName, SerialNumber, Size, MediaType
Get-Disk | Select-Object Number, FriendlyName, Size, PartitionStyle, SerialNumber
```

Isso é o que você vai usar para não errar de disco no Disk Utility. Anote
**tamanho e serial** do SSD do Windows.

### 1.5 (Opcional, mas à prova de tudo) Desconecte o SSD do Windows

Se o servidor permite acesso físico, desconectar o cabo SATA/NVMe do SSD do
Windows durante a instalação elimina **qualquer** risco de apagar o disco errado.
Reconecte depois. Se não puder abrir, pule — só redobre a atenção no passo 2.2.

---

## 2. Instalando o macOS no SSD novo

### 2.1 O SSD novo precisa aparecer

Se ele **nunca** foi usado, pode estar sem tabela de partição e o Disk Utility
mostra só depois de "Mostrar todos os dispositivos" (menu **Ver** → **Mostrar
todos os dispositivos**).

### 2.2 Apague o disco CERTO

Confira **duas vezes** por tamanho e nome antes de apagar:

- O SSD novo = o que você quer para o macOS.
- O SSD do Windows = **não aparece com nome amigável no Disk Utility**, mas
  aparece como `diskNsM` (NTFS). Não encoste nele.

Formate com **APFS / GUID**.

### 2.3 O que acontece com o SSD do Windows durante a instalação

| Ação | Ocorre no SSD do Windows? |
|---|---|
| Formatar/papagar | **Não** |
| Criar container APFS | **Não** (só no SSD novo) |
| Escrever na partição EFI | **Não** — o macOS usa a EFI do disco onde está |
| Escrever NVRAM da placa | **Sim** (entrada de boot do OpenCore) |

Ou seja: o conteúdo do Windows fica intacto; só a ordem de boot muda.

---

## 3. Depois de instalar: como voltar a cada sistema

- **macOS**: pela entrada `OpenCore` da BIOS (o `LauncherOption=Full` do
  `config.plist` registra ela automaticamente).
- **Windows Server**: tecla de boot menu no POST (**F12 / F8 / F11** conforme a
  placa) → escolha **`Windows Boot Manager`**. Não precisa mexer em BIOS.

> **Não** boote o Windows pelo picker do OpenCore se puder evitar. O OpenCore
> aplica `ResizeGpuBars`, SMBIOS e SSDTs, e o Windows pode dar BSOD ou trocar o
> driver de vídeo. F12 é o caminho limpo.

Se o `Windows Boot Manager` desaparecer da lista do F12, ele continua no disco:
entre na BIOS → Boot → *Add Boot Option* → aponte para
`\EFI\Microsoft\Boot\bootmgfw.efi` na partição EFI do SSD do Windows.

---

## 4. Relógio errado ao alternar entre os sistemas

O macOS grava **UTC** no RTC; o Windows grava **hora local**. Resultado: 3 h de
diferença. Conserte no Windows (uma vez só), como administrador:

```cmd
reg add "HKLM\SYSTEM\CurrentControlSet\Control\TimeZoneInformation" /v RealTimeIsUniversal /t REG_DWORD /d 1 /f
```

---

## 5. Se o Windows estiver em Legacy/MBR

O macOS **exige** UEFI + CSM desligado. Com o Windows em Legacy você tem 3 saídas:

1. **Converter o Windows para UEFI (recomendado)** — `mbr2gpt /validate /allowFullOS`
   e depois `mbr2gpt /convert /allowFullOS`, com a BIOS em UEFI. Faça backup antes.
2. **Alternar CSM na BIOS** conforme o sistema (chato, mas funciona): CSM off
   para macOS, CSM on para Windows. Nesse caso, no OpenCore use
   `Misc > Boot > LauncherOption = Disabled` para não brigar com a ordem de boot.
3. **Reinstalar o Windows em UEFI** (último caso).

---

## 6. Como desfazer tudo e voltar só para o Windows

1. BIOS → Boot → coloque `Windows Boot Manager` como primeiro.
2. Opcional: apague a pasta `EFI/OC` da partição EFI do SSD novo
   (a EFI do Windows não é tocada).
3. Se o OpenCore ainda aparecer na lista de boot, remova a entrada `OpenCore`/
   `Bootstrap` na própria BIOS (ou `Reset NVRAM` no picker + remover a entrada).

---

## Checklist de 30 segundos

- [ ] `detail disk` no diskpart mostrou **GPT** no disco do Windows
- [ ] `manage-bde -status` → se On, **suspenso** e chave guardada
- [ ] `powercfg /h off`
- [ ] Anotei tamanho + serial dos dois SSDs
- [ ] (se possível) desconectei o SSD do Windows
- [ ] BIOS: CSM off, Secure Boot off, Above 4G on
- [ ] No Disk Utility apaguei **só** o SSD novo (APFS/GUID)
- [ ] Anotei que o Windows volta pelo **F12 → Windows Boot Manager**
