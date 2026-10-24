-- ── Nord Escuro · Hyprland (formato Lua) ───────────────
-- Convertido do hyprland.conf antigo (que continua lá como backup).
-- Lista de atalhos: Super + /

-- Cores
local bg     = "rgb(0c0f14)"
local border = "rgb(2a303b)"
local frost1 = "rgb(88c0d0)"
local frost4 = "rgb(5e81ac)"

-- Monitor: resolução nativa, posição automática, escala 1
hl.monitor({ output = "", mode = "preferred", position = "auto", scale = 1 })

-- Força a Intel (a NVIDIA/nouveau travava o login)
hl.env("AQ_DRM_DEVICES", "/dev/dri/card1")

-- Programas
local scripts  = "~/.config/hypr/scripts/"
local terminal = "kitty"
local menu     = "pkill -x rofi || rofi -show drun"
local files    = "nautilus"
local browser  = "firefox"

-- Ambiente
hl.env("XCURSOR_SIZE", "24")
hl.env("HYPRCURSOR_SIZE", "24")
hl.env("QT_QPA_PLATFORMTHEME", "qt5ct")
hl.env("GTK_THEME", "Adwaita:dark")
hl.env("MOZ_ENABLE_WAYLAND", "1")
hl.env("ELECTRON_OZONE_PLATFORM_HINT", "auto")
-- Programas do usuário (notepad, claude...) ficam em ~/.local/bin,
-- que o Hyprland não tinha no PATH: atalhos e o Super + R não achavam eles
do
    local bin = os.getenv("HOME") .. "/.local/bin"
    local path = os.getenv("PATH") or ""
    -- só adiciona uma vez (o Lua roda de novo a cada reload)
    if not (":" .. path .. ":"):find(":" .. bin .. ":", 1, true) then
        hl.env("PATH", bin .. ":" .. path)
    end
end

-- Autostart
hl.on("hyprland.start", function()
    hl.exec_cmd("hyprpaper")
    hl.exec_cmd("~/.config/hypr/scripts/resgatar-secreta.py")
    -- Antes de reabrir os apps da última sessão (scripts/sessao.py): passa os
    -- dados desta sessão (tela, Hyprland) pros serviços do sistema e encerra o
    -- servidor do GNOME Terminal que sobrou da sessão anterior; sem isso ele
    -- tentava abrir janelas na tela antiga e travava (o rofi também não abria)
    hl.exec_cmd("sh -c 'dbus-update-activation-environment --systemd WAYLAND_DISPLAY DISPLAY "
        .. "HYPRLAND_INSTANCE_SIGNATURE XDG_CURRENT_DESKTOP XDG_SESSION_TYPE XDG_DATA_DIRS; "
        .. "systemctl --user stop gnome-terminal-server; "
        .. "exec ~/.config/hypr/scripts/sessao.py vigiar'")
    -- Ícones na área de trabalho (~/Desktop), lixeira e menu do botão direito
    hl.exec_cmd("env QT_QPA_PLATFORMTHEME=qt6ct pcmanfm-qt --desktop")
    hl.exec_cmd("waybar")
    hl.exec_cmd("mako")
    hl.exec_cmd("hypridle")
    hl.exec_cmd("nm-applet --indicator")
    hl.exec_cmd("blueman-applet")
    hl.exec_cmd("/usr/libexec/hyprpolkitagent")
    hl.exec_cmd("wl-paste --type text --watch cliphist store")
    hl.exec_cmd("wl-paste --type image --watch cliphist store")
    hl.exec_cmd("gsettings set org.gnome.desktop.interface color-scheme prefer-dark")
    hl.exec_cmd("gsettings set org.gnome.desktop.interface icon-theme Papirus-Dark")
end)

