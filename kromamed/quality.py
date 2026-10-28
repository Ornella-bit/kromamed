"""
Contrôle qualité de la capture (feuille de route §8 : seuil de sécurité 85 %).

Chaque critère donne un score 0..1. Le score global est le MINIMUM des
critères : un seul point faible suffit à refuser. L'application ne rend
jamais un résultat incertain.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import cv2
import numpy as np

from . import config as C


@dataclass
class QualityReport:
    markers: float        # 4 marqueurs détectés ?
    sharpness: float      # netteté (variance du Laplacien sur les marqueurs)
    exposure: float       # pas de zones brûlées / trop sombres
    illumination: float   # inégalité d'éclairage raisonnable
    calibration: float    # contraste, dominante de couleur et ordre des gris (voir calibration.assess)
    strip: float          # bandelette présente dans la fente ?
    overall: float
    reasons: list[str]

    def to_dict(self) -> dict:
        return {k: (round(v, 3) if isinstance(v, float) else v) for k, v in asdict(self).items()}


def _clip01(x: float) -> float:
    return float(min(1.0, max(0.0, x)))


# Valeurs trouvées sur des images SIMULÉES (photo nette ≈ 2600-3300 ; léger flou
# σ=0,5 px ≈ 2000 ; flou σ=1 px ≈ 1000 ; σ=2 px ≈ 400). Plein score à SHARP_OK,
# score nul à SHARP_BAD. À RECALIBRER avec de vraies photos de téléphones (Phase 2/3).
SHARP_OK, SHARP_BAD = 1800.0, 500.0


def sharpness_score(warped_srgb_gray: np.ndarray) -> tuple[float, float]:
    """Variance du Laplacien mesurée sur les 4 marqueurs de la carte redressée.
    (Même contenu à chaque fois -> la mesure est comparable d'une photo à l'autre.)"""
    vals = []
    for x, y in C.MARKERS.values():
        roi = warped_srgb_gray[y:y + C.MARKER_SIZE, x:x + C.MARKER_SIZE]
        vals.append(cv2.Laplacian(roi, cv2.CV_32F).var())
    v = float(np.mean(vals))
    return _clip01((v - SHARP_BAD) / (SHARP_OK - SHARP_BAD)), v


def exposure_score(warped_raw_srgb: np.ndarray, paper: np.ndarray) -> float:
    """Part de pixels de papier saturés (>0.98) ou très sombres (<0.15)."""
    lum = warped_raw_srgb[paper].mean(axis=-1)
    bad = float(np.mean((lum > 0.98) | (lum < 0.15)))
    return _clip01(1.0 - bad * 4.0)


def illumination_score(surface: np.ndarray, paper: np.ndarray) -> float:
    """Rapport entre zone sombre (5e centile) et claire (95e) de l'éclairage."""
    lum = surface.mean(axis=-1)[paper]
    r = float(np.percentile(lum, 5) / np.percentile(lum, 95))
    return _clip01((r - 0.35) / 0.30)


def residual_score(std: float) -> float:
    """Éclairage lisse (écart-type <= 0,025) -> 1.0 ; ombre nette (>= 0,05) -> 0.0.
    Mesuré : photos normales <= 0,02 ; vraie carte imprimée 0,010."""
    return _clip01((0.05 - std) / 0.025)


def calibration_score(mean_delta_e: float) -> float:
    """ΔE moyen ≤ 2 -> 1.0 ; ΔE ≥ 10 -> 0.0."""
    return _clip01(1.0 - (mean_delta_e - 2.0) / 8.0)


def combine(markers: float, sharp: float, expo: float, illum: float, calib: float, strip: float = 1.0) -> QualityReport:
    scores = dict(markers=markers, sharpness=sharp, exposure=expo,
                  illumination=illum, calibration=calib, strip=strip)
    messages = {
        "markers": "Les 4 repères de la carte ne sont pas tous visibles : recentrer la carte.",
        "sharpness": "Image floue : stabiliser le téléphone.",
        "exposure": "Éclairage trop fort ou trop faible : changer d'endroit.",
        "illumination": "Éclairage trop inégal (ombre) : éviter les ombres sur la carte.",
        "calibration": "Photo délavée ou lumière trop colorée : refaire la photo à la lumière du jour.",
        "strip": "Aucune bandelette détectée : posez la bandelette dans la fente de la carte.",
    }
    overall = min(scores.values())
    reasons = [messages[k] for k, v in scores.items() if v < C.MIN_QUALITY]
    return QualityReport(**scores, overall=overall, reasons=reasons)
