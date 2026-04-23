"""
gera_cena.py  –  Interface interativa com pygame
Painel lateral com sliders e botões para controlar objetos, transformações e câmera.

Controles por teclado (câmera):
  W/S        – frente/trás
  A/D        – esquerda/direita
  Q/E        – cima/baixo
  Setas      – orbitar (yaw/pitch)
  +/-        – zoom (FOV)
  ESC        – sair

Requisitos: numpy, pygame, matplotlib
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from quaternios    import Quaternion
from camera        import Camera
from render3d      import Objeto3D, Renderizador
from transformacao import translacao, escala


# ---------------------------------------------------------------------------
# Paleta de cores
# ---------------------------------------------------------------------------

BG_DARK    = (10,  10,  20)
PANEL_BG   = (18,  20,  32)
PANEL_LINE = (38,  42,  62)
SEC_LINE   = (45,  50,  75)
TEXT_PRI   = (215, 220, 245)
TEXT_SEC   = (110, 118, 155)
TEXT_HDR   = (160, 168, 210)
ACCENT     = (55,  135, 245)
ACCENT_DIM = (30,   75, 160)
BTN_HOV    = (45,  50,  78)
BTN_ACT    = (50,  125, 230)
BTN_BG     = (28,  31,  48)
SLIDER_TRK = (38,  42,  62)
SLIDER_THB = (55,  135, 245)
HUD_COL    = (120, 128, 170)


# ---------------------------------------------------------------------------
# Geometrias
# ---------------------------------------------------------------------------

def _geo_cubo():
    v = [[-1,-1,-1],[1,-1,-1],[1,-1,1],[-1,-1,1],
         [-1, 1,-1],[1, 1,-1],[1, 1,1],[-1, 1,1]]
    e = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),
         (0,4),(1,5),(2,6),(3,7)]
    return v, e

def _geo_piramide():
    v = [[-1,0,-1],[1,0,-1],[1,0,1],[-1,0,1],[0,2,0]]
    e = [(0,1),(1,2),(2,3),(3,0),(0,4),(1,4),(2,4),(3,4)]
    return v, e

def _geo_octaedro():
    v = [[0,1,0],[1,0,0],[0,0,1],[-1,0,0],[0,0,-1],[0,-1,0]]
    e = [(0,1),(0,2),(0,3),(0,4),(5,1),(5,2),(5,3),(5,4),
         (1,2),(2,3),(3,4),(4,1)]
    return v, e

def _geo_prisma():
    a1, a2 = 2*np.pi/3, 4*np.pi/3
    v = [[0,1,0],[np.cos(a1),1,np.sin(a1)],[np.cos(a2),1,np.sin(a2)],
         [0,-1,0],[np.cos(a1),-1,np.sin(a1)],[np.cos(a2),-1,np.sin(a2)]]
    e = [(0,1),(1,2),(2,0),(3,4),(4,5),(5,3),(0,3),(1,4),(2,5)]
    return v, e

def _geo_icosaedro():
    phi = (1 + np.sqrt(5)) / 2
    pts = [[-1,phi,0],[1,phi,0],[-1,-phi,0],[1,-phi,0],
           [0,-1,phi],[0,1,phi],[0,-1,-phi],[0,1,-phi],
           [phi,0,-1],[phi,0,1],[-phi,0,-1],[-phi,0,1]]
    v = [np.array(p)/np.linalg.norm(p) for p in pts]
    e = [(0,1),(0,5),(0,7),(0,10),(0,11),(1,5),(1,7),(1,8),(1,9),
         (2,3),(2,4),(2,6),(2,10),(2,11),(3,4),(3,6),(3,8),(3,9),
         (4,5),(4,9),(4,11),(5,9),(5,11),(6,7),(6,8),(6,10),
         (7,8),(7,10),(8,9),(10,11)]
    return [p.tolist() for p in v], e

GEOMETRIAS = {
    "Cubo":      _geo_cubo,
    "Piramide":  _geo_piramide,
    "Octaedro":  _geo_octaedro,
    "Prisma":    _geo_prisma,
    "Icosaedro": _geo_icosaedro,
}

CORES_WIRE = {
    "Ciano":    (0,   200, 255),
    "Vermelho": (240,  80,  80),
    "Verde":    (80,  240, 120),
    "Ambar":   (255, 200,  60),
    "Roxo":     (180, 100, 255),
    "Branco":   (230, 230, 230),
}

EIXOS = ["Y", "X", "Z", "X+Y+Z"]


# ---------------------------------------------------------------------------
# Widgets
# ---------------------------------------------------------------------------

class Slider:
    def __init__(self, x, y, w, label, vmin, vmax, value, fmt="{:.2f}"):
        self.x, self.y, self.w = x, y, w
        self.label    = label
        self.vmin     = vmin
        self.vmax     = vmax
        self.value    = value
        self.fmt      = fmt
        self.dragging = False
        # altura total do widget: label(16) + gap(4) + trilho(20) = 40
        self.total_h  = 40

    def _thumb_x(self):
        t = (self.value - self.vmin) / (self.vmax - self.vmin)
        return int(self.x + t * self.w)

    def draw(self, surf, font_lbl, font_val):
        import pygame
        # label
        lbl = font_lbl.render(self.label, True, TEXT_SEC)
        surf.blit(lbl, (self.x, self.y))
        # trilho (centro y = label_h + gap + metade trilho)
        cy = self.y + 16 + 4 + 10
        pygame.draw.rect(surf, SLIDER_TRK, (self.x, cy - 3, self.w, 6), border_radius=3)
        fill = self._thumb_x() - self.x
        if fill > 0:
            pygame.draw.rect(surf, ACCENT_DIM, (self.x, cy - 3, fill, 6), border_radius=3)
        # polegar
        tx = self._thumb_x()
        pygame.draw.circle(surf, SLIDER_THB, (tx, cy), 9)
        pygame.draw.circle(surf, (210, 230, 255), (tx, cy), 4)
        # valor
        val = font_val.render(self.fmt.format(self.value), True, TEXT_PRI)
        surf.blit(val, (self.x + self.w + 10, cy - val.get_height() // 2))

    def handle_event(self, event):
        import pygame
        cy = self.y + 16 + 4 + 10
        hit = pygame.Rect(self.x - 10, cy - 14, self.w + 20, 28)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if hit.collidepoint(event.pos):
                self.dragging = True
                self._set(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._set(event.pos[0])

    def _set(self, mx):
        t = max(0.0, min(1.0, (mx - self.x) / self.w))
        self.value = self.vmin + t * (self.vmax - self.vmin)


class Button:
    def __init__(self, x, y, w, h, label, active=False):
        self.rect    = (x, y, w, h)
        self.label   = label
        self.active  = active
        self.hovered = False

    def draw(self, surf, font):
        import pygame
        x, y, w, h = self.rect
        bg = BTN_ACT if self.active else (BTN_HOV if self.hovered else BTN_BG)
        tc = (255, 255, 255) if self.active else TEXT_PRI
        pygame.draw.rect(surf, bg,        self.rect, border_radius=5)
        pygame.draw.rect(surf, PANEL_LINE, self.rect, 1, border_radius=5)
        lbl = font.render(self.label, True, tc)
        lr  = lbl.get_rect(center=(x + w // 2, y + h // 2))
        surf.blit(lbl, lr)

    def handle_event(self, event):
        import pygame
        if event.type == pygame.MOUSEMOTION:
            self.hovered = pygame.Rect(self.rect).collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if pygame.Rect(self.rect).collidepoint(event.pos):
                return True
        return False


# ---------------------------------------------------------------------------
# UIState  –  monta todos os widgets sequencialmente sem sobreposição
# ---------------------------------------------------------------------------

class UIState:
    def __init__(self, PW, H):
        self.obj_idx  = 0
        self.cor_idx  = 0
        self.eixo_idx = 0
        self.animando = True

        M  = 18          # margem lateral
        SW = PW - M*2 - 52  # largura slider (espaço para valor à direita)
        BH = 28          # altura dos botões
        GAP_SEC  = 10    # espaço antes do label de seção
        GAP_BTN  = 6     # espaço entre botões e próxima seção
        GAP_SL   = 14    # espaço entre sliders

        obj_nomes = list(GEOMETRIAS.keys())
        cor_nomes = list(CORES_WIRE.keys())

        # ---- posicionamento sequencial ----
        y = 16

        # Título
        self.y_title = y;  y += 30

        # --- Seção Objeto ---
        self.y_sec_obj = y;  y += 20
        # 3 botões na linha 1, 2 na linha 2
        bw3 = (PW - M*2 - 8) // 3
        bw2 = (PW - M*2 - 4) // 2
        self.btn_objs = []
        for i, n in enumerate(obj_nomes):
            if i < 3:
                bx = M + i * (bw3 + 4)
                by = y
            else:
                bx = M + (i - 3) * (bw2 + 4)
                by = y + BH + 5
            self.btn_objs.append(Button(bx, by, bw3 if i < 3 else bw2, BH, n, i == 0))
        y += BH + 5 + BH + GAP_BTN

        # divisória
        self.div_y = []; self.div_y.append(y);  y += 14

        # --- Seção Transformações ---
        self.y_sec_trf = y;  y += 20
        sl_data_trf = [
            ("Escala X",      0.1, 3.0, 1.0, "{:.2f}"),
            ("Escala Y",      0.1, 3.0, 1.0, "{:.2f}"),
            ("Escala Z",      0.1, 3.0, 1.0, "{:.2f}"),
            ("Translacao X", -3.0, 3.0, 0.0, "{:.2f}"),
            ("Translacao Y", -3.0, 3.0, 0.0, "{:.2f}"),
            ("Translacao Z", -3.0, 3.0, 0.0, "{:.2f}"),
        ]
        self.sl_trf = []
        for lbl, vmin, vmax, val, fmt in sl_data_trf:
            sl = Slider(M, y, SW, lbl, vmin, vmax, val, fmt)
            self.sl_trf.append(sl)
            y += sl.total_h + GAP_SL
        y += GAP_BTN - GAP_SL

        self.div_y.append(y);  y += 14

        # --- Seção Cor ---
        self.y_sec_cor = y;  y += 20
        ncor = len(cor_nomes)
        cw   = (PW - M*2 - (ncor-1)*4) // ncor
        self.btn_cores = [
            Button(M + i*(cw+4), y, cw, BH, n[:3], i == 0)
            for i, n in enumerate(cor_nomes)
        ]
        y += BH + GAP_BTN

        self.div_y.append(y);  y += 14

        # --- Seção Câmera ---
        self.y_sec_cam = y;  y += 20
        sl_data_cam = [
            ("FOV",          20, 120, 60, "{:.0f}graus"),
            ("Dist. camera",  3,  20,  7, "{:.1f}"),
            ("Velocidade",    0, 200, 60, "{:.0f}graus/s"),
        ]
        self.sl_cam = []
        for lbl, vmin, vmax, val, fmt in sl_data_cam:
            sl = Slider(M, y, SW, lbl, vmin, vmax, val, fmt)
            self.sl_cam.append(sl)
            y += sl.total_h + GAP_SL
        y += GAP_BTN - GAP_SL

        self.div_y.append(y);  y += 14

        # --- Seção Eixo ---
        self.y_sec_ax = y;  y += 20
        nax = len(EIXOS)
        aw  = (PW - M*2 - (nax-1)*4) // nax
        self.btn_eixos = [
            Button(M + i*(aw+4), y, aw, BH, e, i == 0)
            for i, e in enumerate(EIXOS)
        ]
        y += BH + GAP_BTN

        self.div_y.append(y);  y += 14

        # --- Botão pausar ---
        self.btn_pau = Button(M, y, PW - M*2, 32, "Pausar")
        y += 32 + GAP_BTN

        # --- Atalhos no rodapé ---
        self.y_keys_start = y

        # referências úteis
        self.sl_sx, self.sl_sy, self.sl_sz = self.sl_trf[0], self.sl_trf[1], self.sl_trf[2]
        self.sl_tx, self.sl_ty, self.sl_tz = self.sl_trf[3], self.sl_trf[4], self.sl_trf[5]
        self.sl_fov, self.sl_dist, self.sl_vel = self.sl_cam[0], self.sl_cam[1], self.sl_cam[2]
        self.all_sliders = self.sl_trf + self.sl_cam
        self.M  = M
        self.PW = PW

    def handle_event(self, event):
        for sl in self.all_sliders:
            sl.handle_event(event)
        for i, btn in enumerate(self.btn_objs):
            if btn.handle_event(event):
                self.obj_idx = i
                for b in self.btn_objs: b.active = False
                btn.active = True
        for i, btn in enumerate(self.btn_cores):
            if btn.handle_event(event):
                self.cor_idx = i
                for b in self.btn_cores: b.active = False
                btn.active = True
        for i, btn in enumerate(self.btn_eixos):
            if btn.handle_event(event):
                self.eixo_idx = i
                for b in self.btn_eixos: b.active = False
                btn.active = True
        if self.btn_pau.handle_event(event):
            self.animando = not self.animando
            self.btn_pau.label = "Continuar" if not self.animando else "Pausar"

    def draw_panel(self, surf, fonts):
        import pygame
        font_sm, font_xs, font_md, font_sec = fonts
        PW, M = self.PW, self.M

        surf.fill(PANEL_BG)
        pygame.draw.line(surf, PANEL_LINE, (PW - 1, 0), (PW - 1, surf.get_height()))

        def div(y):
            pygame.draw.line(surf, SEC_LINE, (M, y + 5), (PW - M, y + 5))

        def sec(txt, y):
            surf.blit(font_sec.render(txt, True, TEXT_SEC), (M, y))

        surf.blit(font_md.render("Controles", True, TEXT_PRI), (M, self.y_title))

        sec("OBJETO", self.y_sec_obj)
        for b in self.btn_objs:  b.draw(surf, font_sm)

        div(self.div_y[0])

        sec("TRANSFORMACOES", self.y_sec_trf)
        for sl in self.sl_trf: sl.draw(surf, font_xs, font_sm)

        div(self.div_y[1])

        sec("COR DO WIREFRAME", self.y_sec_cor)
        for b in self.btn_cores: b.draw(surf, font_xs)

        div(self.div_y[2])

        sec("CAMERA / ANIMACAO", self.y_sec_cam)
        for sl in self.sl_cam: sl.draw(surf, font_xs, font_sm)

        div(self.div_y[3])

        sec("EIXO DE ROTACAO", self.y_sec_ax)
        for b in self.btn_eixos: b.draw(surf, font_sm)

        div(self.div_y[4])

        self.btn_pau.draw(surf, font_sm)

        # Atalhos
        atalhos = [
            ("W / S",    "frente / tras"),
            ("A / D",    "esq. / dir."),
            ("Q / E",    "cima / baixo"),
            ("Setas",    "orbitar"),
            ("+ / -",    "zoom"),
            ("ESC",      "sair"),
        ]
        y0 = self.y_keys_start
        sec("TECLADO", y0);  y0 += 18
        for key, desc in atalhos:
            surf.blit(font_xs.render(key,  True, TEXT_HDR), (M,      y0))
            surf.blit(font_xs.render(desc, True, TEXT_SEC), (M + 78, y0))
            y0 += 16


# ---------------------------------------------------------------------------
# Loop principal
# ---------------------------------------------------------------------------

def main():
    import pygame

    pygame.init()

    PANEL_W = 290
    RW, RH  = 860, 800
    W, H    = PANEL_W + RW, RH

    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Computacao Grafica - Interface Interativa")
    clock  = pygame.time.Clock()

    font_md  = pygame.font.SysFont("segoeui", 17, bold=True)
    font_sm  = pygame.font.SysFont("segoeui", 14)
    font_xs  = pygame.font.SysFont("segoeui", 12)
    font_sec = pygame.font.SysFont("segoeui", 11)
    fonts    = (font_sm, font_xs, font_md, font_sec)

    ui           = UIState(PANEL_W, H)
    renderizador = Renderizador(RW, RH)

    camera = Camera(
        eye=[7, 5, 7], at=[0, 0, 0], up=[0, 1, 0],
        fov=60, aspect=RW/RH, near=0.1, far=100.0
    )

    obj_nomes = list(GEOMETRIAS.keys())
    cor_nomes = list(CORES_WIRE.keys())
    cor_vals  = list(CORES_WIRE.values())

    q_acum   = Quaternion(1, 0, 0, 0)
    last_obj = -1

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            ui.handle_event(event)

        if ui.obj_idx != last_obj:
            q_acum   = Quaternion(1, 0, 0, 0)
            last_obj = ui.obj_idx

        # Teclado – câmera
        keys = pygame.key.get_pressed()
        vel  = 3.0 * dt
        if keys[pygame.K_w]:     camera.move( 0,  0, -vel)
        if keys[pygame.K_s]:     camera.move( 0,  0,  vel)
        if keys[pygame.K_a]:     camera.move(-vel, 0,  0)
        if keys[pygame.K_d]:     camera.move( vel, 0,  0)
        if keys[pygame.K_q]:     camera.move( 0,  vel, 0)
        if keys[pygame.K_e]:     camera.move( 0, -vel, 0)
        if keys[pygame.K_UP]:    camera.orbit( 0,  60*dt)
        if keys[pygame.K_DOWN]:  camera.orbit( 0, -60*dt)
        if keys[pygame.K_LEFT]:  camera.orbit( 60*dt, 0)
        if keys[pygame.K_RIGHT]: camera.orbit(-60*dt, 0)
        if keys[pygame.K_PLUS]  or keys[pygame.K_KP_PLUS]:  camera.zoom(-30*dt)
        if keys[pygame.K_MINUS] or keys[pygame.K_KP_MINUS]: camera.zoom( 30*dt)

        # Sliders – câmera
        camera.fov = ui.sl_fov.value
        camera.eye = camera.at + camera.n * ui.sl_dist.value
        camera._compute_vectors()

        # Animação
        if ui.animando:
            spd = np.radians(ui.sl_vel.value) * dt
            ax_map = {
                0: [0, 1, 0],
                1: [1, 0, 0],
                2: [0, 0, 1],
                3: [1/np.sqrt(3), 1/np.sqrt(3), 1/np.sqrt(3)],
            }
            dq     = Quaternion.from_axis_angle(ax_map[ui.eixo_idx], spd)
            q_acum = (dq * q_acum).normalize()

        # Objeto
        verts, arestas = GEOMETRIAS[obj_nomes[ui.obj_idx]]()
        cor_wire       = cor_vals[ui.cor_idx]
        obj = Objeto3D(verts, arestas, cor=tuple(c/255 for c in cor_wire))
        obj.apply_transform(escala(ui.sl_sx.value, ui.sl_sy.value, ui.sl_sz.value))
        obj.apply_transform(q_acum.to_rotation_matrix())
        obj.apply_transform(translacao(ui.sl_tx.value, ui.sl_ty.value, ui.sl_tz.value))

        # Render
        renderizador.render([obj], camera)
        img     = renderizador.get_image_uint8()
        surf_3d = pygame.surfarray.make_surface(np.transpose(img, (1, 0, 2)))
        screen.fill(BG_DARK)
        screen.blit(surf_3d, (PANEL_W, 0))

        painel = pygame.Surface((PANEL_W, H))
        ui.draw_panel(painel, fonts)
        screen.blit(painel, (0, 0))

        # HUD
        q   = q_acum.normalize()
        hud = [
            f"obj: {obj_nomes[ui.obj_idx]}   cor: {cor_nomes[ui.cor_idx]}",
            f"q = ({q.w:.2f}  {q.x:.2f}i  {q.y:.2f}j  {q.z:.2f}k)",
            f"eye=({camera.eye[0]:.1f},{camera.eye[1]:.1f},{camera.eye[2]:.1f})  FOV={camera.fov:.0f}",
        ]
        for i, line in enumerate(hud):
            s = font_xs.render(line, True, HUD_COL)
            screen.blit(s, (PANEL_W + 10, H - (len(hud) - i) * 17 - 6))

        pygame.display.flip()

    pygame.quit()
    print("Encerrado.")


if __name__ == "__main__":
    main()
