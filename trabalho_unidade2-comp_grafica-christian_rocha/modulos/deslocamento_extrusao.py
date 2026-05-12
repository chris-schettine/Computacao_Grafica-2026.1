"""
deslocamento_extrusao.py
Superfícies por deslocamento e sólidos por extrusão.
"""
import numpy as np


def superficie_deslocamento(curva, vetor, passos=40):
    """
    Move a curva ao longo de 'vetor' em 'passos' etapas.
    Retorna X, Y, Z.
    """
    curva = np.array(curva, dtype=float)
    vetor = np.array(vetor, dtype=float)
    listas = [curva + (i / (passos - 1)) * vetor for i in range(passos)]
    sup = np.array(listas)
    return sup[:, :, 0], sup[:, :, 1], sup[:, :, 2]


def extrusao(perfil_2d, altura=2.0):
    """
    Prolonga o perfil 2D no eixo Z até 'altura'.
    Retorna (base, topo), cada um (N, 3).
    """
    p = np.array(perfil_2d, dtype=float)
    base = np.column_stack((p[:, 0], p[:, 1], np.zeros(len(p))))
    topo = np.column_stack((p[:, 0], p[:, 1], np.full(len(p), altura)))
    return base, topo


def extrusao_lados(base, topo):
    """Faces laterais do sólido extrudado. Retorna X, Y, Z (2, N)."""
    X = np.array([base[:, 0], topo[:, 0]])
    Y = np.array([base[:, 1], topo[:, 1]])
    Z = np.array([base[:, 2], topo[:, 2]])
    return X, Y, Z


def perfil_estrela(n_pontas=5, r_ext=1.0, r_int=0.45):
    total = 2 * n_pontas
    angs = [(i / total) * 2 * np.pi - np.pi / 2 for i in range(total + 1)]
    rs   = [r_ext if i % 2 == 0 else r_int for i in range(total + 1)]
    x = np.array(rs) * np.cos(angs)
    y = np.array(rs) * np.sin(angs)
    return np.column_stack((x, y))
