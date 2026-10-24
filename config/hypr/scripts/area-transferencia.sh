#!/usr/bin/env bash
# Histórico do copiar/colar: escolhe um item e ele volta pra área de transferência
cliphist list | rofi -dmenu -p "copiados" | cliphist decode | wl-copy
