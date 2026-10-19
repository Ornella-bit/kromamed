"""
Dessin sur image décimale (float32), compatible OpenCV 4 et 5.

OpenCV 5 n'accepte de dessiner texte et formes que sur des images 8 bits.
On dessine donc sur un masque 8 bits (0..255), puis on le fusionne dans l'image.
"""
from __future__ import annotations
from typing import Callable
import numpy as np


def paint(img: np.ndarray, draw: Callable[[np.ndarray], None], color) -> None:
    """Applique `draw(masque_uint8)` puis colore en `color` les pixels dessinés (in place)."""
    mask = np.zeros(img.shape[:2], np.uint8)
    draw(mask)
    alpha = (mask.astype(np.float32) / 255.0)[..., None]
    img[:] = img * (1.0 - alpha) + np.asarray(color, np.float32) * alpha
