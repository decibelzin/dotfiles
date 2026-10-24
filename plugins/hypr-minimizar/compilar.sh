#!/bin/sh
# Recompila e instala o plugin. Precisa rodar de novo sempre que o Hyprland
# for atualizado (o plugin só funciona com a versão em que foi compilado).
set -e
cd "$(dirname "$0")"
g++ -shared -fPIC -std=c++26 -O2 $(pkg-config --cflags hyprland pixman-1 libdrm) main.cpp -o minimizar.so
mkdir -p ~/.local/lib/hyprland
cp minimizar.so ~/.local/lib/hyprland/minimizar.so
echo "ok: plugin instalado; recarregue com Super+Shift+R ou saia e entre no Hyprland"
