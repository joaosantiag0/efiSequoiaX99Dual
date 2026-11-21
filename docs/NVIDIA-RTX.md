# GPU NVIDIA RTX no macOS Sequoia (driver NullMoth)

> **Resumo:** RTX **não** tem driver da Apple. Existe um driver independente
> (NullMoth, versão 3.0 de 14/11/2026) que faz **GTX 16 e RTX 20/30/40/50**
> funcionarem no Sequoia com Metal 3. É experimental, exige SIP reduzido e não
> tem suporte oficial. Para trabalho crítico, use uma GPU AMD (ver seção 5).

## 1. O que o EFI deste repositório já faz

`EFI/OC/config.plist` é gerado no **modo NVIDIA** (`python3 scripts/build-config.py nvidia`):

| Ajuste | Valor | Por quê |
|---|---|---|
| `boot-args` | `nvfb=1 nvaccel=1 nvfbheads=4 -nvkmsnosmooth amfi_get_out_of_my_way=0x1 amfi=0x80 ipc_control_port_options=0 gfxrst=4 -v keepsyms=1 debug=0x100 alcid=1` | liga framebuffer/accelerator e libera AMFI para o bundle Metal |
| `csr-active-config` | `430A0000` (0x0A43) | permite kexts não assinados |
| `SecureBootModel` | `Disabled` | Apple Secure Boot recusa kext não assinada |
| `Kernel > Add` | `Lilu` + **`AMFIPass 1.4.1`** | AMFI bypass |
| `agdpmod=pikera` | **removido** | era só para AMD Navi; o README do driver manda tirar |
| `ResizeAppleGpuBars` | `0` | valor seguro do **instalador** com NVIDIA |
| `ResizeGpuBars` | `-1` | não força resize do BAR no firmware |

O EFI **não** traz as kexts do driver: elas vão para `/Library/Extensions` do
sistema instalado (é assim que o projeto funciona — não injete por `EFI/OC/Kexts`).

## 2. BIOS

- **Above 4G Decoding**: `Enabled` (o driver mapeia memória acima de 4 GB)
- **CSM**: `Disabled`
- **Resizable BAR**: `Disabled` (em X99 normalmente nem existe)
- Secure Boot: `Disabled`

## 3. Instalação do driver (depois do macOS instalado)

### Opção A — app 1401 (recomendado pelo autor)

```bash
# baixe 1401-Mac-3.0.dmg de:
# https://github.com/nullmoth/nvidia-macos-driver/releases
```

Abra o `.dmg`, rode o **1401** e siga os passos. Ele:
- acha a partição EFI que iniciou a máquina;
- mostra cada mudança no `config.plist` antes de aplicar e faz backup;
- instala o driver e a firmware GSP;
- adiciona a entrada **“1401: Remove NVIDIA driver”** no picker do OpenCore —
  é o seu botão de desfazer se algo der errado.

### Opção B — manual

```bash
cd ~/Downloads
tar -xzf nullmoth-nvidia-3.0.tar.gz
cd pkgroot
shasum -a 256 -c SHA256SUMS      # todas as linhas precisam dizer OK
sudo ./install.sh
sudo shutdown -r now
```

No primeiro boot, o sistema pode **parar até ~1 minuto em “PCI configuration
end”** enquanto a GPU sobe — é normal, não desligue.

Depois o macOS pede para **permitir a extensão** em Ajustes → Privacidade e
Segurança. Permita e reinicie de novo.

### Verificação

```bash
kmutil showloaded --list-only | grep nullmoth      # 4 linhas
system_profiler SPDisplaysDataType | head -20      # "Metal: Supported"
```

## 4. Passo que só é feito DEPOIS do driver instalado

Depois que o driver estiver carregando, exclua o `IONDRVSupport` para o
framebuffer da firmware não roubar o display index 0 do `NVRMFB`:

`Kernel > Block` → nova entrada:

| Campo | Valor |
|---|---|
| Identifier | `com.apple.iokit.IONDRVSupport` |
| Enabled | `true` |
| Strategy | `Exclude` |
| MinKernel / MaxKernel | vazio |

