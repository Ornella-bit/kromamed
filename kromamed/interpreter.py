"""
Interprétation biomédicale (feuille de route §5, BiomedicalInterpreter) :
transforme une couleur L*a*b* mesurée sur une plage en niveau (négatif, +, ++ ...).

Méthode : k plus proches voisins (KNN) dans l'espace L*a*b*, contre la table
de référence (config.REFERENCE_TABLE). Avec k=1 et un seul prototype par niveau,
c'est une "couleur la plus proche". En Phase 3, on ajoutera des échantillons
mesurés sous différentes lumières : le même code les utilisera sans changement.

Règle de sécurité : si la couleur est trop loin de toute référence, ou si deux
niveaux sont presque aussi proches l'un que l'autre, on NE tranche PAS.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np

from . import config as C
from .color import hex_to_srgb, srgb_to_lab, delta_e


@dataclass
class PadResult:
    param: str
    level: str | None            # None si indéterminé
    status: str                  # "ok" | "indéterminé"
    delta_e: float               # distance au niveau le plus proche
    confidence: float            # 0..1
    lab: list[float]
    normal: bool | None = None
    candidates: list[str] = field(default_factory=list)


class BiomedicalInterpreter:
    def __init__(self, table: dict | None = None, k: int = C.KNN_K):
        self.k = k
        self.samples: dict[str, list[tuple[str, np.ndarray]]] = {}
        for param, levels in (table or C.REFERENCE_TABLE).items():
            self.samples[param] = [(lvl, srgb_to_lab(hex_to_srgb(code))) for lvl, code in levels]

    def add_sample(self, param: str, level: str, lab: np.ndarray) -> None:
        """Ajoute un échantillon mesuré (Phase 3 : entraînement)."""
        self.samples[param].append((level, np.asarray(lab, np.float32)))

    def classify(self, param: str, lab: np.ndarray) -> PadResult:
        refs = self.samples[param]
        dists = np.array([float(delta_e(lab, r[1])) for r in refs])
        order = np.argsort(dists)
        knn = order[: self.k]

        # vote pondéré par 1/distance
        votes: dict[str, float] = {}
        for i in knn:
            votes[refs[i][0]] = votes.get(refs[i][0], 0.0) + 1.0 / (dists[i] + 1e-3)
        best = max(votes, key=votes.get)

        d1 = float(dists[order[0]])
        # meilleur concurrent = niveau différent le plus proche
        others = [dists[i] for i in order if refs[i][0] != best]
        d2 = float(others[0]) if others else d1 + 50.0
        margin = (d2 - d1) / (d2 + d1 + 1e-6)
        confidence = float(max(0.0, margin) * max(0.0, 1.0 - d1 / C.MAX_PAD_DELTA_E))

        near = [refs[i][0] for i in order[:2]]
        if d1 > C.MAX_PAD_DELTA_E or margin < C.MIN_PAD_MARGIN:
            return PadResult(param, None, "indéterminé", d1, confidence,
                             [round(float(v), 2) for v in lab], None, near)
        return PadResult(param, best, "ok", d1, confidence,
                         [round(float(v), 2) for v in lab],
                         best in C.NORMAL_LEVELS.get(param, set()), near)
