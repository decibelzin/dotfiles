#!/usr/bin/env python3
# Botão de volume da barra (hyprbars): abre um popupzinho de vidro colado no
# botão com o volume só daquele app. Abre pra baixo se a barra tá na parte de
# cima da tela, e pra cima se tá embaixo. Fecha com Esc, clicando fora ou
# clicando no botão de novo. A janela é uma camada transparente na tela toda
# (só o quadradinho aparece): assim dá pra saber quando clicaram fora.
#
# Uso: volume-app.py <endereço da janela>   (o hyprbars troca {addr} por ele)
import json
import os
import signal
import subprocess
import sys

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import GLib, Gtk, Gdk, GtkLayerShell  # noqa: E402

LARGURA = 260
ALTURA = 92
BARRA = 28        # bar_height do hyprbars
ESPACO = 6        # distância entre a barra e o popup
TRAVA = os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "volume-app.pid")

CSS = b"""
window { background: transparent; }
.caixa {
    background: rgba(12, 15, 20, 0.55);
    border: 1px solid rgba(216, 222, 233, 0.14);
    border-radius: 14px;
    padding: 12px 14px;
}
.nome { color: #eceff4; font-family: "JetBrainsMono Nerd Font"; font-size: 10pt; font-weight: bold; }
.valor { color: #88c0d0; font-family: "JetBrainsMono Nerd Font"; font-size: 10pt; }
.aviso { color: rgba(216, 222, 233, 0.6); font-family: "JetBrainsMono Nerd Font"; font-size: 9pt; }
.mudo { background: transparent; border: none; box-shadow: none; color: #88c0d0;
        font-family: "JetBrainsMono Nerd Font"; font-size: 13pt; padding: 0 4px; min-height: 0; }
.mudo:hover { color: #eceff4; }
scale trough { background: rgba(216, 222, 233, 0.12); border: none; border-radius: 4px; min-height: 6px; }
scale highlight { background: #88c0d0; border: none; border-radius: 4px; }
scale slider { background: #eceff4; border: none; box-shadow: none; min-width: 14px; min-height: 14px; border-radius: 7px; margin: -5px; }
"""


def hyprctl(*args):
    return json.loads(subprocess.run(["hyprctl", "-j", *args], capture_output=True, text=True).stdout)


def descendentes(pid):
    """pid + todos os filhos/netos (navegadores tocam som num processo filho)."""
    filhos = {}
    for p in os.listdir("/proc"):
        if not p.isdigit():
            continue
        try:
            with open(f"/proc/{p}/stat") as f:
                ppid = int(f.read().rsplit(")", 1)[1].split()[1])
            filhos.setdefault(ppid, []).append(int(p))
        except (OSError, IndexError, ValueError):
            pass
    todos, fila = set(), [pid]
    while fila:
        atual = fila.pop()
        if atual not in todos:
            todos.add(atual)
            fila += filhos.get(atual, [])
    return todos


def nomes_do_app(classe):
    # "org.gnome.Terminal" → {"org.gnome.terminal", "terminal"}; "firefox-esr" → {..., "firefox"}
    c = classe.lower()
    return {c, c.split(".")[-1], c.split("-")[0]} - {""}


def streams_do_app(janela):
    try:
        saida = subprocess.run(["pactl", "-f", "json", "list", "sink-inputs"], capture_output=True, text=True).stdout
        streams = json.loads(saida or "[]")
    except json.JSONDecodeError:
        return []
    pids = descendentes(janela["pid"])
    nomes = nomes_do_app(janela["class"])
    achados = []
    for s in streams:
        p = s.get("properties", {})
        pid = p.get("application.process.id")
        nome = {p.get(k, "").lower() for k in ("application.name", "application.process.binary",
                                                 "pipewire.access.portal.app_id")} - {""}
        if (pid and pid.isdigit() and int(pid) in pids) or (nome & nomes) or \
           any(n.split(".")[-1] in nomes for n in nome):
            achados.append(s)
    return achados


def volume_de(s):
    canais = s.get("volume", {}).values()
    vals = [int(c["value_percent"].rstrip("%")) for c in canais if "value_percent" in c]
    return round(sum(vals) / len(vals)) if vals else 100


