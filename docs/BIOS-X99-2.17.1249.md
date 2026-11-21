# BIOS AMI Aptio 2.17.1249 (X99 Huananzhi / Jingsha / JGINYUE / Machinist)

Essa versão `2.17.1249` (AMI Aptio V, Core 5.11) é o firmware padrão das X99
chinesas — Huananzhi X99-AD3/F8, Jingsha X99-D8, JGINYUE X99M-PLUS, Machinist.
O layout tem **abas diferentes** de uma Asus/Gigabyte: as opções de CPU e chipset
ficam na aba **IntelRCSetup**, não em Advanced.

- Entrar na BIOS: **Del** durante o POST
- Boot menu (escolher disco): **F11** ou **F7** (aparece no rodapé da tela)
- Salvar e sair: **F10**

> **Primeiro passo:** F9 (Optimized Defaults) → depois aplique a tabela abaixo.
> Depois de qualquer troca de peça, repita o F9.

---

## 1. Tabela de opções

### Aba Advanced

| Caminho | Opção | Valor | Por quê |
|---|---|---|---|
| Advanced → **PCI Subsystem Settings** | **Above 4G Decoding** | **Enabled** | a RTX mapeia memória acima de 4 GB; sem isso a 4070 Super pode nem dar vídeo |
| Advanced → PCI Subsystem Settings | **Re-Size BAR Support** | **Disabled** | com ReBAR ligado o macOS trava no `PCI configuration end` |
| Advanced → PCI Subsystem Settings | SR-IOV Support | Disabled | irrelevante para desktop, evita BAR estranho |
| Advanced → **CSM Configuration** | **CSM Support** | **Disabled** | macOS exige UEFI puro |
| Advanced → CSM Configuration | Boot option filter | **UEFI only** | se CSM Support não puder ser desligado |
| Advanced → CSM Configuration | Storage / Video / Other PCI | **UEFI** | idem |
| Advanced → **USB Configuration** | **XHCI Hand-off** | **Enabled** | entrega o controle das portas ao SO |
| Advanced → USB Configuration | Legacy USB Support | Disabled | menos conflito; se o teclado sumir no setup, deixe Enabled |
| Advanced → **SATA Configuration** | SATA Mode | **AHCI** | RAID/IDE quebra o boot |
| Advanced → SATA Configuration | sSATA Mode (SCU) | **AHCI** | controlador secundário das X99 |
| Advanced → **Super IO Configuration** | Serial Port 1 / 2 | **Disabled** | IRQ livre, evita conflito de áudio |
| Advanced → **Serial Port Console Redirection** | Console Redirection | **Disabled** | idem |
| Advanced → **CPU Configuration** | CFG Lock *(se aparecer)* | **Disabled** | MSR 0xE2; se não existir, o EFI já cobre (`AppleXcpmCfgLock`) |
| Advanced → CPU Configuration | Intel SGX | Disabled | desnecessário |
| Advanced → ACPI Settings | Enable Hibernation | Disabled | evita hibernação suja |

### Aba IntelRCSetup

| Caminho | Opção | Valor | Por quê |
|---|---|---|---|
| IntelRCSetup → **Processor Configuration** | **Hyper-Threading** | **Enabled** | 12c/24t |
| IntelRCSetup → Processor Configuration | **Intel Virtualization Technology (VMX)** | **Enabled** | só se for usar VM; não atrapalha |
| IntelRCSetup → Processor Configuration | **Intel VT for Directed I/O (VT-d)** | **Disabled** | evita panic do AppleACPICPU |
| IntelRCSetup → Processor Configuration | C-States / C1E | Auto | não mexa |
| IntelRCSetup → **PCH Devices** | **PCH state after G3** | **Last State** (ou **On**) | *servidor*: liga sozinho após queda de energia |
| IntelRCSetup → PCH Devices | PCH LAN / WOL | conforme necessário | opcional |

> Se `Intel VT for Directed I/O` não estiver aí, procure em
> **IntelRCSetup → IIO Configuration**.

### Aba Security

| Caminho | Opção | Valor |
|---|---|---|
| Security → **Secure Boot** | **Secure Boot Support** (ou *Secure Boot*) | **Disabled** |
| Security → Secure Boot → Key Management | se estiver "Enabled" com chaves | mude para Disabled antes; não apague as chaves |

> Com Secure Boot ligado, o OpenCore não carrega kexts não assinadas — o boot
> para no logo. É obrigatório desligar.

### Aba Boot

