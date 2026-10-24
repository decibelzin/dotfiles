#!/usr/bin/env bash
# Print da tela: salva em ~/Pictures/Screenshots e copia pra área de transferência
# uso: print.sh area | tela | editar
dir=~/Pictures/Screenshots
arq="$dir/print_$(date +%Y-%m-%d_%H-%M-%S).png"
mkdir -p "$dir"
case "$1" in
    tela)   grim "$arq" ;;
    editar) area=$(slurp) || exit 0; grim -g "$area" - | swappy -f - ; exit 0 ;;
    *)      area=$(slurp) || exit 0; grim -g "$area" "$arq" ;;
esac
wl-copy < "$arq"
notify-send -i "$arq" "Print salvo" "Copiado pra área de transferência"