hl.config({
    input = {
        kb_layout    = "br",
        kb_variant   = "abnt2",
        numlock_by_default = true,
        follow_mouse = 1,
        sensitivity  = 0,
        touchpad = {
            natural_scroll       = true,
            tap_to_click         = true,
            disable_while_typing = true,
            -- apertar os dois "botões" do touchpad juntos = clique do meio (colar)
            middle_button_emulation = true,
        },
    },

    general = {
        gaps_in     = 6,
        gaps_out    = 12,
        border_size = 0,  -- sem borda colorida nas janelas
        col = {
            active_border   = { colors = { frost1, frost4 }, angle = 45 },
            inactive_border = border,
        },
        layout           = "dwindle",
        resize_on_border = true,
    },

    decoration = {
        rounding         = 12,
        active_opacity   = 1.0,
        inactive_opacity = 0.75,  -- janela sem foco fica translúcida (vidro)
        -- Vidro fosco: desfoque forte + um pouco de granulado (noise)
        -- e vibrance pras cores de trás aparecerem
        blur = {
            enabled           = true,
            size              = 10,
            passes            = 3,
            new_optimizations = true,
            noise             = 0.035,
            contrast          = 1.0,
            brightness        = 0.9,
            vibrancy          = 0.25,
            vibrancy_darkness = 0.2,
            popups            = true,
        },
        shadow = {
            enabled      = true,
            range        = 20,
            render_power = 3,
            color        = "rgba(00000099)",
        },
    },

    animations = { enabled = true },

    dwindle = { preserve_split = true },

    misc = {
        disable_hyprland_logo    = true,
        disable_splash_rendering = true,
        background_color         = bg,
        mouse_move_enables_dpms  = true,
        key_press_enables_dpms   = true,
    },
})

-- Gestos no touchpad: 3 dedos pro lado troca de área de trabalho
hl.gesture({ fingers = 3, direction = "horizontal", action = "workspace" })

-- Animações
hl.curve("suave",  { type = "bezier", points = { {0.05, 0.9}, {0.1, 1.05} } })
hl.curve("linear", { type = "bezier", points = { {0, 0}, {1, 1} } })
hl.animation({ leaf = "windows",     enabled = true, speed = 6,  bezier = "suave",   style = "slide" })
hl.animation({ leaf = "windowsOut",  enabled = true, speed = 6,  bezier = "default", style = "popin 80%" })
hl.animation({ leaf = "border",      enabled = true, speed = 10, bezier = "default" })
hl.animation({ leaf = "borderangle", enabled = true, speed = 60, bezier = "linear",  style = "loop" })
hl.animation({ leaf = "fade",        enabled = true, speed = 6,  bezier = "default" })
hl.animation({ leaf = "workspaces",  enabled = true, speed = 5,  bezier = "suave",   style = "slidevert" })
-- Menus (rofi, notificações, wlogout): fade rápido, sem demora pra aparecer
hl.animation({ leaf = "layers",      enabled = true, speed = 2,  bezier = "default", style = "fade" })
hl.animation({ leaf = "fadeLayers",  enabled = true, speed = 1.5, bezier = "default" })

-- ── Regras de janela ───────────────────────────────────
-- Janelinhas de configuração abrem soltas e no meio da tela
for _, class in ipairs({
    "org.pulseaudio.pavucontrol", "pavucontrol", "blueman-manager",
    "nm-connection-editor", "nwg-look", "qt5ct", "qt6ct", "swappy",
    "org.gnome.Calculator", "xdg-desktop-portal-gtk",
}) do
    hl.window_rule({ match = { class = "^(" .. class .. ")$" }, float = true, center = true })
end
-- Janelas de "Abrir arquivo" / "Salvar"
hl.window_rule({
    match  = { title = "^(Open File|Save File|Save As|Abrir arquivo|Salvar arquivo|Salvar como).*" },
    float  = true,
    center = true,
})
-- Vídeo "picture-in-picture" do navegador: solto e fixo em todas as áreas
hl.window_rule({ match = { title = "^(Picture-in-Picture|Imagem sobre imagem)$" }, float = true, pin = true })

-- Desfoque (blur) atrás da barra, do menu, das notificações e do menu de desligar
for _, ns in ipairs({ "waybar", "rofi", "notifications", "logout_dialog", "volume-app" }) do
    hl.layer_rule({ match = { namespace = ns }, blur = true, ignore_alpha = 0.1 })
end

-- ── Barra de título (plugin hyprbars) ──────────────────
-- Botões no canto superior direito: minimizar, maximizar, fechar.
-- "Minimizar" manda a janela pra área secreta: Super + S mostra ela de novo.
-- hyprbars com patch nosso (~/.local/src/hyprland-plugins/hyprbars): botão com
-- "classes" só aparece nesses apps, e {addr} no comando vira o endereço da janela.
-- Recompilar se o Hyprland atualizar (compilar-porapp.sh lá na pasta).
hl.plugin.load("/home/aux/.local/lib/hyprland/hyprbars-porapp.so")
-- O Hyprland ignora o botão minimizar dos próprios apps (ex.: o — do Discord).
-- Este plugin nosso avisa "minimized" e o resgatar-secreta.py esconde a janela.
-- Fonte em ~/.local/src/hypr-minimizar (rodar compilar.sh se o Hyprland atualizar)
hl.plugin.load(os.getenv("HOME") .. "/.local/lib/hyprland/minimizar.so")

