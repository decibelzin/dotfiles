#!/bin/sh
# Puxa as configs atuais do sistema pra dentro do repositório e mostra o que mudou.
# Depois é só: git add -A && git commit -m "..." && git push
set -e
cd "$(dirname "$0")"
rsync -a --exclude='*.bak*' --exclude='__pycache__' --exclude='hyprland.conf' --exclude='*.v1' \
    ~/.config/hypr ~/.config/waybar ~/.config/kitty ~/.config/rofi ~/.config/mako \
    ~/.config/fastfetch ~/.config/wlogout config/
cp ~/.config/gtk-3.0/gtk.css ~/.config/gtk-3.0/colors.css ~/.config/gtk-3.0/settings.ini config/gtk-3.0/
cp ~/.config/pcmanfm-qt/default/settings.conf config/pcmanfm-qt/default/
cp ~/.config/starship.toml config/
cp ~/.local/share/applications/kitty.desktop ~/.local/share/applications/org.gnome.Terminal.desktop local/share/applications/
cp ~/.zshrc zshrc
cp ~/.local/src/hypr-minimizar/main.cpp ~/.local/src/hypr-minimizar/compilar.sh plugins/hypr-minimizar/
git status --short
