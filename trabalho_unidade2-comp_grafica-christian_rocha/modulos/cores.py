"""
cores.py
Palheta de cores RGB normalizado [0,1] e utilitários.

Sobre o modelo RGB:
  Cada cor é definida por três componentes R (vermelho), G (verde), B (azul)
  no intervalo [0.0, 1.0]. A combinação aditiva dos três canais gera qualquer
  cor: (1,0,0)=vermelho, (0,1,1)=ciano, (1,1,1)=branco, (0,0,0)=preto.
"""
import numpy as np


def criar_palheta():
    """Dicionário {nome: (R, G, B)} em [0,1]."""
    return {
        "Cinza":    (0.55, 0.55, 0.60),
        "Vermelho": (1.00, 0.25, 0.25),
        "Verde":    (0.20, 0.90, 0.40),
        "Azul":     (0.25, 0.55, 1.00),
        "Amarelo":  (1.00, 0.90, 0.10),
        "Laranja":  (1.00, 0.50, 0.05),
        "Ciano":    (0.10, 0.90, 0.90),
        "Magenta":  (0.90, 0.20, 0.90),
        "Branco":   (0.95, 0.95, 0.95),
        "Rosa":     (1.00, 0.45, 0.75),
        "Violeta":  (0.55, 0.20, 0.90),
        "Dourado":  (1.00, 0.80, 0.10),
    }


def rgb_para_hex(r, g, b):
    return "#{:02X}{:02X}{:02X}".format(
        int(np.clip(r, 0, 1) * 255),
        int(np.clip(g, 0, 1) * 255),
        int(np.clip(b, 0, 1) * 255),
    )


def esquema_padrao():
    """Cores padrão por elemento geométrico."""
    return {
        "curva":            (0.20, 0.65, 1.00),
        "bezier":           (1.00, 0.45, 0.10),
        "ctrl_pt":          (1.00, 0.20, 0.20),
        "ctrl_poly":        (0.60, 0.60, 0.65),
        "superficie":       (0.30, 0.80, 0.55),
        "retalho":          (0.75, 0.40, 0.95),
        "revolucao":        (1.00, 0.75, 0.15),
        "deslocamento":     (0.15, 0.85, 0.90),
        "extrusao":         (0.95, 0.35, 0.50),
    }
