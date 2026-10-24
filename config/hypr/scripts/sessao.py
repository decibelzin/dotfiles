#!/usr/bin/env python3
"""Salva e restaura os apps abertos entre um login e outro (o Hyprland não
tem "restaurar sessão").

  sessao.py vigiar     restaura a última sessão e depois, a cada 20s, anota
                       quais apps estão abertos (assim funciona até se o
                       Hyprland cair, sem precisar de logout "certinho")
  sessao.py restaurar  só abre de novo os apps da última sessão
  sessao.py salvar     só anota os apps abertos agora

Conta as janelas (inclusive as escondidas na área secreta) e os apps que
ficam só no tray (lista NO_TRAY). Terminais (kitty, GNOME Terminal) voltam
um por shell, na mesma pasta; se o Claude Code estava rodando nele, volta
na mesma conversa (claude --resume). A sessão fica em ~/.local/state/sessao-hypr.json.
"""
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time

ARQUIVO = os.path.expanduser("~/.local/state/sessao-hypr.json")
SCRIPTS = os.path.expanduser("~/.config/hypr/scripts")
INTERVALO = 20
ESPERA_INICIAL = 60  # depois de restaurar, espera os apps abrirem antes de salvar

# Janelas que não são "apps" pra reabrir (diálogos, testes, coisas do sistema)
IGNORAR = {"", "xdg-desktop-portal-gtk", "hyprland-share-picker", "polkit-kde-authentication-agent-1",
           "hyprpolkitagent", "org.kde.polkit-kde-authentication-agent-1", "wlogout",
           "pcmanfm-qt-desktop", "teste-wl", "teste_teclas", "XClock", "xclock"}

# Apps que abrem por um lançador nosso em vez do próprio comando
LANCADORES = {"Spotify": ["flatpak", "run", "com.spotify.Client"],
              "spotify": ["flatpak", "run", "com.spotify.Client"],
              # o caminho real do Discord muda a cada atualização (app-1.0.xxx)
              "discord": ["discord"]}

# Apps que continuam rodando só no tray, sem janela: nome do processo -> comando
NO_TRAY = {"Discord": ["discord"], "vesktop": ["vesktop"], "steam": ["steam"],
           "telegram-desktop": ["telegram-desktop"], "spotify": ["flatpak", "run", "com.spotify.Client"]}


def cmdline(pid):
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            return [p.decode(errors="replace") for p in f.read().split(b"\0") if p]
    except OSError:
        return []


def processos():
    """{nome do processo: pid} dos processos do usuário."""
    saida = subprocess.run(["ps", "-u", str(os.getuid()), "-o", "pid=,comm="],
                           capture_output=True, text=True).stdout
    procs = {}
    for linha in saida.splitlines():
        pid, _, nome = linha.strip().partition(" ")
        procs.setdefault(nome.strip(), int(pid))
    return procs


def kitty_com_abas(abas, n, gravar=True):
    """Uma janela do kitty com as abas (pasta, comando, ativa), via arquivo de sessão do kitty."""
    arquivo = os.path.join(os.path.dirname(ARQUIVO), f"sessao-kitty-{n}.conf")
    # Abre mostrando a aba que estava ativa (ou a primeira com o Claude);
    # senão ela fica escondida atrás das outras
    foco = next((i for i, a in enumerate(abas) if a[2]), None)
    if foco is None:
        foco = next((i for i, a in enumerate(abas) if a[1]), 0)
    if not gravar:
        return ["kitty", "--session", arquivo]
    with open(arquivo, "w") as f:
        for i, (pasta_aba, cmd, _) in enumerate(abas):
            if i:
                f.write("new_tab\n")
            f.write(f"launch --cwd={shlex.quote(pasta_aba)} {shlex.join(cmd or [])}\n")
            if i == foco:
                f.write("focus\n")
    return ["kitty", "--session", arquivo]


# Terminais: classe da janela -> como reabrir, dadas as abas que tinha
# ([(pasta, comando, ativa)]). O kitty volta com as abas; o GNOME Terminal (um
# processo só pra todas as janelas) volta uma janela por shell.
TERMINAIS = {
    "kitty": lambda abas, n, gravar: [kitty_com_abas(abas, n, gravar)],
    "org.gnome.Terminal": lambda abas, n, gravar: [
        ["gnome-terminal", f"--working-directory={p}"] + (["--"] + c if c else []) for p, c, _ in abas],
}
SHELLS = {"zsh", "bash", "sh", "fish", "dash"}


def arvore():
    """{pid: (pai, nome)} de todos os processos."""
    procs = {}
    for d in os.listdir("/proc"):
        if not d.isdigit():
            continue
        try:
            with open(f"/proc/{d}/stat") as f:
                dados = f.read()
        except OSError:
            continue
        nome = dados[dados.index("(") + 1:dados.rindex(")")]
        pai = int(dados[dados.rindex(")") + 2:].split()[1])
        procs[int(d)] = (pai, nome)
    return procs


