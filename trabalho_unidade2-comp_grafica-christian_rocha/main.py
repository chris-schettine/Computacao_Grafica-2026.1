"""
main.py  —  Trabalho 2: Curvas, Superfícies e Cores
Computação Gráfica  |  Interface estilo Trabalho 1

Layout: painel de controles (esquerda) + visualização 3D matplotlib (direita)
Fundo preto, wireframe colorido, sliders e botões estilo dark.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import tkinter as tk
from tkinter import ttk, font as tkfont
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

from modulos.curvas_superficies  import curva_parametrica, superficie_parametrica, retalho_superficie
from modulos.bezier              import curva_bezier
from modulos.revolucao           import superficie_revolucao, perfil_taca, perfil_vaso, perfil_garrafa
from modulos.deslocamento_extrusao import (superficie_deslocamento, extrusao,
                                           extrusao_lados, perfil_estrela)
from modulos.cores               import criar_palheta, rgb_para_hex, esquema_padrao

# ── Paleta de UI ─────────────────────────────────────────────────────────────
BG       = "#1a1a2a"   # fundo geral
BG2      = "#12121e"   # fundo do canvas
PANEL    = "#1e1e30"   # painel lateral
ACCENT   = "#4fa3d1"   # azul destaque (slider, selecionado)
ACCENT2  = "#5555bb"   # botão selecionado
BTN_DEF  = "#2a2a40"   # botão padrão
BTN_SEL  = "#4a4aaa"   # botão selecionado
FG       = "#c8c8e0"   # texto geral
FG2      = "#7878aa"   # texto secundário
SEP      = "#2a2a44"   # separador

FONT_TITLE = ("Segoe UI", 9, "bold")
FONT_LABEL = ("Segoe UI", 8)
FONT_SMALL = ("Segoe UI", 7)
FONT_MONO  = ("Consolas", 7)

# ── Modos do visualizador ────────────────────────────────────────────────────
MODOS = [
    "Curva Param.",
    "Superfície",
    "Retalho",
    "Bézier",
    "Revolução",
    "Deslocamento",
    "Extrusão",
    "Cena Completa",
]

COR_NAMES = list(criar_palheta().keys())


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Computação Gráfica — Interface Interativa")
        self.configure(bg=BG)
        self.geometry("1240x760")
        self.minsize(900, 580)

        # Estado
        self.modo        = tk.StringVar(value=MODOS[0])
        self.cor_nome    = tk.StringVar(value="Azul")
        self.escala_x    = tk.DoubleVar(value=1.0)
        self.escala_y    = tk.DoubleVar(value=1.0)
        self.escala_z    = tk.DoubleVar(value=1.0)
        self.trans_x     = tk.DoubleVar(value=0.0)
        self.trans_y     = tk.DoubleVar(value=0.0)
        self.trans_z     = tk.DoubleVar(value=0.0)
        self.alpha       = tk.DoubleVar(value=0.85)
        self.resolucao   = tk.IntVar(value=60)
        self.wireframe   = tk.BooleanVar(value=False)
        self.mostrar_eixos = tk.BooleanVar(value=True)
        self.sub_modo    = tk.StringVar(value="Hélice")

        self._build_ui()
        self._draw()

    # =========================================================================
    #  BUILD UI
    # =========================================================================

    def _build_ui(self):
        # ── Layout raiz ──────────────────────────────────────────────────────
        self.columnconfigure(0, minsize=310, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # Painel esquerdo
        self.panel = tk.Frame(self, bg=PANEL, width=310)
        self.panel.grid(row=0, column=0, sticky="nsew")
        self.panel.grid_propagate(False)

        # Área de visualização
        viz_frame = tk.Frame(self, bg=BG2)
        viz_frame.grid(row=0, column=1, sticky="nsew")
        viz_frame.rowconfigure(0, weight=1)
        viz_frame.columnconfigure(0, weight=1)

        # Canvas matplotlib
        self.fig = plt.Figure(facecolor=BG2, tight_layout=True)
        self.ax  = self.fig.add_subplot(111, projection="3d")
        self._style_ax()

        self.canvas = FigureCanvasTkAgg(self.fig, master=viz_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        # Barra de status (rodapé)
        self.status_var = tk.StringVar(value="obj: —  |  cor: Azul  |  modo: Curva Param.")
        status_bar = tk.Label(viz_frame, textvariable=self.status_var,
                              bg="#0e0e18", fg=FG2, font=FONT_MONO,
                              anchor="w", padx=10)
        status_bar.grid(row=1, column=0, sticky="ew")

        # Preenche painel
        self._build_panel()

    def _style_ax(self):
        ax = self.ax
        ax.set_facecolor(BG2)
        for pane in [ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane]:
            pane.fill = False
            pane.set_edgecolor("#2a2a44")
        ax.tick_params(colors="#555577", labelsize=6)
        ax.xaxis.label.set_color(FG2)
        ax.yaxis.label.set_color(FG2)
        ax.zaxis.label.set_color(FG2)
        ax.grid(True, color="#222233", linewidth=0.5)

    # ── Painel de controles ───────────────────────────────────────────────────

    def _build_panel(self):
        p = self.panel

        # Scrollable interior
        canvas_scroll = tk.Canvas(p, bg=PANEL, highlightthickness=0)
        scrollbar = ttk.Scrollbar(p, orient="vertical", command=canvas_scroll.yview)
        self.inner = tk.Frame(canvas_scroll, bg=PANEL)
        self.inner.bind("<Configure>",
                        lambda e: canvas_scroll.configure(
                            scrollregion=canvas_scroll.bbox("all")))
        canvas_scroll.create_window((0, 0), window=self.inner, anchor="nw")
        canvas_scroll.configure(yscrollcommand=scrollbar.set)
        canvas_scroll.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mousewheel
        def _on_mousewheel(event):
            canvas_scroll.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas_scroll.bind_all("<MouseWheel>", _on_mousewheel)

        i = self.inner

        self._section(i, "OBJETO")
        self._modo_buttons(i)

        self._section(i, "VARIANTE")
        self._sub_modo_buttons(i)

        self._section(i, "COR DA GEOMETRIA")
        self._cor_buttons(i)

        self._section(i, "TRANSFORMAÇÕES")
        self._slider(i, "Escala X",   self.escala_x, 0.1, 3.0)
        self._slider(i, "Escala Y",   self.escala_y, 0.1, 3.0)
        self._slider(i, "Escala Z",   self.escala_z, 0.1, 3.0)
        self._slider(i, "Translação X", self.trans_x, -4.0, 4.0)
        self._slider(i, "Translação Y", self.trans_y, -4.0, 4.0)
        self._slider(i, "Translação Z", self.trans_z, -4.0, 4.0)

        self._section(i, "VISUALIZAÇÃO")
        self._slider(i, "Alpha",      self.alpha,     0.1, 1.0)
        self._slider(i, "Resolução",  self.resolucao, 10, 120, integer=True)

        self._section(i, "OPÇÕES")
        self._check(i, "Wireframe apenas",   self.wireframe)
        self._check(i, "Mostrar eixos XYZ",  self.mostrar_eixos)

        self._section(i, "")
        btn_render = tk.Button(i, text="▶  RENDERIZAR",
                               command=self._draw,
                               bg=BTN_SEL, fg="white",
                               font=("Segoe UI", 9, "bold"),
                               relief="flat", padx=8, pady=7,
                               activebackground="#6666cc",
                               activeforeground="white",
                               cursor="hand2")
        btn_render.pack(fill="x", padx=14, pady=(4, 2))

        btn_reset = tk.Button(i, text="↺  Resetar",
                              command=self._reset,
                              bg=BTN_DEF, fg=FG,
                              font=FONT_LABEL,
                              relief="flat", padx=8, pady=5,
                              activebackground="#333355",
                              cursor="hand2")
        btn_reset.pack(fill="x", padx=14, pady=(0, 10))

    # ── Widgets helpers ───────────────────────────────────────────────────────

    def _section(self, parent, title):
        if title:
            tk.Label(parent, text=title, bg=PANEL, fg=FG2,
                     font=("Segoe UI", 7, "bold"),
                     anchor="w").pack(fill="x", padx=14, pady=(10, 2))
        tk.Frame(parent, bg=SEP, height=1).pack(fill="x", padx=10, pady=(0, 4))

    def _slider(self, parent, label, var, lo, hi, integer=False):
        frame = tk.Frame(parent, bg=PANEL)
        frame.pack(fill="x", padx=14, pady=1)

        lbl = tk.Label(frame, text=label, bg=PANEL, fg=FG, font=FONT_LABEL,
                       width=13, anchor="w")
        lbl.pack(side="left")

        val_lbl = tk.Label(frame, bg=PANEL, fg=ACCENT, font=FONT_MONO, width=6)
        val_lbl.pack(side="right")

        def _update_label(*_):
            v = var.get()
            val_lbl.config(text=f"{int(v)}" if integer else f"{v:.2f}")
        var.trace_add("write", _update_label)
        _update_label()

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.Horizontal.TScale",
                        background=PANEL,
                        troughcolor="#2a2a40",
                        slidercolor=ACCENT)

        sl = ttk.Scale(frame, from_=lo, to=hi, variable=var,
                       orient="horizontal",
                       command=lambda v: None,
                       style="Dark.Horizontal.TScale")
        sl.pack(side="left", fill="x", expand=True, padx=(4, 4))

    def _check(self, parent, label, var):
        style = ttk.Style()
        style.configure("Dark.TCheckbutton",
                        background=PANEL, foreground=FG,
                        font=FONT_LABEL)
        cb = ttk.Checkbutton(parent, text=label, variable=var,
                             style="Dark.TCheckbutton",
                             command=self._draw)
        cb.pack(anchor="w", padx=18, pady=1)

    def _modo_buttons(self, parent):
        """Grade de botões para seleção de modo."""
        self._btn_frames = {}
        frame = tk.Frame(parent, bg=PANEL)
        frame.pack(fill="x", padx=10, pady=2)
        per_row = 2
        for idx, m in enumerate(MODOS):
            r, c = divmod(idx, per_row)
            btn = tk.Button(frame, text=m, font=FONT_LABEL,
                            bg=BTN_DEF, fg=FG,
                            relief="flat", padx=4, pady=5,
                            activebackground=BTN_SEL,
                            cursor="hand2",
                            command=lambda val=m: self._set_modo(val))
            btn.grid(row=r, column=c, padx=3, pady=2, sticky="ew")
            frame.columnconfigure(c, weight=1)
            self._btn_frames[m] = btn
        self._update_modo_btns()

    def _sub_modo_buttons(self, parent):
        """Botões de variante (dependem do modo)."""
        self._sub_frame = tk.Frame(parent, bg=PANEL)
        self._sub_frame.pack(fill="x", padx=10, pady=2)
        self._rebuild_sub_buttons()

    def _rebuild_sub_buttons(self):
        for w in self._sub_frame.winfo_children():
            w.destroy()
        opts = self._sub_opcoes()
        if not opts:
            tk.Label(self._sub_frame, text="—", bg=PANEL,
                     fg=FG2, font=FONT_SMALL).pack()
            return
        if self.sub_modo.get() not in opts:
            self.sub_modo.set(opts[0])
        per_row = 3
        for idx, o in enumerate(opts):
            r, c = divmod(idx, per_row)
            is_sel = (o == self.sub_modo.get())
            btn = tk.Button(self._sub_frame, text=o, font=FONT_SMALL,
                            bg=BTN_SEL if is_sel else BTN_DEF,
                            fg="white" if is_sel else FG,
                            relief="flat", padx=3, pady=4,
                            activebackground=BTN_SEL,
                            cursor="hand2",
                            command=lambda val=o: self._set_sub(val))
            btn.grid(row=r, column=c, padx=2, pady=2, sticky="ew")
            self._sub_frame.columnconfigure(c, weight=1)

    def _sub_opcoes(self):
        m = self.modo.get()
        if m == "Curva Param.":    return ["Hélice", "Senoidal", "Lissajous"]
        if m == "Superfície":      return ["Toroide", "Ondulada", "Esfera"]
        if m == "Revolução":       return ["Taça", "Vaso", "Garrafa"]
        if m == "Extrusão":        return ["Estrela 5", "Estrela 7", "Círculo"]
        if m == "Deslocamento":    return ["Senoidal", "Circular", "Quadrado"]
        return []

    def _cor_buttons(self, parent):
        """Botões de seleção de cor."""
        self._cor_btns = {}
        frame = tk.Frame(parent, bg=PANEL)
        frame.pack(fill="x", padx=10, pady=2)
        palheta = criar_palheta()
        per_row = 4
        for idx, (nome, rgb) in enumerate(palheta.items()):
            r, c = divmod(idx, per_row)
            hex_c = rgb_para_hex(*rgb)
            abrev = nome[:3]
            is_sel = (nome == self.cor_nome.get())
            btn = tk.Button(frame, text=abrev, font=FONT_SMALL,
                            bg=hex_c if is_sel else BTN_DEF,
                            fg="black" if is_sel else FG,
                            relief="flat" if not is_sel else "sunken",
                            padx=3, pady=4,
                            activebackground=hex_c,
                            cursor="hand2",
                            command=lambda n=nome: self._set_cor(n))
            btn.grid(row=r, column=c, padx=2, pady=2, sticky="ew")
            frame.columnconfigure(c, weight=1)
            self._cor_btns[nome] = btn

    # ── State setters ─────────────────────────────────────────────────────────

    def _set_modo(self, val):
        self.modo.set(val)
        self._update_modo_btns()
        self._rebuild_sub_buttons()
        self._draw()

    def _set_sub(self, val):
        self.sub_modo.set(val)
        self._rebuild_sub_buttons()
        self._draw()

    def _set_cor(self, nome):
        self.cor_nome.set(nome)
        # Atualiza visual dos botões de cor
        palheta = criar_palheta()
        for n, btn in self._cor_btns.items():
            rgb = palheta[n]
            is_sel = (n == nome)
            hex_c = rgb_para_hex(*rgb)
            btn.config(bg=hex_c if is_sel else BTN_DEF,
                       fg="black" if is_sel else FG,
                       relief="sunken" if is_sel else "flat")
        self._draw()

    def _update_modo_btns(self):
        for m, btn in self._btn_frames.items():
            is_sel = (m == self.modo.get())
            btn.config(bg=BTN_SEL if is_sel else BTN_DEF,
                       fg="white" if is_sel else FG)

    def _reset(self):
        self.escala_x.set(1.0); self.escala_y.set(1.0); self.escala_z.set(1.0)
        self.trans_x.set(0.0);  self.trans_y.set(0.0);  self.trans_z.set(0.0)
        self.alpha.set(0.85);   self.resolucao.set(60)
        self.wireframe.set(False); self.mostrar_eixos.set(True)
        self._draw()

    # =========================================================================
    #  DRAW
    # =========================================================================

    def _draw(self, *_):
        self.ax.cla()
        self._style_ax()

        cor_rgb = criar_palheta().get(self.cor_nome.get(), (0.3, 0.7, 1.0))
        modo    = self.modo.get()
        sub     = self.sub_modo.get()
        res     = self.resolucao.get()
        alpha   = self.alpha.get()
        sx, sy, sz = self.escala_x.get(), self.escala_y.get(), self.escala_z.get()
        tx, ty, tz = self.trans_x.get(),  self.trans_y.get(),  self.trans_z.get()
        wf      = self.wireframe.get()

        def transf(X, Y, Z):
            return X * sx + tx, Y * sy + ty, Z * sz + tz

        ax = self.ax
        titulo = f"{modo}  ·  {sub}" if sub else modo

        try:
            if modo == "Curva Param.":
                t = np.linspace(0, 4 * np.pi, max(res * 5, 100))
                tipo_map = {"Hélice": "helice", "Senoidal": "senoidal", "Lissajous": "lissajous"}
                c = curva_parametrica(t, tipo=tipo_map.get(sub, "helice"))
                X, Y, Z = transf(c[:, 0], c[:, 1], c[:, 2])
                ax.plot(X, Y, Z, color=cor_rgb, linewidth=2.2)

            elif modo == "Superfície":
                u = np.linspace(0, 2 * np.pi, res)
                v = np.linspace(0, 2 * np.pi, res)
                U, V = np.meshgrid(u, v)
                tipo_map = {"Toroide": "toroide", "Ondulada": "ondulada", "Esfera": "esfera"}
                X, Y, Z = superficie_parametrica(U, V, tipo=tipo_map.get(sub, "toroide"))
                X, Y, Z = transf(X, Y, Z)
                if wf:
                    ax.plot_wireframe(X, Y, Z, color=cor_rgb, linewidth=0.5, alpha=alpha)
                else:
                    ax.plot_surface(X, Y, Z, color=cor_rgb, alpha=alpha,
                                    linewidth=0, antialiased=True)

            elif modo == "Retalho":
                X, Y, Z = retalho_superficie(-np.pi, np.pi, -np.pi, np.pi, nu=res, nv=res)
                X, Y, Z = transf(X, Y, Z)
                if wf:
                    ax.plot_wireframe(X, Y, Z, color=cor_rgb, linewidth=0.5, alpha=alpha)
                else:
                    ax.plot_surface(X, Y, Z, color=cor_rgb, alpha=alpha,
                                    linewidth=0, antialiased=True)

            elif modo == "Bézier":
                pts = np.array([
                    [0.0, 0.0, 0.0],
                    [0.5, 2.0, 0.5],
                    [1.5, 2.5, 1.2],
                    [2.5, 1.0, 1.8],
                    [3.5, 2.2, 0.6],
                    [4.0, 0.0, 0.0],
                ])
                bz = curva_bezier(pts, num_pontos=max(res * 4, 200))
                X, Y, Z = transf(bz[:, 0], bz[:, 1], bz[:, 2])
                ax.plot(X, Y, Z, color=cor_rgb, linewidth=2.5, label="Bézier grau 5")

                pX, pY, pZ = transf(pts[:, 0], pts[:, 1], pts[:, 2])
                ax.plot(pX, pY, pZ, "--", color="#666688", linewidth=1.2,
                        label="Polígono de controle")
                ax.scatter(pX, pY, pZ, color=(1.0, 0.25, 0.25), s=50, zorder=5,
                           label="Pontos de controle")
                for i, (px, py, pz) in enumerate(zip(pX, pY, pZ)):
                    ax.text(px, py, pz + 0.15, f"P{i}", color=(1, 0.25, 0.25),
                            fontsize=7)
                ax.legend(fontsize=7, loc="upper left",
                          facecolor="#1e1e30", labelcolor=FG,
                          edgecolor="#444466")
                titulo = "Bézier grau 5 — 6 pontos de controle"

            elif modo == "Revolução":
                perfil_map = {"Taça": perfil_taca, "Vaso": perfil_vaso, "Garrafa": perfil_garrafa}
                fn = perfil_map.get(sub, perfil_taca)
                raios, alturas = fn()
                X, Y, Z = superficie_revolucao(raios, alturas, num_fatias=res)
                X, Y, Z = transf(X, Y, Z)
                if wf:
                    ax.plot_wireframe(X, Y, Z, color=cor_rgb, linewidth=0.5, alpha=alpha)
                else:
                    ax.plot_surface(X, Y, Z, color=cor_rgb, alpha=alpha,
                                    linewidth=0, antialiased=True)

            elif modo == "Deslocamento":
                t = np.linspace(0, 2 * np.pi, res)
                tipo_base_map = {
                    "Senoidal": lambda t: np.column_stack((t, np.sin(t), np.zeros_like(t))),
                    "Circular": lambda t: np.column_stack((np.cos(t), np.sin(t), np.zeros_like(t))),
                    "Quadrado": lambda t: np.column_stack((
                        np.clip(np.cos(t) * 2, -1, 1),
                        np.clip(np.sin(t) * 2, -1, 1),
                        np.zeros_like(t))),
                }
                cb = tipo_base_map.get(sub, tipo_base_map["Senoidal"])(t)
                X, Y, Z = superficie_deslocamento(cb, [0, 0, 3.0], passos=res)
                X, Y, Z = transf(X, Y, Z)
                if wf:
                    ax.plot_wireframe(X, Y, Z, color=cor_rgb, linewidth=0.5, alpha=alpha)
                else:
                    ax.plot_surface(X, Y, Z, color=cor_rgb, alpha=alpha,
                                    linewidth=0, antialiased=True)
                # Curva base
                ax.plot(cb[:, 0] * sx + tx, cb[:, 1] * sy + ty, cb[:, 2] * sz + tz,
                        color="white", linewidth=1.5, alpha=0.7, label="Curva base")
                ax.legend(fontsize=7, facecolor="#1e1e30",
                          labelcolor=FG, edgecolor="#444466")

            elif modo == "Extrusão":
                n_map = {"Estrela 5": 5, "Estrela 7": 7}
                if sub == "Círculo":
                    ang = np.linspace(0, 2 * np.pi, res + 1)
                    perfil = np.column_stack((np.cos(ang), np.sin(ang)))
                else:
                    perfil = perfil_estrela(n_pontas=n_map.get(sub, 5))
                base, topo = extrusao(perfil, altura=2.5)
                Xe, Ye, Ze = extrusao_lados(base, topo)
                Xe, Ye, Ze = transf(Xe, Ye, Ze)
                if wf:
                    ax.plot_wireframe(Xe, Ye, Ze, color=cor_rgb, linewidth=0.7, alpha=alpha)
                else:
                    ax.plot_surface(Xe, Ye, Ze, color=cor_rgb, alpha=alpha,
                                    linewidth=0, antialiased=True)
                bX, bY, bZ = transf(base[:, 0], base[:, 1], base[:, 2])
                tX, tY, tZ = transf(topo[:, 0], topo[:, 1], topo[:, 2])
                ax.plot_trisurf(bX, bY, bZ, color=cor_rgb, alpha=alpha * 0.8)
                ax.plot_trisurf(tX, tY, tZ, color=cor_rgb, alpha=alpha * 0.8)

            elif modo == "Cena Completa":
                self._draw_cena_completa(ax, transf, cor_rgb, alpha, wf)
                titulo = "Cena Completa — todos os elementos"

        except Exception as e:
            ax.text2D(0.5, 0.5, f"Erro:\n{e}", transform=ax.transAxes,
                      ha="center", va="center", color="red", fontsize=9)

        # Eixos XYZ
        if self.mostrar_eixos.get():
            try:
                xlim = ax.get_xlim(); ylim = ax.get_ylim(); zlim = ax.get_zlim()
                orig = [xlim[0], ylim[0], zlim[0]]
                for vec, col, lbl in [([1,0,0],"#ff4444","X"),
                                       ([0,1,0],"#44ff44","Y"),
                                       ([0,0,1],"#4488ff","Z")]:
                    span = [abs(xlim[1]-xlim[0]),
                            abs(ylim[1]-ylim[0]),
                            abs(zlim[1]-zlim[0])]
                    length = max(span) * 0.25
                    ax.quiver(*orig,
                              vec[0]*length, vec[1]*length, vec[2]*length,
                              color=col, linewidth=1.5, arrow_length_ratio=0.2)
                    ax.text(orig[0]+vec[0]*length*1.15,
                            orig[1]+vec[1]*length*1.15,
                            orig[2]+vec[2]*length*1.15,
                            lbl, color=col, fontsize=7)
            except Exception:
                pass

        ax.set_title(titulo, color=FG, fontsize=9, pad=6)
        self.fig.tight_layout()
        self.canvas.draw_idle()

        # Atualiza status
        cor_rgb = criar_palheta().get(self.cor_nome.get(), (0,0,1))
        hex_c = rgb_para_hex(*cor_rgb)
        self.status_var.set(
            f"obj: {titulo}  |  cor: {self.cor_nome.get()} {hex_c}  "
            f"|  sx={self.escala_x.get():.2f} sy={self.escala_y.get():.2f} sz={self.escala_z.get():.2f}  "
            f"|  tx={self.trans_x.get():.2f} ty={self.trans_y.get():.2f} tz={self.trans_z.get():.2f}"
        )

    # ── Cena completa ─────────────────────────────────────────────────────────

    def _draw_cena_completa(self, ax, transf, cor_rgb, alpha, wf):
        esq = esquema_padrao()

        # 1. Curva paramétrica (hélice)
        t = np.linspace(0, 4 * np.pi, 300)
        c = curva_parametrica(t, "helice")
        X, Y, Z = c[:, 0] * 0.8, c[:, 1] * 0.8, c[:, 2] * 0.8
        ax.plot(X - 3, Y + 3, Z, color=esq["curva"], linewidth=2, label="Hélice")

        # 2. Bézier
        pts = [[0,3,0],[1,5,1],[2,3,2],[3,5,1],[4,3,0]]
        bz = curva_bezier(pts, 200)
        pA = np.array(pts)
        ax.plot(bz[:,0]-2, bz[:,1]-4, bz[:,2],
                color=esq["bezier"], linewidth=2, label="Bézier")
        ax.scatter(pA[:,0]-2, pA[:,1]-4, pA[:,2],
                   color=esq["ctrl_pt"], s=30, zorder=5)
        ax.plot(pA[:,0]-2, pA[:,1]-4, pA[:,2], "--",
                color=esq["ctrl_poly"], linewidth=0.8)

        # 3. Retalho
        Xr, Yr, Zr = retalho_superficie(0, np.pi, 0, np.pi, nu=25, nv=25)
        ax.plot_surface(Xr - 3, Yr - 3, Zr,
                        color=esq["retalho"], alpha=0.5, linewidth=0)

        # 4. Revolução — taça
        ra, al = perfil_taca()
        Xt, Yt, Zt = superficie_revolucao(ra * 0.5, al * 0.5, num_fatias=50)
        ax.plot_surface(Xt + 3, Yt, Zt,
                        color=esq["revolucao"], alpha=0.75, linewidth=0)

        # 5. Deslocamento
        td = np.linspace(0, 2 * np.pi, 40)
        cb = np.column_stack((td - np.pi, np.sin(td), np.zeros_like(td)))
        Xd, Yd, Zd = superficie_deslocamento(cb, [0, 0, 2], passos=20)
        ax.plot_surface(Xd, Yd + 4, Zd,
                        color=esq["deslocamento"], alpha=0.6, linewidth=0)

        # 6. Extrusão
        pf = perfil_estrela(5, 0.5, 0.22)
        b_e, t_e = extrusao(pf, 1.2)
        Xe, Ye, Ze = extrusao_lados(b_e, t_e)
        ax.plot_surface(Xe - 3, Ye + 0, Ze,
                        color=esq["extrusao"], alpha=0.8, linewidth=0)

        ax.legend(fontsize=7, loc="upper left",
                  facecolor="#1e1e30", labelcolor=FG, edgecolor="#444466")


# =============================================================================
if __name__ == "__main__":
    app = App()
    app.mainloop()
