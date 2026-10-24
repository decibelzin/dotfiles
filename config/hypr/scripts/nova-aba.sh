#!/usr/bin/env bash
# Botão "+" da barra: abre uma aba nova na janela ativa.
# Terminais usam Ctrl+Shift+T, navegadores Ctrl+T; o resto ganha um terminal novo.
sleep 0.15  # espera soltar o clique antes de mandar as teclas
classe=$(hyprctl -j activewindow | python3 -c 'import json,sys; print(json.load(sys.stdin).get("class",""))')
case "$classe" in
    org.gnome.Terminal|kitty)
        wtype -M ctrl -M shift t -m shift -m ctrl ;;
    firefox*|firefox-esr|chromium|google-chrome|brave-browser)
        wtype -M ctrl t -m ctrl ;;
    *)
        kitty & ;;
esac