| Caminho | Opção | Valor | Por quê |
|---|---|---|---|
| Boot | **Fast Boot** | **Disabled** | firmware não pula a inicialização do USB |
| Boot | Quiet Boot | Disabled | você quer ver as mensagens durante o ajuste |
| Boot | Setup Prompt Timeout | 5 | tempo para apertar Del/F11 |
| Boot | **Boot Option #1** | **OpenCore** (ou o pendrive) | ordem de boot |
| Boot | Hard Drive BBS Priorities | disco do macOS | quando há vários discos |

---

## 2. O que fazer se a opção não existir

| Faltando | Solução |
|---|---|
| **Above 4G Decoding** | adicione `npci=0x2000` aos `boot-args` — **nunca os dois juntos** |
| **CFG Lock** | já resolvido: `AppleXcpmCfgLock=true` no config |
| **VT-d** | já resolvido: `DisableIoMapper=true` no config |
| **Secure Boot** | procure em `Security → Secure Boot` ou `Boot → Secure Boot`; em último caso desabilite as chaves em Key Management |
| **XHCI Hand-off** | geralmente não é necessário; USB 2.0 traseiro funciona no instalador |
| Menu **IntelRCSetup** ausente | aí é uma placa X99 de marca (Asus/Gigabyte/ASRock): use `Advanced → System Agent (SA) Configuration` para VT-d/Above 4G e `Advanced → CPU Configuration` para o resto |

---

## 3. Pegadinhas específicas dessa BIOS

1. **Mudar uma opção pode resetar outras.** Nessas AMI chinesas, ativar/desativar
   CSM às vezes volta o Secure Boot para Enabled. Confira Secure Boot **depois**
   de mexer em CSM, e salve.
2. **Tela preta com a 4070 Super mesmo com Above 4G**: em algumas unidades o
   "Above 4G Decoding" só entra em vigor depois de um **clearing CMOS**
   (jumper/bateria). Se o valor não "pega", faça Load Optimized Defaults (F9),
   salve, desligue da tomada, limpe o CMOS e configure de novo.
3. **Turbo Boost unlock / microcode mod**: se a placa tiver BIOS modificada
   (patch "鸡血"), o boot do macOS pode ficar instável. Se der panic aleatório,
   volte para a BIOS original antes de culpar o OpenCore.
4. **Dual socket (X99-D8 / 8D4)**: `CpuTscSync.kext` já está no EFI; se ainda
   travar com 2 CPUs, comece com **uma CPU** instalada para validar.
5. **`PCH state after G3 = On`** é ótimo para servidor, mas se você for tirar o
   SSD do Windows com frequência, use `Last State` para não ligar sozinho.

---

## 4. Checklist para imprimir

```
[ ] F9 (Optimized Defaults) + F10
[ ] Advanced > PCI Subsystem Settings > Above 4G Decoding = Enabled
[ ] Advanced > PCI Subsystem Settings > Re-Size BAR Support = Disabled
[ ] Advanced > CSM Configuration > CSM Support = Disabled
[ ] Advanced > USB Configuration > XHCI Hand-off = Enabled
[ ] Advanced > SATA Configuration > SATA/sSATA Mode = AHCI
[ ] Advanced > Super IO > Serial Port 1 = Disabled
[ ] IntelRCSetup > Processor Configuration > Hyper-Threading = Enabled
[ ] IntelRCSetup > Processor Configuration > VT-d = Disabled
[ ] IntelRCSetup > PCH Devices > PCH state after G3 = Last State (opcional)
[ ] Security > Secure Boot = Disabled
[ ] Boot > Fast Boot = Disabled
[ ] Boot > Boot Option #1 = pendrive / OpenCore
[ ] F10 save & exit
[ ] Conferir de novo: Secure Boot ainda Disabled?
```

---

## 5. Socorro: ficou sem vídeo depois de mexer na BIOS

Isso é quase sempre uma destas três coisas, nesta ordem de probabilidade:

1. **CSM desligado + option ROM de vídeo em Legacy** → o POST não inicializa a GPU.
2. **Above 4G Decoding ligado** com o BAR do slot mal alocado → o firmware trava
   antes de desenhar a tela.
3. **Resizable BAR** ligado junto com Above 4G.

### Passo 1 — Limpar o CMOS (devolve o vídeo em ~1 min)

1. Desligue e **tire o cabo de força**.
2. Segure o botão power por 10 s (descarrega a fonte).
3. Ache o jumper **CLR_CMOS** (perto da bateria) e encoste a chave/ jumper nos
   pinos 2–3 por 10 s; **ou** tire a bateria CR2032 e espere 5 min.
4. Recoloque tudo, ligue, entre na BIOS (Del) e dê **F9 → F10**.

Se o vídeo voltar: o culpado é uma das opções que você acabou de aplicar.

### Passo 1.5 — Antes de tudo: esperar e confirmar que está vivo

