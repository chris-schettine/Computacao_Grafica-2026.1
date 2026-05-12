"""
revolucao.py
Superfícies e sólidos de revolução em torno do eixo Z.
"""
import numpy as np


def superficie_revolucao(raios, alturas, num_fatias=80):
    """
    Rotaciona a curva geratriz (raios, alturas) em torno do eixo Z.
    Retorna X, Y, Z.
    """
    raios = np.array(raios, dtype=float)
    alturas = np.array(alturas, dtype=float)
    theta = np.linspace(0, 2 * np.pi, num_fatias)
    R, T = np.meshgrid(raios, theta)
    return R * np.cos(T), R * np.sin(T), np.tile(alturas, (num_fatias, 1))


def perfil_taca():
    t = np.linspace(0, 1, 80)
    alturas = t * 4.0
    raios = (0.15
             + 0.8 * np.exp(-((t - 0.70) ** 2) / 0.020)
             + 0.3 * np.exp(-((t - 0.15) ** 2) / 0.005))
    return raios, alturas


def perfil_vaso():
    t = np.linspace(0, 1, 80)
    alturas = t * 3.5
    raios = np.clip(
        0.9 * (1 - t) * np.exp(-2 * t)
        + 0.4 * np.exp(-((t - 0.55) ** 2) / 0.01)
        + 0.6 * t ** 2 * np.exp(-2 * (1 - t)),
        0.08, None)
    return raios, alturas


def perfil_garrafa():
    t = np.linspace(0, 1, 100)
    alturas = t * 5.0
    raios = np.where(
        t < 0.60,
        0.5 + 0.05 * np.sin(5 * np.pi * t),
        np.where(t < 0.75, 0.5 - 2.5 * (t - 0.60), 0.15))
    return raios, alturas