class Popup(Gtk.Window):
    def __init__(self, janela):
        super().__init__()
        self.janela = janela
        self.mexendo = False

        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_namespace(self, "volume-app")
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.EXCLUSIVE)
        self.posicionar()
        visual = self.get_screen().get_rgba_visual()
        if visual:
            self.set_visual(visual)
        self.set_app_paintable(True)

        prov = Gtk.CssProvider()
        prov.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov,
                                                 Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        caixa = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        caixa.get_style_context().add_class("caixa")
        caixa.set_size_request(LARGURA, -1)

        topo = Gtk.Box(spacing=8)
        nome = Gtk.Label(label=janela["class"].split(".")[-1].capitalize(), xalign=0)
        nome.set_ellipsize(3)
        nome.get_style_context().add_class("nome")
        self.valor = Gtk.Label(label="")
        self.valor.get_style_context().add_class("valor")
        topo.pack_start(nome, True, True, 0)
        topo.pack_end(self.valor, False, False, 0)

        linha = Gtk.Box(spacing=6)
        self.mudo = Gtk.Button(label="󰕾")
        self.mudo.get_style_context().add_class("mudo")
        self.mudo.connect("clicked", self.alternar_mudo)
        self.barra = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.barra.set_draw_value(False)
        self.barra.connect("value-changed", self.mudou)
        self.barra.connect("button-press-event", lambda *_: setattr(self, "mexendo", True))
        self.barra.connect("button-release-event", lambda *_: setattr(self, "mexendo", False))
        linha.pack_start(self.mudo, False, False, 0)
        linha.pack_start(self.barra, True, True, 0)

        self.aviso = Gtk.Label(label="esse app não tá tocando som agora", xalign=0)
        self.aviso.get_style_context().add_class("aviso")

        caixa.pack_start(topo, False, False, 0)
        caixa.pack_start(linha, False, False, 0)
        caixa.pack_start(self.aviso, False, False, 0)
        self.caixa = caixa
        fundo = Gtk.Fixed()
        fundo.put(caixa, self.x, self.y)
        self.add(fundo)

        self.connect("key-press-event", self.tecla)
        self.connect("button-press-event", self.clique)
        self.show_all()
        self.atualizar()
        GLib.timeout_add(700, self.atualizar)

    def posicionar(self):
        w = self.janela
        mon = next(m for m in hyprctl("monitors") if m["id"] == w["monitor"])
        escala = mon["scale"] or 1
        larg_mon, alt_mon = mon["width"] / escala, mon["height"] / escala
        # o cursor tá em cima do botão que foi clicado
        cur = hyprctl("cursorpos")
        x = cur["x"] - mon["x"] - LARGURA / 2
        x = max(8, min(x, larg_mon - LARGURA - 8))
        topo_barra = w["at"][1] - mon["y"] - BARRA  # barra fica acima da área do app
        if w["at"][1] - mon["y"] < 0 or topo_barra + BARRA / 2 > alt_mon / 2:
            y = topo_barra - ESPACO - ALTURA          # barra na metade de baixo → abre pra cima
        else:
            y = topo_barra + BARRA + ESPACO           # barra em cima → abre pra baixo
        y = max(8, min(y, alt_mon - ALTURA - 8))
        GtkLayerShell.set_monitor(self, Gdk.Display.get_default().get_monitor(w["monitor"])
                                  or Gdk.Display.get_default().get_monitor(0))
        for borda in (GtkLayerShell.Edge.TOP, GtkLayerShell.Edge.BOTTOM,
                      GtkLayerShell.Edge.LEFT, GtkLayerShell.Edge.RIGHT):
            GtkLayerShell.set_anchor(self, borda, True)
        GtkLayerShell.set_exclusive_zone(self, -1)  # cobre a waybar também
        self.x, self.y = int(x), int(y)

    def atualizar(self):
        self.streams = streams_do_app(self.janela)
        tem = bool(self.streams)
        self.barra.set_sensitive(tem)
        self.mudo.set_sensitive(tem)
        self.aviso.set_visible(not tem)
        if tem and not self.mexendo:
            vol = volume_de(self.streams[0])
            mudo = all(s.get("mute") for s in self.streams)
            self.trocando = True
            self.barra.set_value(min(vol, 100))
            self.trocando = False
            self.mostrar(vol, mudo)
        elif not tem:
            self.valor.set_text("")
        return True

    def mostrar(self, vol, mudo):
        self.valor.set_text("mudo" if mudo else f"{vol}%")
        self.mudo.set_label("󰝟" if mudo else ("󰕿" if vol < 34 else "󰖀" if vol < 67 else "󰕾"))

    def mudou(self, barra):
        if getattr(self, "trocando", False):
            return
        vol = int(barra.get_value())
        for s in self.streams:
            subprocess.Popen(["pactl", "set-sink-input-volume", str(s["index"]), f"{vol}%"])
            if s.get("mute"):
                subprocess.Popen(["pactl", "set-sink-input-mute", str(s["index"]), "0"])
                s["mute"] = False
        self.mostrar(vol, False)

    def alternar_mudo(self, _):
        mudo = not all(s.get("mute") for s in self.streams)
        for s in self.streams:
            subprocess.Popen(["pactl", "set-sink-input-mute", str(s["index"]), "1" if mudo else "0"])
            s["mute"] = mudo
        self.mostrar(int(self.barra.get_value()), mudo)

    def clique(self, _, ev):
        # clique que chegou até a janela: se foi fora do quadradinho, fecha
        a = self.caixa.get_allocation()
        if not (a.x <= ev.x <= a.x + a.width and a.y <= ev.y <= a.y + a.height):
            self.fechar()
        return False

    def tecla(self, _, ev):
        if ev.keyval == Gdk.KEY_Escape:
            self.fechar()
        return False

    def fechar(self):
        try:
            os.remove(TRAVA)
        except OSError:
            pass
        Gtk.main_quit()


def main():
    # clicou no botão com o popup já aberto → só fecha
    try:
        with open(TRAVA) as f:
            os.kill(int(f.read()), signal.SIGTERM)
        os.remove(TRAVA)
        return
    except (OSError, ValueError):
        pass

    endereco = sys.argv[1] if len(sys.argv) > 1 else hyprctl("activewindow").get("address")
    janela = next((c for c in hyprctl("clients") if c["address"] == endereco), None)
    if not janela:
        return
    with open(TRAVA, "w") as f:
        f.write(str(os.getpid()))
    signal.signal(signal.SIGTERM, lambda *_: Gtk.main_quit())
    Popup(janela)
    Gtk.main()
    try:
        os.remove(TRAVA)
    except OSError:
        pass


if __name__ == "__main__":
    main()
