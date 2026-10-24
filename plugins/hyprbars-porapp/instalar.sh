#!/bin/sh
# Baixa o hyprbars oficial, aplica o patch "botão por app" e instala em
# ~/.local/lib/hyprland/hyprbars-porapp.so. Precisa do pacote hyprland-dev.
# Se o Hyprland for de outra versão, troque a TAG (e o patch pode precisar de ajuste).
set -e
TAG=${TAG:-v0.56.0}
AQUI=$(cd "$(dirname "$0")" && pwd)
mkdir -p ~/.local/src
cd ~/.local/src
[ -d hyprland-plugins ] || git clone --depth 1 --branch "$TAG" https://github.com/hyprwm/hyprland-plugins
cd hyprland-plugins
git apply "$AQUI/hyprbars-porapp-v0.56.0.patch"
cp "$AQUI/compilar-porapp.sh" hyprbars/
sh hyprbars/compilar-porapp.sh
