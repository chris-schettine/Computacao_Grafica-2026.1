"""
curvas_superficies.py
Funções para curvas e superfícies paramétricas e retalhos.
"""
import numpy as np


def curva_parametrica(t, tipo="helice"):
    """
    Curva paramétrica 3D.
    tipo: 'helice' | 'senoidal' | 'lissajous'
    Retorna array (N, 3).
    """
    if tipo == "senoidal":
        return np.column_stack((t, np.sin(t), np.zeros_like(t)))
    elif tipo == "helice":
        return np.column_stack((np.cos(t), np.sin(t), t / (2 * np.pi)))
    elif tipo == "lissajous":
        return np.column_stack((np.sin(3 * t), np.sin(2 * t), np.cos(t)))
    raise ValueError(f"tipo desconhecido: {tipo}")


def superficie_parametrica(u, v, tipo="ondulada"):
    """
    Superfície paramétrica 3D.
    tipo: 'ondulada' | 'toroide' | 'esfera'
    Retorna X, Y, Z (meshgrid).
    """
    if tipo == "ondulada":
        return u, v, np.sin(u) * np.cos(v)
    elif tipo == "toroide":
        R, r = 2.0, 0.7
        X = (R + r * np.cos(v)) * np.cos(u)
        Y = (R + r * np.cos(v)) * np.sin(u)
        Z = r * np.sin(v)
        return X, Y, Z
    elif tipo == "esfera":
        return np.sin(u) * np.cos(v), np.sin(u) * np.sin(v), np.cos(u)
    raise ValueError(f"tipo desconhecido: {tipo}")


def retalho_superficie(u_min, u_max, v_min, v_max, nu=40, nv=40):
    """
    Retalho de superfície bicúbica sin*cos*exp limitado pelos intervalos dados.
    Retorna X, Y, Z.
    """
    u = np.linspace(u_min, u_max, nu)
    v = np.linspace(v_min, v_max, nv)
    U, V = np.meshgrid(u, v)
    Z = np.sin(U) * np.cos(V) * np.exp(-0.1 * (U ** 2 + V ** 2))
    return U, V, Z
