"""
Configuration centrale : géométrie de la carte d'étalonnage, bandelette
Multistix 10 SG (10 paramètres) et table de référence des couleurs.

Tout est exprimé en "unités canoniques" : la carte redressée fait
CARD_W x CARD_H pixels, avec PX_PER_MM pixels par millimètre
(600 x 900 px = carte imprimée de 150 x 225 mm).
Le même plan sert à imprimer la carte (scripts/make_card.py), à simuler des
photos (kromamed/simulate.py) et à lire les zones dans l'image (pipeline).
Si on change la carte ou la bandelette, on ne modifie QUE ce fichier.
"""
from __future__ import annotations
import cv2

BRAND = "Siemens Multistix 10 SG"
PX_PER_MM = 4

# --- Carte --------------------------------------------------------------
CARD_W, CARD_H = 600, 900                  # = 150 x 225 mm
ARUCO_DICT = cv2.aruco.DICT_4X4_50
MARKER_SIZE = 90                           # 22,5 mm
MARGIN = 20

# Coin haut-gauche de chaque marqueur. Ids : 0 haut-gauche, 1 haut-droit,
# 2 bas-droit, 3 bas-gauche.
MARKERS = {
    0: (MARGIN, MARGIN),
    1: (CARD_W - MARGIN - MARKER_SIZE, MARGIN),
    2: (CARD_W - MARGIN - MARKER_SIZE, CARD_H - MARGIN - MARKER_SIZE),
    3: (MARGIN, CARD_H - MARGIN - MARKER_SIZE),
}

# Zones de texte imprimées (exclues de la mesure d'éclairage)
TITLE_RECT = (130, 30, 340, 60)            # x, y, w, h
LABELS_RECT = (312, 266, 170, 392)

# --- Patchs de référence ------------------------------------------------
# Réflectance en RGB LINÉAIRE, relative au papier blanc (papier = 1.0).
# NB : à remplacer par des valeurs mesurées sur la carte réellement imprimée.
PATCH_W, PATCH_H = 90, 60
PATCH_X0, PATCH_STEP = 40, 110
PATCH_ROWS_Y = (130, 200)
PATCHES = [
    ("gris_70", (0.70, 0.70, 0.70)),
    ("gris_45", (0.45, 0.45, 0.45)),
    ("gris_25", (0.25, 0.25, 0.25)),
    ("gris_10", (0.10, 0.10, 0.10)),
    ("gris_03", (0.03, 0.03, 0.03)),
    ("rouge", (0.60, 0.05, 0.05)),
    ("vert", (0.05, 0.50, 0.08)),
    ("bleu", (0.05, 0.08, 0.55)),
    ("jaune", (0.75, 0.65, 0.05)),
    ("cyan", (0.05, 0.55, 0.60)),
]


def patch_rect(index: int) -> tuple[int, int, int, int]:
    row, col = divmod(index, 5)
    return (PATCH_X0 + col * PATCH_STEP, PATCH_ROWS_Y[row], PATCH_W, PATCH_H)


# --- Bandelette Multistix 10 SG ------------------------------------------
# DIMENSIONS ESTIMÉES : à remplacer par les mesures de VOTRE bandelette
# (largeur, longueur, distance pointe -> 1re plage, écart entre plages, taille d'une plage).
STRIP_W_MM = 5.5
STRIP_LEN_MM = 95.0
PAD_SIZE_MM = 4.5
PAD_PITCH_MM = 7.0
FIRST_PAD_MM = 8.0           # de la pointe (haut) au CENTRE de la 1re plage
STRIP_TOP_Y = 272            # position verticale de la pointe sur la carte

STRIP_BODY_COLOR = (0.85, 0.85, 0.85)
_S = PX_PER_MM
STRIP_BODY = (CARD_W // 2 - int(STRIP_W_MM * _S / 2), STRIP_TOP_Y,
              int(STRIP_W_MM * _S), int(STRIP_LEN_MM * _S))

# Ordre des plages, de la POINTE (haut) vers la poignée (bas) : ordre de
# l'étiquette Multistix 10 SG. À VÉRIFIER avec le tableau de couleurs de votre flacon.
PARAMS = ["leucocytes", "nitrites", "urobilinogene", "proteines", "ph",
          "sang", "densite", "cetones", "bilirubine", "glucose"]

