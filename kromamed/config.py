"""
Configuration centrale : la géométrie de la carte d'étalonnage et la table
de référence des couleurs de la bandelette.

Tout est exprimé en "unités canoniques" : la carte redressée fait
CARD_W x CARD_H pixels. Le même plan sert à imprimer la carte
(scripts/make_card.py), à simuler des photos (scripts/simulate.py)
et à lire les zones dans l'image réelle (pipeline).
Si on change la carte imprimée, on ne modifie QUE ce fichier.
"""
from __future__ import annotations
import cv2

# --- Carte --------------------------------------------------------------
CARD_W, CARD_H = 600, 900
ARUCO_DICT = cv2.aruco.DICT_4X4_50
MARKER_SIZE = 90
MARGIN = 20

# Position (x, y) du coin haut-gauche de chaque marqueur + son identifiant.
# Ordre des ids : 0 haut-gauche, 1 haut-droit, 2 bas-droit, 3 bas-gauche.
MARKERS = {
    0: (MARGIN, MARGIN),
    1: (CARD_W - MARGIN - MARKER_SIZE, MARGIN),
    2: (CARD_W - MARGIN - MARKER_SIZE, CARD_H - MARGIN - MARKER_SIZE),
    3: (MARGIN, CARD_H - MARGIN - MARKER_SIZE),
}

# --- Patchs de référence ------------------------------------------------
# Réflectance en RGB LINÉAIRE, relative au papier blanc (papier = 1.0).
# Ils servent à calculer la matrice de correction des couleurs.
# NB : à remplacer par des valeurs mesurées sur la carte réellement imprimée.
PATCH_W, PATCH_H = 90, 60
PATCH_X0, PATCH_STEP = 40, 110
PATCH_ROWS_Y = (130, 200)
PATCHES = [
    # ligne 1 : gris
    ("gris_70", (0.70, 0.70, 0.70)),
    ("gris_45", (0.45, 0.45, 0.45)),
    ("gris_25", (0.25, 0.25, 0.25)),
    ("gris_10", (0.10, 0.10, 0.10)),
    ("gris_03", (0.03, 0.03, 0.03)),
    # ligne 2 : couleurs
    ("rouge", (0.60, 0.05, 0.05)),
    ("vert", (0.05, 0.50, 0.08)),
    ("bleu", (0.05, 0.08, 0.55)),
    ("jaune", (0.75, 0.65, 0.05)),
    ("cyan", (0.05, 0.55, 0.60)),
]


def patch_rect(index: int) -> tuple[int, int, int, int]:
    """Rectangle (x, y, w, h) du patch n° index dans la carte canonique."""
    row, col = divmod(index, 5)
    return (PATCH_X0 + col * PATCH_STEP, PATCH_ROWS_Y[row], PATCH_W, PATCH_H)


# --- Bandelette ---------------------------------------------------------
STRIP_BODY = (250, 280, 100, 456)          # x, y, w, h  (plastique)
STRIP_BODY_COLOR = (0.85, 0.85, 0.85)      # réflectance linéaire
PAD_W, PAD_H, PAD_GAP = 60, 44, 18
PAD_X = 270
PAD_Y0 = 300

# Ordre des plages réactives sur la bandelette (haut -> bas)
PARAMS = ["leucocytes", "nitrites", "ph", "proteines", "glucose", "cetones", "sang"]


def pad_rect(index: int) -> tuple[int, int, int, int]:
    return (PAD_X, PAD_Y0 + index * (PAD_H + PAD_GAP), PAD_W, PAD_H)


# --- Table de référence des couleurs ------------------------------------
# sRGB hexadécimal par niveau. VALEURS DE DÉMONSTRATION : approximatives,
# inspirées des teintes courantes des bandelettes urinaires.
# En production : remplacer par la table du fabricant de la bandelette
# (ou par des mesures de la Phase 3) - c'est la seule chose à changer.
REFERENCE_TABLE = {
    "leucocytes": [("négatif", "#E9E3C0"), ("traces", "#D9CBC0"),
                   ("+", "#C7A9C0"), ("++", "#A97FAE"), ("+++", "#7F4F8F")],
    "nitrites":   [("négatif", "#F1ECDD"), ("positif", "#EBA0B4")],
    "ph":         [("5,0", "#E8A24A"), ("6,0", "#D9B84F"), ("6,5", "#B8BE52"),
                   ("7,0", "#8CB468"), ("8,0", "#5FA88A"), ("9,0", "#4B8FA6")],
    "proteines":  [("négatif", "#E3E49A"), ("traces", "#C9D9A0"),
                   ("+", "#A9CFA6"), ("++", "#7FBFAF"), ("+++", "#4FA9B5")],
    "glucose":    [("négatif", "#9CC4D8"), ("+", "#8FB59B"),
                   ("++", "#B59A58"), ("+++", "#8A5A3A")],
    "cetones":    [("négatif", "#EDD9C3"), ("traces", "#E5BBB4"),
                   ("+", "#D08CA2"), ("++", "#9E5A86")],
    "sang":       [("négatif", "#E6D77A"), ("traces", "#BCCB72"),
                   ("+", "#8DBA70"), ("++", "#5FA575"), ("+++", "#2F7F66")],
}

# Niveaux considérés normaux, pour le verdict global.
NORMAL_LEVELS = {
    "leucocytes": {"négatif"}, "nitrites": {"négatif"},
    "ph": {"5,0", "6,0", "6,5", "7,0", "8,0"},
    "proteines": {"négatif"}, "glucose": {"négatif"},
    "cetones": {"négatif"}, "sang": {"négatif"},
}

# --- Seuils -------------------------------------------------------------
MIN_QUALITY = 0.85          # sous ce seuil : refus d'analyser (feuille de route §8)
MAX_PAD_DELTA_E = 12.0      # couleur trop loin de toute référence -> "indéterminé"
MIN_PAD_MARGIN = 0.15       # marge entre 1er et 2e voisin (sinon confiance faible)
KNN_K = 1
