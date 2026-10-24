#!/bin/sh
# Recompila o hyprbars com o patch "botão por app" (classes + {addr}).
# Rodar de novo sempre que o Hyprland atualizar; vale no próximo login
# (NUNCA recarregar plugin com a sessão aberta: já derrubou o Hyprland).
set -e
cd "$(dirname "$0")"
g++ -shared -fPIC -std=c++26 -O2 -Wno-c++11-narrowing --no-gnu-unique \
    $(pkg-config --cflags pixman-1 libdrm hyprland libinput libudev wayland-server xkbcommon) \
    main.cpp barDeco.cpp BarPassElement.cpp -o hyprbars.so
mkdir -p ~/.local/lib/hyprland
cp hyprbars.so ~/.local/lib/hyprland/hyprbars-porapp.so.novo
mv ~/.local/lib/hyprland/hyprbars-porapp.so.novo ~/.local/lib/hyprland/hyprbars-porapp.so
echo "ok: vale no próximo login"