LABELS_FR = {
    "leucocytes": "Leucocytes", "nitrites": "Nitrites", "urobilinogene": "Urobilinogène",
    "proteines": "Protéines", "ph": "pH", "sang": "Sang", "densite": "Densité",
    "cetones": "Cétones", "bilirubine": "Bilirubine", "glucose": "Glucose",
}

# Temps de lecture du fabricant (secondes) - notice Multistix 10 SG
READ_TIME_S = {
    "glucose": 30, "bilirubine": 30, "cetones": 40, "densite": 45,
    "sang": 60, "ph": 60, "proteines": 60, "urobilinogene": 60,
    "nitrites": 60, "leucocytes": 120,
}


def pad_rect(index: int) -> tuple[int, int, int, int]:
    size = int(PAD_SIZE_MM * _S)
    cx = CARD_W // 2
    cy = STRIP_TOP_Y + int((FIRST_PAD_MM + index * PAD_PITCH_MM) * _S)
    return (cx - size // 2, cy - size // 2, size, size)


# --- Table de référence des couleurs ------------------------------------
# sRGB hexadécimal par niveau. VALEURS DE DÉMONSTRATION (approximatives).
# En production : remplacer par la table du fabricant ou des mesures (Phase 3).
REFERENCE_TABLE = {
    "leucocytes": [("négatif", "#E9E3C0"), ("traces", "#D9CBC0"),
                   ("+", "#C7A9C0"), ("++", "#A97FAE"), ("+++", "#7F4F8F")],
    "nitrites":   [("négatif", "#F1ECDD"), ("positif", "#EBA0B4")],
    "urobilinogene": [("normal", "#F2C9A0"), ("+", "#EFA98A"),
                      ("++", "#E58A78"), ("+++", "#D86A66")],
    "proteines":  [("négatif", "#E3E49A"), ("traces", "#C9D9A0"),
                   ("+", "#A9CFA6"), ("++", "#7FBFAF"), ("+++", "#4FA9B5")],
    "ph":         [("5,0", "#E8A24A"), ("6,0", "#D9B84F"), ("6,5", "#B8BE52"),
                   ("7,0", "#8CB468"), ("8,0", "#5FA88A"), ("8,5", "#4B8FA6")],
    "sang":       [("négatif", "#E6D77A"), ("traces", "#BCCB72"),
                   ("+", "#8DBA70"), ("++", "#5FA575"), ("+++", "#2F7F66")],
    "densite":    [("1,000", "#219AA3"), ("1,005", "#59A099"), ("1,010", "#79A78E"),
                   ("1,015", "#93AE83"), ("1,020", "#ABB477"), ("1,025", "#C0BB6B"),
                   ("1,030", "#D4C25D")],
    "cetones":    [("négatif", "#EDD9C3"), ("traces", "#E5BBB4"),
                   ("+", "#D08CA2"), ("++", "#9E5A86")],
    "bilirubine": [("négatif", "#F1E6D0"), ("+", "#E4CBA6"),
                   ("++", "#D2AE8E"), ("+++", "#B98770")],
    "glucose":    [("négatif", "#9CC4D8"), ("+", "#8FB59B"),
                   ("++", "#B59A58"), ("+++", "#8A5A3A")],
}

# Niveaux considérés normaux, pour le verdict global.
NORMAL_LEVELS = {
    "leucocytes": {"négatif"}, "nitrites": {"négatif"}, "urobilinogene": {"normal"},
    "proteines": {"négatif"}, "ph": {"5,0", "6,0", "6,5", "7,0", "8,0"},
    "sang": {"négatif"}, "densite": {"1,005", "1,010", "1,015", "1,020", "1,025", "1,030"},
    "cetones": {"négatif"}, "bilirubine": {"négatif"}, "glucose": {"négatif"},
}

# Un résultat "tout normal" type (démos, tests, exemples)
NORMAL_DEFAULT = {
    "leucocytes": "négatif", "nitrites": "négatif", "urobilinogene": "normal",
    "proteines": "négatif", "ph": "6,0", "sang": "négatif", "densite": "1,015",
    "cetones": "négatif", "bilirubine": "négatif", "glucose": "négatif",
}

# --- Seuils -------------------------------------------------------------
MIN_QUALITY = 0.85          # sous ce seuil : refus d'analyser
MAX_PAD_DELTA_E = 12.0      # couleur trop loin de toute référence -> "indéterminé"
MIN_PAD_MARGIN = 0.15       # marge entre 1er et 2e voisin
KNN_K = 1
