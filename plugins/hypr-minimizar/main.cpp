// hypr-minimizar: faz o botão "minimizar" dos próprios apps (o — da barra do
// Discord, GNOME Terminal etc.) funcionar no Hyprland.
// 1. O Hyprland diz aos apps Wayland que não sabe minimizar (wm_capabilities
//    sem MINIMIZE), então eles nem mandam o pedido: o plugin anuncia que sabe.
// 2. Quando o pedido chega, o Hyprland ignora e nem avisa ninguém: o plugin
//    manda o evento "minimized>>ENDEREÇO,1" no socket de eventos, e o
//    ~/.config/hypr/scripts/resgatar-secreta.py esconde a janela na área
//    secreta (Super + S mostra de novo).
#define WLR_USE_UNSTABLE

#include <format>
#include <unordered_map>

#include <src/Compositor.hpp>
#include <src/desktop/state/ViewState.hpp>
#include <src/desktop/view/Window.hpp>
#include <src/event/EventBus.hpp>
#include <src/managers/EventManager.hpp>
#include <src/managers/eventLoop/EventLoopManager.hpp>
#include <src/plugins/PluginAPI.hpp>
#include <src/protocols/XDGShell.hpp>
#include <src/xwayland/XSurface.hpp>

inline HANDLE PHANDLE = nullptr;

// O "transmissor" Wayland da janela (m_resource) é privado no Hyprland; este é
// o jeito padrão (e legal) em C++ de acessar um membro privado de fora
template <typename Tag, typename Tag::type M>
struct SAcesso {
    friend typename Tag::type membro(Tag) {
        return M;
    }
};
struct SResourceTag {
    using type = SP<CXdgToplevel> CXDGToplevelResource::*;
    friend type membro(SResourceTag);
};
template struct SAcesso<SResourceTag, &CXDGToplevelResource::m_resource>;

static void anunciarMinimizar(const SP<CXDGToplevelResource>& top) {
    const auto& res = top.get()->*membro(SResourceTag{});
    if (!res)
        return;
    wl_array caps;
    wl_array_init(&caps);
    for (uint32_t c : {XDG_TOPLEVEL_WM_CAPABILITIES_MAXIMIZE, XDG_TOPLEVEL_WM_CAPABILITIES_FULLSCREEN, XDG_TOPLEVEL_WM_CAPABILITIES_MINIMIZE})
        *(uint32_t*)wl_array_add(&caps, sizeof(uint32_t)) = c;
    res->sendWmCapabilities(&caps);
    wl_array_release(&caps);
}

static CHyprSignalListener                                   g_aoCriar;
static CHyprSignalListener                                   g_aoAbrir;
static CHyprSignalListener                                   g_aoDestruir;
static std::unordered_map<Desktop::View::CWindow*, CHyprSignalListener> g_ouvintes;

static void avisarMinimizar(PHLWINDOWREF janela) {
    // Fora do meio do sinal, pra não mexer na janela enquanto o Hyprland
    // ainda está tratando o pedido
    g_pEventLoopManager->doLater([janela] {
        if (const auto w = janela.lock(); w && w->m_isMapped)
            g_pEventManager->postEvent(SHyprIPCEvent{"minimized", std::format("{:x},1", (uintptr_t)w.get())});
    });
}

static void ouvir(PHLWINDOW w) {
    if (!w || g_ouvintes.contains(w.get()))
        return;
    PHLWINDOWREF ref = w;
    if (const auto top = w->m_xdgSurface ? w->m_xdgSurface->m_toplevel.lock() : nullptr) {
        anunciarMinimizar(top);
        WP<CXDGToplevelResource> fraco = top;
        g_ouvintes[w.get()] = top->m_events.stateChanged.listen([fraco, ref] {
            if (const auto t = fraco.lock(); t && t->m_state.requestsMinimize.value_or(false))
                avisarMinimizar(ref);
        });
    } else if (const auto x = w->m_xwaylandSurface.lock()) {
        WP<CXWaylandSurface> fraco = x;
        g_ouvintes[w.get()] = x->m_events.stateChanged.listen([fraco, ref] {
            if (const auto s = fraco.lock(); s && s->m_state.requestsMinimize.value_or(false))
                avisarMinimizar(ref);
        });
    }
}

APICALL EXPORT std::string PLUGIN_API_VERSION() {
    return HYPRLAND_API_VERSION;
}

APICALL EXPORT PLUGIN_DESCRIPTION_INFO PLUGIN_INIT(HANDLE handle) {
    PHANDLE = handle;

    g_aoCriar     = Event::bus()->m_events.window.create.listen([](PHLWINDOW w) { ouvir(w); });
    g_aoAbrir     = Event::bus()->m_events.window.open.listen([](PHLWINDOW w) { ouvir(w); });
    g_aoDestruir  = Event::bus()->m_events.window.destroy.listen([](PHLWINDOWREF) {
        std::erase_if(g_ouvintes, [](const auto& par) {
            return std::ranges::none_of(Desktop::viewState()->windows(), [&](const auto& j) { return j.get() == par.first; });
        });
    });
    for (const auto& w : Desktop::viewState()->windows())
        ouvir(w);

    return {"minimizar", "Faz o botão minimizar dos próprios apps funcionar", "aux", "1.0"};
}

APICALL EXPORT void PLUGIN_EXIT() {
    g_ouvintes.clear();
}
