#!/usr/bin/env bash
# Liga/desliga a luz noturna (tela mais amarelada, cansa menos a vista)
if pkill -x hyprsunset; then
    notify-send "Luz noturna" "Desligada"
else
    hyprsunset -t 4500 >/dev/null 2>&1 &
    notify-send "Luz noturna" "Ligada"
fi
