"""
Correction d'éclairage par surface polynomiale (feuille de route §4, étape 2).

Idée : le papier de la carte est blanc partout. Si la photo le montre plus
sombre à droite qu'à gauche, c'est que la lumière est inégale. On ajuste
une surface lisse (polynôme de degré 2 en x, y) sur les pixels de papier,
une surface par canal R,G,B, puis on divise l'image par cette surface.
Le papier devient uniformément 1.0, la teinte de la lumière est aussi
neutralisée (une surface par canal).
"""
from __future__ import annotations
import numpy as np


def _features(xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
    return np.stack([np.ones_like(xs), xs, ys, xs * xs, xs * ys, ys * ys], axis=-1)


def fit_illumination(rgb_lin: np.ndarray, mask: np.ndarray, step: int = 6) -> np.ndarray:
    """Retourne la surface d'éclairage (H,W,3) estimée sur les pixels `mask`."""
    h, w = mask.shape
    yy, xx = np.mgrid[0:h, 0:w]
    sel = np.zeros_like(mask)
    sel[::step, ::step] = True
    sel &= mask
    xs = (xx[sel] / w).astype(np.float32)
    ys = (yy[sel] / h).astype(np.float32)
    A = _features(xs, ys)

    xg = (xx / w).astype(np.float32)
    yg = (yy / h).astype(np.float32)
    Ag = _features(xg, yg)

    surface = np.empty((h, w, 3), np.float32)
    for c in range(3):
        coef, *_ = np.linalg.lstsq(A, rgb_lin[..., c][sel], rcond=None)
        surface[..., c] = Ag @ coef
    return np.maximum(surface, 1e-3)


def correct_illumination(rgb_lin: np.ndarray, mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Retourne (image_corrigée, surface)."""
    surface = fit_illumination(rgb_lin, mask)
    return rgb_lin / surface, surface


def fit_residual(rgb_lin: np.ndarray, surface: np.ndarray, mask: np.ndarray) -> float:
    """Écart-type de (papier mesuré / surface lisse). Faible = éclairage lisse, bien décrit par la surface.
    Élevé = ombre nette, doigt, pli : la correction n'est plus fiable."""
    lum = np.array([0.2126, 0.7152, 0.0722], np.float32)
    ratio = (rgb_lin @ lum)[mask] / np.maximum((surface @ lum)[mask], 1e-4)
    return float(np.std(ratio))
