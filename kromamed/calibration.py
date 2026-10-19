"""
Étalonnage des couleurs (feuille de route §4, étape 3).

On mesure la couleur de chaque patch de référence dans la photo (déjà
corrigée de l'éclairage), on connaît sa vraie couleur, et on cherche la
matrice 3x3 M qui transforme au mieux "ce que voit la caméra" en "ce que
c'est vraiment" (moindres carrés). On l'applique ensuite à toute l'image.
"""
from __future__ import annotations
import numpy as np

from . import config as C
from .color import linear_to_lab, delta_e


def _patch_median(img: np.ndarray, rect: tuple[int, int, int, int], shrink: float = 0.6) -> np.ndarray:
    x, y, w, h = rect
    dx, dy = int(w * (1 - shrink) / 2), int(h * (1 - shrink) / 2)
    roi = img[y + dy:y + h - dy, x + dx:x + w - dx].reshape(-1, 3)
    return np.median(roi, axis=0)


def measure_patches(img: np.ndarray) -> np.ndarray:
    return np.array([_patch_median(img, C.patch_rect(i)) for i in range(len(C.PATCHES))])


def fit_color_matrix(measured: np.ndarray, reference: np.ndarray) -> np.ndarray:
    """M (3x3) tel que measured @ M.T ≈ reference."""
    X, *_ = np.linalg.lstsq(measured, reference, rcond=None)
    return X.T.astype(np.float32)


def apply_matrix(img: np.ndarray, M: np.ndarray) -> np.ndarray:
    return np.clip(img @ M.T, 0.0, 1.5)


def calibrate(img_illum_corrected: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    """Retourne (image_étalonnée, M, erreur_moyenne_ΔE sur les patchs)."""
    reference = np.array([p[1] for p in C.PATCHES], np.float32)
    measured = measure_patches(img_illum_corrected)
    M = fit_color_matrix(measured, reference)
    out = apply_matrix(img_illum_corrected, M)
    after = measure_patches(out)
    err = float(np.mean(delta_e(linear_to_lab(after), linear_to_lab(reference))))
    return out, M, err
