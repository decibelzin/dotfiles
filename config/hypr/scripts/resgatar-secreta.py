#!/usr/bin/env python3
# Quando um app escondido na área secreta pede pra aparecer (ex.: "Show app"
# no tray), o Hyprland só marca a janela como "urgent". Este script escuta
# esse evento e traz a janela pro workspace atual, com foco.
# Também faz o botão "minimizar" do próprio app (ex.: GNOME Terminal) funcionar:
# o Hyprland ignora o pedido e só avisa "minimized>>ADDR,1", aí a gente esconde.
import json
import os
import socket
import subprocess
import time

SECRETA = "special:secreta"
base = os.path.join(os.environ["XDG_RUNTIME_DIR"], "hypr",
                    os.environ["HYPRLAND_INSTANCE_SIGNATURE"])


def hyprctl_json(*args):
    out = subprocess.run(["hyprctl", "-j", *args], capture_output=True, text=True).stdout
    return json.loads(out)


def resgatar(addr):
    addr = "0x" + addr
    janela = next((c for c in hyprctl_json("clients") if c["address"] == addr), None)
    if not janela or janela["workspace"]["name"] != SECRETA:
        return
    ws = hyprctl_json("activeworkspace")["id"]
    alvo = f"address:{addr}"
    subprocess.run(["hyprctl", "dispatch",
                    f'hl.dsp.window.move({{ workspace = "{ws}", window = "{alvo}" }})'],
                   capture_output=True)
    subprocess.run(["hyprctl", "dispatch", f'hl.dsp.focus({{ window = "{alvo}" }})'],
                   capture_output=True)


def minimizar(addr):
    alvo = f"address:0x{addr}"
    subprocess.run(["hyprctl", "dispatch",
                    f'hl.dsp.window.move({{ workspace = "{SECRETA}", window = "{alvo}", follow = false }})'],
                   capture_output=True)


while True:
    try:
        with socket.socket(socket.AF_UNIX) as s:
            s.connect(os.path.join(base, ".socket2.sock"))
            for linha in s.makefile():
                if linha.startswith("urgent>>"):
                    resgatar(linha.strip().split(">>", 1)[1])
                elif linha.startswith("minimized>>"):
                    addr, estado = linha.strip().split(">>", 1)[1].split(",")
                    if estado == "1":
                        minimizar(addr)
    except OSError:
        pass
    time.sleep(2)
