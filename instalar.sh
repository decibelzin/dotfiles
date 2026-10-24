#!/bin/sh
# Copia as configs deste repositório pro sistema. O que já existir é
# guardado antes como arquivo.bak-dotfiles.
set -e
cd "$(dirname "$0")"

copiar() {  # copiar <origem> <destino>
    mkdir -p "$(dirname "$2")"
    if [ -e "$2" ] && [ ! -e "$2.bak-dotfiles" ]; then cp -a "$2" "$2.bak-dotfiles"; fi
    cp -a "$1" "$2"
}

for item in config/*; do
    nome=$(basename "$item")
    if [ -d "$item" ]; then
        find "$item" -type f | while read -r f; do copiar "$f" "$HOME/.config/${f#config/}"; done
    else
        copiar "$item" "$HOME/.config/$nome"
    fi
done
for f in local/share/applications/*; do copiar "$f" "$HOME/.local/share/applications/$(basename "$f")"; done
for f in wallpapers/*; do copiar "$f" "$HOME/Pictures/wallpapers/$(basename "$f")"; done
copiar zshrc "$HOME/.zshrc"

perfil=$(ls -d "$HOME"/.mozilla/firefox/*.default* 2>/dev/null | head -1)
if [ -n "$perfil" ]; then
    copiar firefox/user.js "$perfil/user.js"
    copiar firefox/chrome/userChrome.css "$perfil/chrome/userChrome.css"
fi

echo "Configs copiadas. Faltam (veja o README):"
echo "  - pacotes do apt"
echo "  - plugins: plugins/hyprbars-porapp/instalar.sh e plugins/hypr-minimizar/compilar.sh"
echo "  - Fn Lock: sudo cp sistema/fn-lock.conf /etc/tmpfiles.d/"