> **Não** faça isso antes de instalar o driver: o **instalador** do macOS roda
> no framebuffer da firmware e precisa do `IONDRVSupport` ativo.

## 5. Alternativa sem risco: GPU AMD dedicada

Se o Mac for máquina de trabalho, o caminho estável é manter a RTX para Windows
e colocar uma AMD barata para o macOS (a placa-mãe X99 tem slots de sobra):

| Placa | Situação | Preço usado (BR) |
|---|---|---|
| RX 580 8 GB | suportada nativa (Polaris) | ~R$ 400–600 |
| RX 6600 | suportada nativa (Navi 23) — a do PC de referência | ~R$ 900–1.100 |
| RX 6800 / 6900 XT | topo suportado (Navi 21) | ~R$ 1.800+ |

Nesse caso, gere o EFI no modo AMD:

```bash
python3 scripts/build-config.py amd && cp variants/config-amd.plist EFI/OC/config.plist
```

e no macOS desative a RTX (SSDT ou `DeviceProperties` com `disable-gpu`), para
não haver conflito de drivers.

## 6. Limitações reais do driver

- **SIP reduzido e AMFI liberado** = a máquina fica menos protegida. Não use
  como servidor exposto.
- **Licença PolyForm Noncommercial**: uso pessoal/pesquisa ok, uso comercial não.
- **Atualizações do macOS**: remova o driver (entrada “Remove NVIDIA driver”)
  antes de atualizar e reinstale depois.
- **Dual boot com Windows**: entre no Windows pelo menu de boot da firmware
  (F12/F8), **não** pelo picker do OpenCore — `ResizeGpuBars` é aplicado ao
  hardware antes do SO e o Windows pode dar BSOD.
- Desenvolvido/testado em RTX 5060; RTX 5070/5080 reportadas funcionando. RTX 20
  e 30 têm relatos, mas menos cobertura. Tenha o pendrive de recovery à mão.
- Sem aceleração de vídeo por hardware em alguns codecs; H.264/HEVC podem cair
  para decodificação por software dependendo da placa.

## 7. Se der tela preta depois de instalar o driver

1. Escolha **“1401: Remove NVIDIA driver”** no picker (desfaz tudo).
2. Ou boote com `-nvrmnogo` nos boot-args (driver fica idle, usa framebuffer).
3. Ou adicione `-nvrmnoflip` (corrige flicker/tearing) / `nvrmsettle=10000`
   (BAR1 demorando a subir).
4. Último recurso: `sudo ./uninstall.sh` de dentro do `pkgroot` restaurado.

## 8. Trocar de GPU: RTX 3060 → RTX 4070 Super

Testar na 3060 primeiro é a ordem certa (Ampere é mais reportada que Ada), mas o
EFI **não muda** entre as duas:

| | RTX 3060 (GA106, Ampere) | RTX 4070 Super (AD104, Ada) |
|---|---|---|
| Suporte do driver | Turing+ → sim | Turing+ → sim |
| Above 4G Decoding | obrigatório | **mais crítico** (BAR maior) |
| Resizable BAR | manter `off` | manter `off` |
| Consumo | 170 W | 220 W (fonte 600 W+) |
| Boot-args | os mesmos já gravados | os mesmos |

Nada a editar no `config.plist` ao trocar de placa. Só reinicie.

Se a 4070 Super não der imagem no primeiro boot com o driver:

1. Adicione `nvrmsettle=10000` aos boot-args (BAR1 demorando a ser alocado).
2. Troque a saída de vídeo (DisplayPort ↔ HDMI) — em Ada a saída primária varia.
3. Se houver flicker/tearing com o mouse, adicione `-nvrmnoflip`.
4. Se travar no logo, boote com `-nvrmnogo` (driver idle) e investigue pelo log.

> Depois de trocar a placa, o driver baixa a firmware GSP correspondente na
> primeira inicialização — os primeiros 30–60 s podem parecer travados em
> “PCI configuration end”. Não desligue.

> Se um dia voltar para a AMD, use `variants/config-amd.plist` (tem
> `agdpmod=pikera`) **e** remova o driver NVIDIA com a entrada
> “1401: Remove NVIDIA driver” do picker.
