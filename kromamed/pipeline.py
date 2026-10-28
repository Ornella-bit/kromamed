"""
Pipeline complet : photo -> contrôle qualité -> résultat (feuille de route §2).

    1. Capture        détection des 4 marqueurs + redressement (homographie)
    2. Normalisation  correction d'éclairage + étalonnage des couleurs
    3. Extraction     mesure de la couleur de chaque plage réactive (ROI)
    4. Classification KNN en L*a*b* -> niveau par paramètre

Si la qualité est < 85 %, on s'arrête et on demande une nouvelle photo.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import time
import unicodedata

import cv2
import numpy as np

from . import config as C
from . import card, illumination, calibration, quality
from .color import srgb_to_linear, linear_to_srgb, linear_to_lab
from .interpreter import BiomedicalInterpreter, PadResult

_INTERPRETER = BiomedicalInterpreter()


@dataclass
class AnalysisResult:
    status: str                              # "ok" | "rejected"
    quality: quality.QualityReport
    pads: list[PadResult] = field(default_factory=list)
    all_normal: bool | None = None
    duration_ms: float = 0.0
    debug: dict[str, np.ndarray] = field(default_factory=dict, repr=False)

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "quality": self.quality.to_dict(),
            "all_normal": self.all_normal,
            "duration_ms": round(self.duration_ms, 1),
            "pads": [
                {"param": p.param, "level": p.level, "status": p.status,
                 "delta_e": round(p.delta_e, 2), "confidence": round(p.confidence, 2),
                 "normal": p.normal, "lab": p.lab, "candidates": p.candidates}
                for p in self.pads
            ],
        }


def _ascii(text: str) -> str:
    """OpenCV ne dessine pas les accents : on les retire pour l'image annotée."""
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()


def _to_bgr8(rgb_lin: np.ndarray) -> np.ndarray:
    srgb = linear_to_srgb(np.clip(rgb_lin, 0, 1))
    return cv2.cvtColor((srgb * 255).astype(np.uint8), cv2.COLOR_RGB2BGR)


def _reject(markers_score: float, reasons: list[str] | None = None, t0: float = 0.0) -> AnalysisResult:
    q = quality.combine(markers_score, 0.0, 0.0, 0.0, 0.0)
    if reasons:
        q.reasons = reasons
    return AnalysisResult("rejected", q, duration_ms=(time.perf_counter() - t0) * 1000)


def analyze(image: np.ndarray | str | Path, keep_debug: bool = False, require_strip: bool = True) -> AnalysisResult:
    """Analyse une photo (tableau BGR uint8 ou chemin de fichier).

    require_strip=False : mode « photo de test » (carte seule, sans bandelette) pour régler la caméra."""
    t0 = time.perf_counter()
    if not isinstance(image, np.ndarray):
        image = cv2.imread(str(image))
        if image is None:
            raise FileNotFoundError("Image illisible")

    # --- 1. Capture ------------------------------------------------------
    markers = card.find_markers(image)
    if len(markers) < 4:
        return _reject(len(markers) / 4.0, t0=t0)

    rgb_lin = srgb_to_linear(cv2.cvtColor(image, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0)
    warped, _ = card.rectify(rgb_lin, markers)
    paper = card.paper_mask()

    # --- 2. Normalisation : le papier blanc est la référence (lumière + teinte) ----
    corrected, surface = illumination.correct_illumination(warped, paper)
    calibrated = corrected
    cal = calibration.assess(warped, corrected, paper)

    # --- 3. Lecture des plages (avant le contrôle qualité : on vérifie la présence de la bandelette)
    pad_rgb = [calibration._patch_median(calibrated, C.pad_rect(i), shrink=0.7) for i in range(len(C.PARAMS))]
    pad_lab = [linear_to_lab(rgb.reshape(1, 3)).reshape(3) for rgb in pad_rgb]
    strip_s, _n = calibration.strip_score(pad_lab) if require_strip else (1.0, len(pad_lab))

    # --- qualité ---------------------------------------------------------
    warped_srgb = linear_to_srgb(warped)
    gray255 = (warped_srgb.mean(axis=-1) * 255.0).astype(np.float32)
    sharp, sharp_raw = quality.sharpness_score(gray255)
    report = quality.combine(
        markers=1.0,
        sharp=sharp,
        expo=quality.exposure_score(warped_srgb, paper),
        illum=min(quality.illumination_score(surface, paper),
                  quality.residual_score(illumination.fit_residual(warped, surface, paper))),
        calib=cal["score"],
        strip=strip_s,
    )

    debug = {}
    if keep_debug:
        debug["card_raw"] = _to_bgr8(warped)
        debug["card_corrected"] = _to_bgr8(calibrated)

    if report.overall < C.MIN_QUALITY:
        return AnalysisResult("rejected", report,
                              duration_ms=(time.perf_counter() - t0) * 1000, debug=debug)

    # --- 4. Classification ------------------------------------------------
    pads: list[PadResult] = [_INTERPRETER.classify(param, pad_lab[i]) for i, param in enumerate(C.PARAMS)]

    decided = [p for p in pads if p.status == "ok"]
    all_normal = (all(p.normal for p in decided) if len(decided) == len(pads) else None)

    if keep_debug:
        overlay = debug["card_corrected"].copy()
        for i, p in enumerate(pads):
            x, y, w, h = C.pad_rect(i)
            col = (80, 160, 40) if p.normal else ((60, 60, 220) if p.normal is False else (0, 160, 255))
            cv2.rectangle(overlay, (x, y), (x + w, y + h), col, 2)
            cv2.putText(overlay, _ascii(f"{p.param}: {p.level or '?'}"), (x + w + 10, y + h // 2 + 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (30, 30, 30), 1, cv2.LINE_AA)
        debug["card_result"] = overlay

    return AnalysisResult("ok", report, pads, all_normal,
                          (time.perf_counter() - t0) * 1000, debug)