Depois de tirar a bateria, a X99 **retreina a memória**: pode ficar 1–3 minutos
sem imagem, com as ventoinhas girando. Não desligue antes disso.

Sinais de que a máquina está viva mesmo sem tela:

| Sinal | Significado |
|---|---|
| Tecla **NumLock/CapsLock** acende e apaga ao apertar | o POST passou, só o vídeo morreu |
| `ping <ip>` responde | o SO bootou |
| Ventoinhas aceleram e voltam | POST em andamento |
| Beeps longos repetidos | memória/GPU |

### Passo 2 — Se mesmo com CMOS limpo não houver vídeo

| Teste | O que indica |
|---|---|
| Trocar o cabo/porta (DP ↔ HDMI) | saída primária diferente |
| Tirar e recolocar a GPU, e **reconectar o cabo de força PCIe** | contato/BAR |
| Testar a **3060** em vez da 4070 Super | placa/firmware |
| Mover para o **slot x16 superior** (mais próximo da CPU) | slot/linhas |
| Olhar LED de debug / ouvir beeps | memória, CPU ou VGA |

### Passo 3 — Confirmar se a máquina está viva mesmo sem tela

Como é servidor, dá para saber se ele está **bootando** sem monitor:

```bash
ping <ip-do-servidor>          # do seu Mac
```

Se responder, o problema é **só saída de vídeo**, não o sistema.

### Passo 4 — Reaplicar as opções UMA por vez

Não configure tudo de uma vez. Ordem segura, reiniciando e conferindo o vídeo
depois de cada item:

1. SATA/sSATA = AHCI
2. XHCI Hand-off = Enabled
3. Serial Port = Disabled
4. Secure Boot = Disabled
5. **CSM Support = Disabled** ← teste aqui; se perder vídeo, veja 5.1
6. Fast Boot = Disabled
7. **Above 4G Decoding = Enabled** ← teste aqui; se perder vídeo, veja 5.2
8. Re-Size BAR = Disabled (só aparece se o 7 estiver ligado)

### 5.1 Se morrer no CSM — a pegadinha do "UEFI only"

Nessa BIOS existem **duas coisas diferentes** que muita gente confunde:

| Opção | O que faz | Risco |
|---|---|---|
| `Boot option filter = UEFI only` | só afeta **de quais dispositivos** ele tenta bootar | baixo |
| `CSM Support = Disabled` | desliga **todo o suporte legacy**, inclusive o *Video Option ROM* legacy | **alto** |
| `Video = Legacy/UEFI/Do not launch` (dentro de CSM Configuration) | qual ROM de vídeo o firmware usa no POST | **é aqui que morre** |

Ou seja: ao trocar o filtro e depois desligar o CSM, o firmware passa a precisar
do **GOP UEFI da placa de vídeo** — e se o `Video` estiver em `Legacy` (ou a VBIOS
da GPU não tiver GOP), o POST não desenha nada.

**Ordem correta:**

1. `Advanced → CSM Configuration` → **Video = UEFI** (e `Storage = UEFI`,
   `Other PCI devices = UEFI`) — **salve e teste o vídeo aqui**.
2. Só depois mude `Boot option filter = UEFI only`.
3. Só depois tente `CSM Support = Disabled`.

**Se o passo 1 já matar o vídeo**, a VBIOS da sua GPU está sem GOP UEFI (comum em
placa usada/vinda de mineração). Aí:

- deixe **CSM Support = Enabled** com **Boot option filter = UEFI only** — o
  macOS instala e funciona assim, você só não consegue dar boot em disco Legacy;
- ou regrave a VBIOS com GOP (tool do fabricante / `nvflash` com ROM oficial);
- ou teste a outra placa (3060), que provavelmente tem GOP.

> **Sobre o macOS com CSM ligado:** funciona. O OpenCore inicializa em UEFI e o
> sistema não usa nada do CSM. O único cuidado é nunca dar boot em disco Legacy.

### 5.2 Se morrer no Above 4G

Deixe **Above 4G = Disabled** e adicione `npci=0x2000` aos `boot-args`:

```
-v keepsyms=1 debug=0x100 alcid=1 gfxrst=4 nvfb=1 nvaccel=1 nvfbheads=4
-nvkmsnosmooth amfi_get_out_of_my_way=0x1 amfi=0x80 ipc_control_port_options=0
npci=0x2000
```

Isso resolve o boot e a instalação. Para o **driver NVIDIA** o Above 4G é
recomendado (ele mapeia memória acima de 4 GB); se a placa não aceitar, o driver
pode falhar ao subir a GPU — nesse caso o caminho é a AMD.
