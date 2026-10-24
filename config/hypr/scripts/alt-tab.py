#!/usr/bin/env python3
# Alt+Tab que passa por todas as janelas, de todos os workspaces, incluindo
# as minimizadas (área secreta). Uma janela minimizada volta pro workspace
# atual; uma de outro workspace leva você até ela.
import json
import subprocess
import sys

SECRETA = "special:secreta"
voltar = "--prev" in sys.argv


def hyprctl_json(*args):
    out = subprocess.run(["hyprctl", "-j", *args], capture_output=True, text=True).stdout
    return json.loads(out or "null")


def dispatch(lua):
    subprocess.run(["hyprctl", "dispatch", lua], capture_output=True)


janelas = [c for c in hyprctl_json("clients") if c["mapped"]]
if not janelas:
    sys.exit()

# Ordem fixa: workspaces normais em ordem, minimizadas por último
janelas.sort(key=lambda c: (c["workspace"]["name"] == SECRETA,
                            c["workspace"]["id"], c["at"][0], c["at"][1]))
ativa = (hyprctl_json("activewindow") or {}).get("address")
enderecos = [c["address"] for c in janelas]
i = enderecos.index(ativa) if ativa in enderecos else -1
alvo = janelas[(i + (-1 if voltar else 1)) % len(janelas)]
endereco = f'address:{alvo["address"]}'

if alvo["workspace"]["name"] == SECRETA:
    ws = hyprctl_json("activeworkspace")["id"]
    dispatch(f'hl.dsp.window.move({{ workspace = "{ws}", window = "{endereco}" }})')
dispatch(f'hl.dsp.focus({{ window = "{endereco}" }})')
