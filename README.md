# dotfiles: Kali + Hyprland

Meu setup do Kali com Hyprland 0.56: tema Nord azul gelo, tudo com vidro (blur),
barra de título com botões (hyprbars), waybar flutuante, kitty, rofi.

Notebook: Lenovo LOQ 15IAX9 (Intel + NVIDIA), teclado ABNT2.

## O que tem aqui

| Pasta | O que é |
| --- | --- |
| `config/hypr` | `hyprland.lua` (config principal, em Lua), hypridle, hyprlock, hyprpaper e `scripts/` |
| `config/waybar`, `rofi`, `kitty`, `mako`, `wlogout`, `fastfetch`, `starship.toml` | visual de cada programa |
| `config/gtk-3.0` | barra de vidro dos apps GTK |
| `config/pcmanfm-qt` | ícones na área de trabalho (estilo Windows) |
| `firefox/` | `user.js` + `userChrome.css` (topo do Firefox de vidro) |
| `plugins/hyprbars-porapp` | patch no hyprbars: botão que só aparece em certos apps (`classes`) e `{addr}` no comando |
| `plugins/hypr-minimizar` | plugin próprio: faz o botão minimizar dos apps (Discord etc.) funcionar |
| `sistema/fn-lock.conf` | F1–F12 sem precisar de Fn (Lenovo) |
| `wallpapers/` | papéis de parede |
| `zshrc` | zsh com fastfetch e starship |

### Scripts (`config/hypr/scripts`)

- `volume-app.py`: popup de volume por app (botão de engrenagem na barra)
- `nova-aba.sh`: botão `+` dos terminais
- `alt-tab.py`: Alt+Tab por todas as janelas, inclusive minimizadas
- `resgatar-secreta.py`: tira da "área secreta" (minimizados) o app que pede pra aparecer
- `mostrar-desktop.py`: Super+D igual Windows
- `sessao.py`: salva as janelas e reabre tudo no próximo login (inclusive abas do kitty)
- `atalhos.sh`: Super+/ mostra os atalhos
- `print.sh`, `area-transferencia.sh`, `luz-noturna.sh`

## Instalar num sistema novo

1. Pacotes:
   ```sh
   sudo apt install hyprland hyprland-dev hyprland-plugin-hyprbars hyprpaper hypridle hyprlock \
       hyprpolkitagent hyprland-qtutils hyprsunset hyprpicker waybar kitty rofi mako-notifier wlogout \
       cliphist wtype swappy grim slurp fastfetch starship chafa pcmanfm-qt \
       python3-gi gir1.2-gtk-3.0 gir1.2-gtklayershell-0.1 pulseaudio-utils rsync
   ```
   Fonte: JetBrainsMono Nerd Font.
2. Configs: `./instalar.sh` (o que já existir vira `.bak-dotfiles`).
3. Plugins (precisam bater com a versão do Hyprland):
   ```sh
   plugins/hyprbars-porapp/instalar.sh
   plugins/hypr-minimizar/compilar.sh
   ```
4. Fn Lock (só no Lenovo): `sudo cp sistema/fn-lock.conf /etc/tmpfiles.d/`
5. Sair e entrar na sessão **Hyprland**.

## Atualizar este repositório

Depois de mexer em alguma coisa no sistema:

```sh
./atualizar.sh
git add -A && git commit -m "o que mudou" && git push
```

## Cuidados

- **Nunca** recarregar plugin com a sessão aberta (`hyprctl plugin load/unload`): derruba o Hyprland.
  Plugin novo só no próximo login.
- Se o Hyprland atualizar, recompilar os dois plugins.
- Trocar o caminho do plugin no `hyprland.lua` com a sessão aberta faz os botões da barra sumirem até o próximo login.