if hl.plugin.hyprbars then
    hl.config({
        plugin = {
            hyprbars = {
                bar_height            = 28,
                -- Vidro: cor escura bem transparente + desfoque do que está atrás
                bar_color             = "rgba(0c0f1459)",
                bar_blur              = true,
                ["col.text"]          = "rgb(d8dee9)",
                bar_text_font         = "JetBrainsMono Nerd Font",
                bar_text_size         = 10,
                bar_part_of_window    = true,
                bar_precedence_over_border = true,
                bar_padding           = 10,
                bar_button_padding    = 8,
                icon_on_hover         = true,
                on_double_click       = [[hyprctl dispatch 'hl.dsp.window.fullscreen({ mode = "maximized" })']],
            },
        },
    })

    -- O GNOME Terminal usa esta barra também (a dele tá desligada, porque o
    -- Hyprland ignora o minimizar dela); o botão + abre aba nova (scripts/nova-aba.sh)

    -- Apps que já desenham a própria barra com minimizar/maximizar/fechar:
    -- sem a nossa barra, pra não ficar duas
    hl.window_rule({ match = { class = "^(discord|vesktop|Spotify)$" }, ["hyprbars:no_bar"] = true })

    -- A ordem é da direita pra esquerda: o primeiro fica no canto
    local botoes = {
        { cor = "rgb(bf616a)", icone = "󰖭", acao = [[hl.dsp.window.close()]] },
        { cor = "rgb(a3be8c)", icone = "󰖯", acao = [[hl.dsp.window.fullscreen({ mode = "maximized" })]] },
        { cor = "rgb(ebcb8b)", icone = "󰖰", acao = [[hl.dsp.window.move({ workspace = "special:secreta", follow = false })]] },
        { cor = "rgb(88c0d0)", icone = "󰐕", acao = [[hl.dsp.exec_cmd("~/.config/hypr/scripts/nova-aba.sh")]],
          classes = "^(kitty|org\\.gnome\\.Terminal)$" },  -- + só nos terminais
        -- engrenagem: popup com o volume só desse app (scripts/volume-app.py)
        { cor = "rgb(81a1c1)", icone = "󰒓", cmd = "~/.config/hypr/scripts/volume-app.py {addr}" },
    }
    for _, b in ipairs(botoes) do
        hl.plugin.hyprbars.add_button({
            bg_color = b.cor,
            fg_color = bg,
            size     = 14,
            icon     = b.icone,
            action   = b.cmd or ("hyprctl dispatch '" .. b.acao .. "'"),
            classes  = b.classes,
        })
    end
end

-- ── Atalhos (SUPER = tecla Windows) ────────────────────
local mod = "SUPER"

-- Apertar e soltar o SUPER sozinho abre/fecha o menu de apps
hl.bind(mod .. " + SUPER_L", hl.dsp.exec_cmd(menu), { release = true })

-- Apps
hl.bind(mod .. " + Return", hl.dsp.exec_cmd(terminal))
hl.bind(mod .. " + D",      hl.dsp.exec_cmd(scripts .. "mostrar-desktop.py"))  -- igual Win+D
hl.bind(mod .. " + E",      hl.dsp.exec_cmd(files))
hl.bind(mod .. " + B",      hl.dsp.exec_cmd(browser))
-- Igual ao Win+R do Windows: digita um comando e executa
hl.bind(mod .. " + R",      hl.dsp.exec_cmd("pkill -x rofi || rofi -show run"))