def descendentes(pid, procs):
    filhos = [p for p, (pai, _) in procs.items() if pai == pid]
    return filhos + [n for f in filhos for n in descendentes(f, procs)]


def pasta(pid):
    try:
        return os.readlink(f"/proc/{pid}/cwd")
    except OSError:
        return os.path.expanduser("~")


class Conversas:
    """Descobre em qual conversa do Claude Code cada terminal estava.

    Dois tipos: conversas em segundo plano (sobrevivem ao logout; o Claude no
    terminal é só uma tela conectada) voltam com `claude attach <id>`; um
    Claude normal morre com o terminal e volta com `claude --resume <id>`."""

    def __init__(self):
        self._lista = None
        self.usadas = set()

    def fundo(self):
        """Conversas em segundo plano (claude agents --json)."""
        if self._lista is None:
            try:
                saida = subprocess.run([os.path.expanduser("~/.local/bin/claude"), "agents", "--json"],
                                       capture_output=True, text=True, timeout=15).stdout
                dados = json.loads(saida)
                lista = dados if isinstance(dados, list) else dados.get("sessions", [])
                self._lista = [c for c in lista if isinstance(c, dict) and "id" in c]
            except Exception:
                self._lista = []
        return self._lista

    @staticmethod
    def existe(conversa, onde):
        projeto = os.path.expanduser("~/.claude/projects/" + "".join(
            c if c.isalnum() else "-" for c in onde))
        return os.path.exists(os.path.join(projeto, conversa + ".jsonl"))

    def de(self, pid, titulo, onde):
        """("attach" | "resume", id), ou None se não der pra saber."""
        ids_fundo = {c["id"]: c for c in self.fundo()}
        args = cmdline(pid)
        # 1. O próprio comando diz (abas que já voltaram de um login)
        for i, a in enumerate(args[:-1]):
            if a in ("attach", "--resume", "-r"):
                curto = re.sub(r"^([0-9a-f]{8})-[0-9a-f-]{27}$", r"\1", args[i + 1])
                return ("attach", curto) if curto in ids_fundo else ("resume", args[i + 1])
        # 2. Claude normal: o Claude Code anota a conversa de cada processo
        try:
            with open(os.path.expanduser(f"~/.claude/sessions/{pid}.json")) as f:
                info = json.load(f)
            if info.get("kind") == "interactive" and self.existe(info["sessionId"], onde):
                return ("resume", info["sessionId"])
        except (OSError, ValueError, KeyError):
            pass
        # 3. Tela de uma conversa em segundo plano: o título da aba é o nome
        #    dela (o Claude põe um ✳/◐ na frente)
        if titulo:
            nome = re.sub(r"^\W+", "", titulo).strip()
            for c in self.fundo():
                if c.get("name") == nome and c["id"] not in self.usadas:
                    return ("attach", c["id"])
        return None


def comando_claude(conversa, shell):
    if conversa:
        tipo, ident = conversa
        retomar = f"claude attach {ident}" if tipo == "attach" else f"claude --resume {ident}"
    else:
        retomar = "claude"  # não deu pra saber qual era: abre um novo em vez de chutar
    return [shell, "-ic", f"{retomar}; exec {shell}"]


def abas_do_kitty(pid):
    """Abas de um kitty pelo controle remoto: [[(pasta, pid do claude, título, ativa, spotify)]] por janela."""
    sock = os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), f"kitty-{pid}")
    if not os.path.exists(sock):
        return None
    try:
        dados = json.loads(subprocess.run(["kitty", "@", "--to", f"unix:{sock}", "ls"],
                                          capture_output=True, text=True, timeout=5).stdout)
    except Exception:
        return None
    janelas = []
    for jan in dados:
        abas = []
        for t in jan["tabs"]:
            w = t["windows"][0]
            claude = next((f["pid"] for f in w.get("foreground_processes", [])
                           if os.path.basename((f.get("cmdline") or [""])[0]) == "claude"), None)
            spotify = any(os.path.basename((f.get("cmdline") or [""])[0]) == "spotify_player"
                          for f in w.get("foreground_processes", []))
            abas.append((w["cwd"], claude, t.get("title", ""), t.get("is_active", t.get("is_focused")), spotify))
        janelas.append(abas)
    return janelas


def abas_pela_arvore(pid, procs):
    """Sem controle remoto (GNOME Terminal, kitty antigo): uma aba por shell filho."""
    abas = []
    for sh in (p for p, (pai, nome) in procs.items() if pai == pid and nome in SHELLS):
        claude = next((d for d in descendentes(sh, procs) if procs[d][1] == "claude"), None)
        spotify = any(procs[d][1] == "spotify_player" for d in descendentes(sh, procs))
        abas.append((pasta(claude or sh), claude, None, False, spotify))
    return [abas]


