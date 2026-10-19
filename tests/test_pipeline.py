"""Tests du moteur de vision. Lancer :  pytest -q"""
import numpy as np
import pytest

from kromamed import analyze
from kromamed import config as C
from kromamed.card import find_markers
from kromamed.color import srgb_to_lab, hex_to_srgb, delta_e
from kromamed.interpreter import BiomedicalInterpreter
from kromamed.simulate import simulate_photo, random_levels


def test_les_quatre_reperes_sont_detectes():
    img = simulate_photo(seed=0)
    assert set(find_markers(img)) == {0, 1, 2, 3}


@pytest.mark.parametrize("seed", range(8))
def test_tous_les_niveaux_sont_retrouves(seed):
    levels = random_levels(np.random.default_rng(seed))
    res = analyze(simulate_photo(levels, seed=seed))
    assert res.status == "ok"
    assert {p.param: p.level for p in res.pads} == levels


def test_robuste_a_la_lumiere_coloree_et_aux_ombres():
    levels = {p: C.REFERENCE_TABLE[p][1][0] for p in C.PARAMS}
    res = analyze(simulate_photo(levels, seed=7, warm=0.45, shadow=0.12))
    assert res.status == "ok"
    assert {p.param: p.level for p in res.pads} == levels


def test_refuse_une_image_floue():
    res = analyze(simulate_photo(seed=1, blur_sigma=2.5))
    assert res.status == "rejected" and res.pads == []


def test_refuse_si_un_repere_est_cache():
    res = analyze(simulate_photo(seed=3, hide_marker=1))
    assert res.status == "rejected" and res.quality.markers < 1.0


def test_refuse_une_ombre_trop_forte():
    res = analyze(simulate_photo(seed=4, shadow=0.75))
    assert res.status == "rejected"


def test_photo_sans_carte_est_refusee():
    res = analyze(np.full((600, 800, 3), 128, np.uint8))
    assert res.status == "rejected"


def test_verdict_global():
    normal = dict(C.NORMAL_DEFAULT)
    assert analyze(simulate_photo(normal, seed=2)).all_normal is True
    anormal = dict(normal, proteines="+++")
    assert analyze(simulate_photo(anormal, seed=2)).all_normal is False


def test_dix_parametres_dans_l_ordre_de_la_notice():
    assert len(C.PARAMS) == 10
    assert C.PARAMS[0] == "leucocytes" and C.PARAMS[-1] == "glucose"
    assert set(C.READ_TIME_S) == set(C.PARAMS) == set(C.REFERENCE_TABLE)


def test_les_plages_ne_se_chevauchent_pas():
    rects = [C.pad_rect(i) for i in range(len(C.PARAMS))]
    for (x1, y1, w1, h1), (x2, y2, w2, h2) in zip(rects, rects[1:]):
        assert y1 + h1 < y2
    sx, sy, sw, sh = C.STRIP_BODY
    for x, y, w, h in rects:
        assert sx <= x and x + w <= sx + sw and sy <= y and y + h <= sy + sh


def test_couleur_inconnue_est_indeterminee():
    interp = BiomedicalInterpreter()
    r = interp.classify("proteines", np.array([50.0, 60.0, -60.0]))   # violet très saturé
    assert r.status == "indéterminé" and r.level is None


def test_niveaux_voisins_assez_distincts():
    """Garde-fou sur la table : deux niveaux d'un même paramètre doivent
    rester séparés d'au moins ΔE 10, sinon la lecture n'est pas fiable."""
    for param, levels in C.REFERENCE_TABLE.items():
        labs = [srgb_to_lab(hex_to_srgb(c)) for _, c in levels]
        for i in range(len(labs)):
            for j in range(i + 1, len(labs)):
                assert delta_e(labs[i], labs[j]) >= 10, (param, levels[i][0], levels[j][0])
