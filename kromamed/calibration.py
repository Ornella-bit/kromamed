"""
Contrôle de la lumière et du contraste (feuille de route §4, étape 3).

IMPORTANT (leçon d'un test sur une vraie carte imprimée) : les couleurs imprimées par une imprimante de
bureau sont très différentes des couleurs « idéales » (un vert sort 4 fois plus sombre, les gris ont une
teinte). Forcer ces couleurs à leurs valeurs idéales déformait toute l'image. La référence fiable est le
PAPIER BLANC (déjà utilisé par illumination.py : le papier devient blanc partout, ce qui corrige aussi la
teinte de la lumière). Ici, on ne fait que CONTRÔLER la capture avec des critères qui ne dépendent pas
de l'imprimante : contraste noir/blanc, dominante de couleur, ordre des gris.
Les anciennes fonctions d'ajustement par matrice 3x3 sont conservées plus bas pour les essais en laboratoire.

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



# ---------------------------------------------------------------------------
# Contrôles utilisés par le pipeline
# ---------------------------------------------------------------------------
_LUM = np.array([0.2126, 0.7152, 0.0722], np.float32)


def _clip01(x: float) -> float:
    return float(min(1.0, max(0.0, x)))


def assess(raw_warped: np.ndarray, corrected: np.ndarray, paper: np.ndarray) -> dict:
    """3 contrôles, chacun noté de 0 à 1 ; la note globale est la plus basse.

    contrast : rapport blanc/noir des 4 repères (photo délavée, reflet, flou -> note basse)
    cast     : dominante de couleur du papier AVANT correction (lumière très colorée -> note basse)
    order    : les 5 gris imprimés doivent rester du plus clair au plus foncé (exposition aberrante -> basse)
    """
    lum = raw_warped @ _LUM
    vals = np.concatenate([lum[y:y + C.MARKER_SIZE, x:x + C.MARKER_SIZE].ravel() for x, y in C.MARKERS.values()])
    black, white = max(float(np.percentile(vals, 5)), 1e-4), float(np.percentile(vals, 95))
    contrast = white / black
    s_contrast = _clip01((np.log10(contrast) - 0.7) / 0.5)          # 5:1 -> 0 ; 16:1 et plus -> 1

    paper_rgb = raw_warped[paper].mean(axis=0)
    cast = float(paper_rgb.max() / max(float(paper_rgb.min()), 1e-4))
    s_cast = _clip01((3.0 - cast) / 1.2)                              # 1,8 et moins -> 1 ; 3,0 -> 0

    grays = [float(_patch_median(corrected, C.patch_rect(i)) @ _LUM) for i in range(5)]
    ratios = [grays[i] / max(grays[i + 1], 1e-4) for i in range(4)]
    s_order = _clip01((min(ratios) - 1.05) / 0.25)                    # 1,3 et plus -> 1 ; 1,05 -> 0

    return {"score": min(s_contrast, s_cast, s_order), "contrast": contrast, "cast": cast, "min_gray_ratio": min(ratios),
            "scores": {"contrast": s_contrast, "cast": s_cast, "order": s_order}}


def strip_score(pad_lab: np.ndarray) -> tuple[float, int]:
    """Y a-t-il une bandelette ? Au moins 4 plages doivent différer nettement du papier blanc (ΔE >= 12).
    Une carte vide donne 0 : on refuse plutôt que de « lire » du papier."""
    white = np.array([100.0, 0.0, 0.0], np.float32)
    n = int(sum(float(delta_e(lab, white)) >= 12.0 for lab in pad_lab))
    return _clip01((n - 2) / 2.0), n