def terminais_abertos(janelas, procs, gravar=True):
    """Os terminais abertos, com suas abas: {chave: comando pra reabrir}."""
    itens, vistos, conversas = {}, set(), Conversas()
    os.makedirs(os.path.dirname(ARQUIVO), exist_ok=True)
    shell = os.environ.get("SHELL", "/bin/zsh")
    for j in janelas:
        classe, pid = j.get("class"), j.get("pid", -1)
        # Um processo pode ter várias janelas (GNOME Terminal sempre; kitty às vezes)
        if classe not in TERMINAIS or pid in vistos:
            continue
        vistos.add(pid)
        grupos = (abas_do_kitty(pid) if classe == "kitty" else None) or abas_pela_arvore(pid, procs)
        for grupo in grupos:
            abas = []
            for onde, claude, titulo, ativa, spotify in grupo:
                cmd = None
                if claude:
                    conversa = conversas.de(claude, titulo, onde)
                    if conversa:
                        conversas.usadas.add(conversa[1])
                    cmd = comando_claude(conversa, shell)
                abas.append((onde, cmd, ativa))
            for cmd in TERMINAIS[classe](abas, len(itens), gravar) if abas else []:
                itens[f"terminal:{classe}:{len(itens)}"] = cmd
    return itens


def apps_abertos(gravar=True):
    """{chave: comando} dos apps abertos. Com gravar=False só olha, sem
    escrever os arquivos de sessão do kitty (usado na restauração)."""
    apps = {}
    try:
        janelas = json.loads(subprocess.run(["hyprctl", "clients", "-j"],
                                            capture_output=True, text=True).stdout)
    except Exception:
        return None
    procs = arvore()
    apps.update(terminais_abertos(janelas, procs, gravar))
    for j in janelas:
        classe = j.get("class") or j.get("initialClass") or ""
        if classe in IGNORAR or classe in TERMINAIS or classe in apps or j.get("pid", -1) <= 0:
            continue
        cmd = LANCADORES.get(classe) or cmdline(j["pid"])
        if cmd:
            apps[classe] = cmd
    for nome, pid in processos().items():
        if nome in NO_TRAY and not any(nome.lower() in c.lower() for c in apps):
            apps[nome] = NO_TRAY[nome]
    return apps


def salvar():
    apps = apps_abertos()
    if apps is None:
        return
    os.makedirs(os.path.dirname(ARQUIVO), exist_ok=True)
    with open(ARQUIVO + ".tmp", "w") as f:
        json.dump(apps, f, indent=2, ensure_ascii=False)
    os.replace(ARQUIVO + ".tmp", ARQUIVO)
    # Apaga arquivos de sessão do kitty que a sessão salva não usa mais.
    # Só aqui, ao salvar: na restauração o kitty ainda vai ler esses arquivos
    em_uso = {c[-1] for c in apps.values() if c[:2] == ["kitty", "--session"]}
    pasta_estado = os.path.dirname(ARQUIVO)
    for a in os.listdir(pasta_estado):
        caminho = os.path.join(pasta_estado, a)
        if a.startswith("sessao-kitty-") and caminho not in em_uso:
            os.remove(caminho)


def restaurar():
    try:
        with open(ARQUIVO) as f:
            apps = json.load(f)
    except (OSError, ValueError):
        return
    # Cópia do que foi salvo antes deste login (o salvador sobrescreve depois)
    anterior = os.path.join(os.path.dirname(ARQUIVO), "sessao-anterior")
    shutil.rmtree(anterior, ignore_errors=True)
    os.makedirs(anterior)
    for a in os.listdir(os.path.dirname(ARQUIVO)):
        if a.startswith("sessao-") and a != "sessao-anterior":
            shutil.copy2(os.path.join(os.path.dirname(ARQUIVO), a), anterior)
    ja_abertos = apps_abertos(gravar=False) or {}
    for classe, cmd in apps.items():
        if classe in ja_abertos:
            continue
        # Apps Electron reescrevem a linha de comando num texto só, com espaços
        if len(cmd) == 1 and " " in cmd[0] and not os.path.exists(cmd[0]):
            cmd = cmd[0].split()
        # Se o executável sumiu (ex.: Discord atualizou e mudou a pasta), tenta pelo nome
        if not (os.path.exists(cmd[0]) or shutil.which(cmd[0])):
            cmd = [shutil.which(classe.lower()) or ""]
            if not cmd[0]:
                continue
        subprocess.Popen(cmd, start_new_session=True, cwd=os.path.expanduser("~"),
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
        time.sleep(0.5)


def main():
    acao = sys.argv[1] if len(sys.argv) > 1 else "vigiar"
    if acao == "salvar":
        salvar()
    elif acao == "restaurar":
        restaurar()
    else:
        restaurar()
        time.sleep(ESPERA_INICIAL)
        while True:
            salvar()
            time.sleep(INTERVALO)


if __name__ == "__main__":
    main()
