"""
bezier.py
Curvas de Bézier via polinômios de Bernstein — implementação manual.
"""
import numpy as np
from math import comb


def bernstein(n, i, t):
    """Polinômio de Bernstein B_{i,n}(t)."""
    return comb(n, i) * (t ** i) * ((1 - t) ** (n - i))


def curva_bezier(pontos_controle, num_pontos=300):
    """
    B(t) = Σ C(n,i)·(1-t)^(n-i)·t^i·Pi
    Retorna array (num_pontos, dim).
    """
    P = np.array(pontos_controle, dtype=float)
    n = len(P) - 1
    curva = []
    for t in np.linspace(0, 1, num_pontos):
        pt = np.zeros(P.shape[1])
        for i in range(n + 1):
            pt += bernstein(n, i, t) * P[i]
        curva.append(pt)
    return np.array(curva)
