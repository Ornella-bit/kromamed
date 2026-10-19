"""
Outils couleur : conversions sRGB <-> RGB linéaire <-> CIE L*a*b*, écart ΔE.

Pourquoi le RGB linéaire ? Un appareil photo enregistre une image "gamma"
(sRGB). Les corrections d'éclairage (division) et de teinte (matrice 3x3)
ne sont physiquement justes que sur la lumière LINÉAIRE. On décode donc
d'abord, on corrige, puis on convertit en L*a*b* pour comparer les couleurs.
"""
from __future__ import annotations
import cv2
import numpy as np


def srgb_to_linear(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float32)
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4).astype(np.float32)


def linear_to_srgb(x: np.ndarray) -> np.ndarray:
    x = np.clip(np.asarray(x, dtype=np.float32), 0.0, 1.0)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055).astype(np.float32)


def hex_to_srgb(code: str) -> np.ndarray:
    code = code.lstrip("#")
    return np.array([int(code[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32) / 255.0


def linear_to_lab(rgb_lin: np.ndarray) -> np.ndarray:
    """RGB linéaire (…,3) dans [0,1] -> L*a*b* (…,3), L dans [0,100]."""
    arr = linear_to_srgb(rgb_lin).reshape(-1, 1, 3).astype(np.float32)
    lab = cv2.cvtColor(arr, cv2.COLOR_RGB2Lab).reshape(-1, 3)
    return lab.reshape(np.shape(rgb_lin))


def srgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    return linear_to_lab(srgb_to_linear(rgb))


def delta_e(lab1: np.ndarray, lab2: np.ndarray) -> np.ndarray:
    """ΔE*ab (CIE76) : distance euclidienne dans L*a*b*.
    Simple et suffisant pour la PoC ; ΔE2000 pourra la remplacer."""
    return np.linalg.norm(np.asarray(lab1) - np.asarray(lab2), axis=-1)
