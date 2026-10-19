"""
Carte d'étalonnage : rendu (pour imprimer / simuler) + détection + redressement.

Rendu    : render_card()   -> image RGB linéaire canonique
Détection: find_markers()  -> coins des 4 marqueurs ArUco dans la photo
Redress. : rectify()       -> carte vue "de face" en CARD_W x CARD_H
"""
from __future__ import annotations
import cv2
import numpy as np

from . import config as C
from .color import hex_to_srgb, srgb_to_linear


# ---------------------------------------------------------------- rendu --
def _aruco_dictionary():
    return cv2.aruco.getPredefinedDictionary(C.ARUCO_DICT)


def render_card(levels: dict[str, str] | None = None, with_strip: bool = True) -> np.ndarray:
    """Carte canonique en RGB linéaire float32 (papier = 1.0).

    levels : niveau de chaque paramètre à peindre sur la bandelette
             (sert à la simulation ; ex. {"proteines": "++"}). Par défaut "négatif"
             (ou la 1re valeur pour le pH).
    """
    img = np.ones((C.CARD_H, C.CARD_W, 3), np.float32)

    # marqueurs ArUco (noir/blanc = 0.02/1.0 en linéaire)
    d = _aruco_dictionary()
    for mid, (x, y) in C.MARKERS.items():
        m = cv2.aruco.generateImageMarker(d, mid, C.MARKER_SIZE).astype(np.float32) / 255.0
        m = 0.02 + 0.98 * m
        img[y:y + C.MARKER_SIZE, x:x + C.MARKER_SIZE] = m[..., None]

    # patchs de référence
    for i, (_, rgb) in enumerate(C.PATCHES):
        x, y, w, h = C.patch_rect(i)
        img[y:y + h, x:x + w] = rgb

    if with_strip:
        x, y, w, h = C.STRIP_BODY
        img[y:y + h, x:x + w] = C.STRIP_BODY_COLOR
        levels = levels or {}
        for i, param in enumerate(C.PARAMS):
            table = dict(C.REFERENCE_TABLE[param])
            hexcode = table.get(levels.get(param, ""), C.REFERENCE_TABLE[param][0][1])
            rgb_lin = srgb_to_linear(hex_to_srgb(hexcode))
            px, py, pw, ph = C.pad_rect(i)
            img[py:py + ph, px:px + pw] = rgb_lin
    return img


def paper_mask() -> np.ndarray:
    """Masque booléen (CARD_H x CARD_W) des zones de papier blanc nu
    (hors marqueurs, patchs, bandelette) : sert à mesurer l'éclairage."""
    mask = np.ones((C.CARD_H, C.CARD_W), bool)
    pad = 12  # marge de sécurité autour des éléments imprimés
    mask[:C.MARGIN + pad, :] = False
    mask[-(C.MARGIN + pad):, :] = False
    mask[:, :C.MARGIN + pad] = False
    mask[:, -(C.MARGIN + pad):] = False
    for x, y in C.MARKERS.values():
        mask[y - pad:y + C.MARKER_SIZE + pad, x - pad:x + C.MARKER_SIZE + pad] = False
    for i in range(len(C.PATCHES)):
        x, y, w, h = C.patch_rect(i)
        mask[y - pad:y + h + pad, x - pad:x + w + pad] = False
    x, y, w, h = C.STRIP_BODY
    mask[y - pad:y + h + pad, x - pad:x + w + pad] = False
    return mask


# ------------------------------------------------------------ détection --
def find_markers(image_bgr: np.ndarray) -> dict[int, np.ndarray]:
    """Retourne {id: coins (4x2)} pour les marqueurs de la carte détectés."""
    detector = cv2.aruco.ArucoDetector(_aruco_dictionary(), cv2.aruco.DetectorParameters())
    corners, ids, _ = detector.detectMarkers(image_bgr)
    found: dict[int, np.ndarray] = {}
    if ids is not None:
        for c, i in zip(corners, ids.flatten()):
            if int(i) in C.MARKERS:
                found[int(i)] = c.reshape(4, 2)
    return found


def rectify(image: np.ndarray, markers: dict[int, np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    """Redresse la carte par homographie (transformation perspective 3x3).

    On associe les 16 coins détectés (4 par marqueur) à leurs positions
    théoriques dans la carte canonique ; OpenCV (RANSAC) en déduit la
    matrice H. Retourne (carte_redressée, H).
    """
    src, dst = [], []
    for mid, corners in markers.items():
        x, y = C.MARKERS[mid]
        s = C.MARKER_SIZE
        canon = np.array([[x, y], [x + s, y], [x + s, y + s], [x, y + s]], np.float32)
        src.append(corners)
        dst.append(canon)
    src, dst = np.concatenate(src).astype(np.float32), np.concatenate(dst)
    H, _ = cv2.findHomography(src, dst, cv2.RANSAC, 3.0)
    if H is None:
        raise ValueError("Homographie impossible")
    warped = cv2.warpPerspective(image, H, (C.CARD_W, C.CARD_H), flags=cv2.INTER_LINEAR)
    return warped, H
