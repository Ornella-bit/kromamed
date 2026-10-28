"""
Simulateur de photos : fabrique de FAUSSES photos réalistes de la carte
+ bandelette, avec éclairage inégal, ombre, lumière colorée, perspective,
bruit et flou. Sert à tester le moteur sans photos réelles et à mesurer
sa robustesse (Phase 1 demande 100 photos de test : voir scripts/benchmark.py).

IMPORTANT : une simulation prouve que le code est cohérent, PAS que la
méthode marche en conditions réelles. La validation sur de vraies photos
reste à faire (Phases 3 et 4).
"""
from __future__ import annotations
import cv2
import numpy as np

from . import config as C
from .card import render_card
from .drawing import paint
from .color import linear_to_srgb


def random_levels(rng: np.random.Generator) -> dict[str, str]:
    return {p: C.REFERENCE_TABLE[p][rng.integers(len(C.REFERENCE_TABLE[p]))][0] for p in C.PARAMS}


def simulate_photo(levels: dict[str, str] | None = None, seed: int = 0, *,
                   blur_sigma: float = 0.0, shadow: float = 0.08,
                   warm: float = 0.25, tilt: float = 1.0,
                   hide_marker: int | None = None, with_strip: bool = True, scene=(1200, 1500)) -> np.ndarray:
    """Retourne une photo BGR uint8."""
    rng = np.random.default_rng(seed)
    S = 2  # rendu 2x pour des bords nets
    card = render_card(levels, with_strip=with_strip)
    card = cv2.resize(card, None, fx=S, fy=S, interpolation=cv2.INTER_NEAREST)
    H, W = card.shape[:2]

    # --- éclairage dans le plan de la carte --------------------------------
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    xn, yn = xx / W - 0.5, yy / H - 0.5
    a, b, c = rng.uniform(-0.25, 0.25), rng.uniform(-0.25, 0.25), rng.uniform(-0.2, 0.2)
    light = 0.78 * (1 + a * xn + b * yn + c * xn * yn)
    if shadow > 0:
        cx, cy = rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3)
        light *= 1 - shadow * np.exp(-((xn - cx) ** 2 + (yn - cy) ** 2) / (2 * 0.15 ** 2))
    cast = np.array([1.0, 1.0 - 0.3 * warm * rng.uniform(0.6, 1.0), 1.0 - 0.9 * warm * rng.uniform(0.6, 1.0)])
    img = card * light[..., None] * cast

    # mélange de canaux de la caméra (diaphonie)
    cam = np.array([[0.96, 0.025, 0.015], [0.02, 0.96, 0.02], [0.01, 0.03, 0.96]], np.float32)   # un téléphone renvoie déjà des couleurs proches de sRGB
    img = (img @ cam.T).astype(np.float32)

    # --- placement en perspective dans la scène ----------------------------
    sw, sh = scene
    src = np.float32([[0, 0], [W, 0], [W, H], [0, H]])
    base = np.float32([[200, 150], [1000, 150], [1000, 1350], [200, 1350]])
    jitter = rng.uniform(-60, 60, (4, 2)).astype(np.float32) * tilt
    dst = base + jitter
    Hm = cv2.getPerspectiveTransform(src, dst)
    bg = np.full((sh, sw, 3), 0.10, np.float32) * (1 + 0.3 * rng.random())
    warped = cv2.warpPerspective(img, Hm, (sw, sh), flags=cv2.INTER_LINEAR)
    mask = cv2.warpPerspective(np.ones((H, W), np.float32), Hm, (sw, sh), flags=cv2.INTER_LINEAR)
    scene_img = bg * (1 - mask[..., None]) + warped * mask[..., None]

    if hide_marker is not None:                      # simule un doigt sur un repère
        x, y = C.MARKERS[hide_marker]
        pts = cv2.perspectiveTransform(
            np.float32([[[x * S, y * S], [(x + C.MARKER_SIZE) * S, (y + C.MARKER_SIZE) * S]]]), Hm)[0]
        p1, p2 = pts.astype(int)
        paint(scene_img, lambda m: cv2.rectangle(m, tuple(int(v) for v in p1 - 15), tuple(int(v) for v in p2 + 15), 255, -1),
              (0.45, 0.3, 0.25))

    if blur_sigma > 0:
        scene_img = cv2.GaussianBlur(scene_img, (0, 0), blur_sigma)
    scene_img = scene_img + rng.normal(0, 0.004, scene_img.shape).astype(np.float32)

    srgb = linear_to_srgb(np.clip(scene_img, 0, 1))
    return cv2.cvtColor((srgb * 255 + 0.5).astype(np.uint8), cv2.COLOR_RGB2BGR)
