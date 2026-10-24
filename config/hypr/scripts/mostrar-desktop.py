#!/usr/bin/env python3
# Igual ao Win + D: esconde todas as janelas do workspace atual na área
# secreta pra mostrar a área de trabalho. Apertar de novo traz elas de volta.
import json
import os
import subprocess

SECRETA = "special:secreta"
ESTADO = os.path.join(os.environ["XDG_RUNTIME_DIR"], "mostrar-desktop.json")


def hyprctl_json(*args):
    out = subprocess.run(["hyprctl", "-j", *args], capture_output=True, text=True).stdout
    return json.loads(out)


def mover(addr, ws):
    subprocess.run(["hyprctl", "dispatch",
                    f'hl.dsp.window.move({{ workspace = "{ws}", window = "address:{addr}", follow = false }})'],
                   capture_output=True)


ws = hyprctl_json("activeworkspace")["id"]
clientes = hyprctl_json("clients")
visiveis = [c["address"] for c in clientes if c["workspace"]["id"] == ws and c["mapped"]]

try:
    with open(ESTADO) as f:
        escondidas = json.load(f)
except (OSError, ValueError):
    escondidas = {}

if visiveis:
    escondidas[str(ws)] = visiveis
    for addr in visiveis:
        mover(addr, SECRETA)
else:
    # Só traz de volta as que ainda estão na área secreta
    na_secreta = {c["address"] for c in clientes if c["workspace"]["name"] == SECRETA}
    for addr in escondidas.pop(str(ws), []):
        if addr in na_secreta:
            mover(addr, ws)

with open(ESTADO, "w") as f:
    json.dump(escondidas, f)