-- Janelas
hl.bind(mod .. " + Q", hl.dsp.window.close())
hl.bind("ALT + F4",   hl.dsp.window.close())  -- igual ao Windows
hl.bind(mod .. " + F", hl.dsp.window.fullscreen())
hl.bind(mod .. " + M", hl.dsp.window.fullscreen({ mode = "maximized" }))
hl.bind(mod .. " + T", hl.dsp.window.float({ action = "toggle" }))
hl.bind(mod .. " + C", hl.dsp.window.center())
hl.bind(mod .. " + P", hl.dsp.window.pseudo())
hl.bind(mod .. " + J", hl.dsp.layout("togglesplit"))
-- Alt+Tab passa por todas as janelas, até as minimizadas (scripts/alt-tab.py)
hl.bind("ALT + Tab",         hl.dsp.exec_cmd(scripts .. "alt-tab.py"))
hl.bind("ALT + SHIFT + Tab", hl.dsp.exec_cmd(scripts .. "alt-tab.py --prev"))

-- Ferramentas
hl.bind(mod .. " + V",           hl.dsp.exec_cmd(scripts .. "area-transferencia.sh"))
hl.bind(mod .. " + period",      hl.dsp.exec_cmd("rofimoji --selector rofi"))
hl.bind(mod .. " + SHIFT + C",   hl.dsp.exec_cmd("hyprpicker -a"))
hl.bind(mod .. " + N",           hl.dsp.exec_cmd(scripts .. "luz-noturna.sh"))
hl.bind(mod .. " + slash",       hl.dsp.exec_cmd(scripts .. "atalhos.sh"))

-- Sessão
hl.bind(mod .. " + L",         hl.dsp.exec_cmd("loginctl lock-session"))
hl.bind(mod .. " + Escape",    hl.dsp.exec_cmd("pkill wlogout || wlogout -b 5"))
hl.bind(mod .. " + SHIFT + E", hl.dsp.exit())

-- Print da tela (salva em ~/Pictures/Screenshots e copia)
hl.bind("Print",               hl.dsp.exec_cmd(scripts .. "print.sh area"))
hl.bind("SHIFT + Print",       hl.dsp.exec_cmd(scripts .. "print.sh tela"))
hl.bind(mod .. " + SHIFT + S", hl.dsp.exec_cmd(scripts .. "print.sh editar"))

-- Mover o foco / mover janelas
for _, dir in ipairs({ "left", "right", "up", "down" }) do
    hl.bind(mod .. " + " .. dir,           hl.dsp.focus({ direction = dir }))
    hl.bind(mod .. " + SHIFT + " .. dir,   hl.dsp.window.move({ direction = dir }))
end

-- Áreas de trabalho
for i = 1, 6 do
    hl.bind(mod .. " + " .. i,           hl.dsp.focus({ workspace = i }))
    hl.bind(mod .. " + SHIFT + " .. i,   hl.dsp.window.move({ workspace = i }))
end
hl.bind(mod .. " + Tab",        hl.dsp.focus({ workspace = "previous" }))
hl.bind(mod .. " + mouse_down", hl.dsp.focus({ workspace = "e+1" }))
hl.bind(mod .. " + mouse_up",   hl.dsp.focus({ workspace = "e-1" }))

-- Área secreta: some/aparece por cima de tudo
hl.bind(mod .. " + S",       hl.dsp.workspace.toggle_special("secreta"))
hl.bind(mod .. " + ALT + S", hl.dsp.window.move({ workspace = "special:secreta" }))

-- Mover/redimensionar com o mouse
hl.bind(mod .. " + mouse:272", hl.dsp.window.drag(),   { mouse = true })
hl.bind(mod .. " + mouse:273", hl.dsp.window.resize(), { mouse = true })

-- Teclas de mídia, volume e brilho
local lr = { locked = true, repeating = true }
hl.bind("XF86AudioRaiseVolume",  hl.dsp.exec_cmd("wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+"), lr)
hl.bind("XF86AudioLowerVolume",  hl.dsp.exec_cmd("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-"), lr)
hl.bind("XF86AudioMute",         hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"), lr)
hl.bind("XF86AudioMicMute",      hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle"), lr)
hl.bind("XF86MonBrightnessUp",   hl.dsp.exec_cmd("brightnessctl s 5%+"), lr)
hl.bind("XF86MonBrightnessDown", hl.dsp.exec_cmd("brightnessctl s 5%-"), lr)
hl.bind("XF86AudioPlay",  hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPause", hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioNext",  hl.dsp.exec_cmd("playerctl next"),       { locked = true })
hl.bind("XF86AudioPrev",  hl.dsp.exec_cmd("playerctl previous"),   { locked = true })
